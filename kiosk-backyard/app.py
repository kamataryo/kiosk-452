#!/usr/bin/env python3
"""
Smart Roadster Kiosk API Server
Flask-based JSON API server for the kiosk system
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os
import json
from datetime import datetime
import random
import requests
import threading
import queue
import uuid
import base64
import io
from zundamon_compositor import ZundamonCompositor

# 既存モジュールのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)  # フロントエンドからのアクセスを許可
socketio = SocketIO(app, cors_allowed_origins="*")

# グローバル変数（簡易的な状態管理）
voice_status = {
    'isPlaying': False,
    'lastMessage': 'システム起動完了'
}

# 音声合成キュー
voice_queue = queue.Queue()

# ずんだもん画像合成器を初期化
zundamon_compositor = None

class VoicevoxClient:
    """VOICEVOX ENGINEクライアント"""

    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('VOICEVOX_URL', 'http://voicevox-engine:50021')

    def is_available(self):
        """VOICEVOX ENGINEが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_speakers(self):
        """利用可能な話者一覧を取得"""
        try:
            response = requests.get(f"{self.base_url}/speakers", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"話者一覧取得エラー: {e}")
            return []

    def synthesize(self, text, speaker_id=3):
        """音声合成を実行"""
        try:
            # 1. 音声クエリを生成
            query_response = requests.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10
            )
            query_response.raise_for_status()

            # 2. 音声合成を実行
            synthesis_response = requests.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query_response.json(),
                timeout=30
            )
            synthesis_response.raise_for_status()

            return synthesis_response.content

        except Exception as e:
            print(f"音声合成エラー: {e}")
            raise

# VOICEVOX クライアントを初期化
voicevox_client = VoicevoxClient()

def process_voice_queue():
    """音声合成キューを処理"""
    while not voice_queue.empty():
        task = voice_queue.get()

        # 処理開始通知
        socketio.emit('voice_processing', {
            'task_id': task['task_id'],
            'text': task['text']
        }, room=task['client_id'])

        try:
            # VOICEVOX で音声合成
            if voicevox_client.is_available():
                audio_data = voicevox_client.synthesize(
                    task['text'],
                    task['speaker_id']
                )

                # 音声データをBase64エンコードして送信
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')

                socketio.emit('voice_ready', {
                    'task_id': task['task_id'],
                    'audio_data': audio_b64,
                    'format': 'wav',
                    'text': task['text']
                }, room=task['client_id'])

                # ステータス更新
                global voice_status
                voice_status['lastMessage'] = task['text']
                voice_status['isPlaying'] = False

            else:
                # VOICEVOX が利用できない場合のフォールバック
                socketio.emit('voice_fallback', {
                    'task_id': task['task_id'],
                    'text': task['text'],
                    'message': 'VOICEVOX ENGINEが利用できません。ブラウザTTSを使用してください。'
                }, room=task['client_id'])

        except Exception as e:
            print(f"音声合成エラー: {e}")
            socketio.emit('voice_error', {
                'task_id': task['task_id'],
                'error': str(e),
                'text': task['text']
            }, room=task['client_id'])

# WebSocket イベントハンドラー
@socketio.on('connect')
def handle_connect():
    """クライアント接続時の処理"""
    print(f'WebSocketクライアント接続: {request.sid}')

    # 接続状態とシステム状態を送信
    emit('status', {
        'connected': True,
        'voice_status': voice_status,
        'voicevox_available': voicevox_client.is_available(),
        'queue_size': voice_queue.qsize()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """クライアント切断時の処理"""
    print(f'WebSocketクライアント切断: {request.sid}')

@socketio.on('voice_synthesize')
def handle_voice_synthesize(data):
    """音声合成リクエストの処理"""
    try:
        text = data.get('text', '')
        speaker_id = data.get('speaker', 3)  # デフォルトはずんだもん
        priority = data.get('priority', 'normal')

        if not text:
            emit('voice_error', {
                'error': 'テキストが指定されていません'
            })
            return

        # タスクIDを生成
        task_id = str(uuid.uuid4())

        # キューに追加
        voice_queue.put({
            'task_id': task_id,
            'text': text,
            'speaker_id': speaker_id,
            'priority': priority,
            'client_id': request.sid,
            'timestamp': datetime.now().isoformat()
        })

        # キュー追加通知
        emit('voice_queued', {
            'task_id': task_id,
            'queue_position': voice_queue.qsize(),
            'text': text
        })

        # ステータス更新
        global voice_status
        voice_status['isPlaying'] = True

        # 音声合成処理を開始（別スレッド）
        threading.Thread(target=process_voice_queue, daemon=True).start()

    except Exception as e:
        print(f"音声合成リクエストエラー: {e}")
        emit('voice_error', {
            'error': str(e)
        })

@socketio.on('get_speakers')
def handle_get_speakers():
    """話者一覧取得"""
    try:
        if voicevox_client.is_available():
            speakers = voicevox_client.get_speakers()
            emit('speakers_list', {
                'speakers': speakers,
                'available': True
            })
        else:
            emit('speakers_list', {
                'speakers': [],
                'available': False,
                'message': 'VOICEVOX ENGINEが利用できません'
            })
    except Exception as e:
        emit('speakers_list', {
            'speakers': [],
            'available': False,
            'error': str(e)
        })

@socketio.on('get_voice_status')
def handle_get_voice_status():
    """音声システム状態取得"""
    emit('voice_status_update', {
        'voice_status': voice_status,
        'voicevox_available': voicevox_client.is_available(),
        'queue_size': voice_queue.qsize()
    })

def init_zundamon():
    """ずんだもん合成器を初期化"""
    global zundamon_compositor
    try:
        zundamon_compositor = ZundamonCompositor()
        print("✅ ずんだもん画像合成器を初期化しました")
    except Exception as e:
        print(f"❌ ずんだもん画像合成器の初期化に失敗: {e}")
        zundamon_compositor = None

@app.route('/')
def index():
    """API サーバーのルート"""
    return jsonify({
        'message': 'Smart Roadster Kiosk API Server',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/gps')
def get_gps():
    """GPS位置情報を取得"""
    try:
        # 既存のGPSモジュールを使用する予定だが、現在はサンプルデータ
        # from sensors.gps_reader import get_current_position
        # position = get_current_position()

        # サンプルデータ（東京駅周辺）
        sample_positions = [
            {
                'latitude': 35.681236,
                'longitude': 139.767125,
                'address': '東京都千代田区丸の内1丁目'
            },
            {
                'latitude': 35.658034,
                'longitude': 139.701636,
                'address': '東京都渋谷区渋谷2丁目'
            },
            {
                'latitude': 35.689487,
                'longitude': 139.691706,
                'address': '東京都新宿区新宿3丁目'
            }
        ]

        position = random.choice(sample_positions)

        return jsonify({
            'success': True,
            'data': position,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/weather')
def get_weather():
    """天気予報情報を取得"""
    try:
        # 既存の天気モジュールを使用する予定だが、現在はサンプルデータ
        # from sensors.weather_checker import get_weather_forecast
        # forecast = get_weather_forecast()

        # サンプルデータ
        weather_conditions = ['晴れ', '曇り', '小雨', '雨', '雪']
        condition = random.choice(weather_conditions)

        # Smart Roadster用の雨アラート
        rain_alert = condition in ['小雨', '雨']

        weather_data = {
            'temperature': random.randint(15, 30),
            'condition': condition,
            'humidity': random.randint(40, 80),
            'rainAlert': rain_alert
        }

        return jsonify({
            'success': True,
            'data': weather_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/voice/status')
def get_voice_status():
    """音声システムのステータスを取得"""
    try:
        return jsonify({
            'success': True,
            'data': voice_status,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/voice/speak', methods=['POST'])
def speak_text():
    """テキストを音声で再生"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({
                'success': False,
                'error': 'テキストが指定されていません',
                'timestamp': datetime.now().isoformat()
            }), 400

        # 既存の音声モジュールを使用する予定だが、現在はログ出力のみ
        # from voice.speak import speak_text
        # speak_text(text)

        print(f"[音声出力] {text}")

        # ステータスを更新
        global voice_status
        voice_status['isPlaying'] = True
        voice_status['lastMessage'] = text

        # 簡易的に2秒後に再生完了とする
        import threading
        def reset_status():
            import time
            time.sleep(2)
            voice_status['isPlaying'] = False

        threading.Thread(target=reset_status).start()

        return jsonify({
            'success': True,
            'message': '音声再生を開始しました',
            'text': text,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/zundamon/options')
def get_zundamon_options():
    """ずんだもんの利用可能なオプションを取得"""
    try:
        if not zundamon_compositor:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像合成器が初期化されていません',
                'timestamp': datetime.now().isoformat()
            }), 503

        options = zundamon_compositor.get_available_options()

        return jsonify({
            'success': True,
            'data': options,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/zundamon/generate', methods=['POST'])
def generate_zundamon():
    """ずんだもん画像を生成"""
    try:
        if not zundamon_compositor:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像合成器が初期化されていません',
                'timestamp': datetime.now().isoformat()
            }), 503

        # パラメータを取得
        data = request.get_json() if request.is_json else {}
        params = data.get('params', {})
        format_type = data.get('format', 'PNG')

        # 画像を合成
        img_buffer = zundamon_compositor.compose_image(params, format_type)

        # Content-Typeを設定
        mimetype = 'image/png' if format_type.upper() == 'PNG' else 'image/jpeg'

        return send_file(
            img_buffer,
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'zundamon.{format_type.lower()}'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/zundamon/generate')
def generate_zundamon_get():
    """ずんだもん画像を生成（GETリクエスト対応）"""
    try:
        if not zundamon_compositor:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像合成器が初期化されていません',
                'timestamp': datetime.now().isoformat()
            }), 503

        # URLパラメータから設定を取得
        params = {}
        for key in ['head_direction', 'right_arm', 'left_arm', 'edamame',
                   'face_color', 'expression_mouth', 'expression_eyes', 'expression_eyebrows']:
            value = request.args.get(key)
            if value:
                params[key] = value

        format_type = request.args.get('format', 'PNG')

        # 画像を合成
        img_buffer = zundamon_compositor.compose_image(params, format_type)

        # Content-Typeを設定
        mimetype = 'image/png' if format_type.upper() == 'PNG' else 'image/jpeg'

        return send_file(
            img_buffer,
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'zundamon.{format_type.lower()}'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/system/info')
def get_system_info():
    """システム情報を取得"""
    try:
        import platform
        import psutil

        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }

        return jsonify({
            'success': True,
            'data': system_info,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': True,  # システム情報取得失敗でもエラーにしない
            'data': {
                'platform': 'Unknown',
                'message': 'システム情報の取得に失敗しました'
            },
            'timestamp': datetime.now().isoformat()
        })

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラー"""
    return jsonify({
        'success': False,
        'error': 'エンドポイントが見つかりません',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    return jsonify({
        'success': False,
        'error': 'サーバー内部エラーが発生しました',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("🚗 Smart Roadster Kiosk API Server")
    print("=" * 40)
    print("サーバーを起動中...")
    print("URL: http://localhost:8000")
    print("WebSocket: ws://localhost:8000")
    print("=" * 40)

    # ずんだもん合成器を初期化
    init_zundamon()

    # VOICEVOX接続確認
    if voicevox_client.is_available():
        print("✅ VOICEVOX ENGINE接続確認済み")
    else:
        print("⚠️  VOICEVOX ENGINEに接続できません（フォールバック機能で動作）")

    # SocketIOサーバーを起動
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
