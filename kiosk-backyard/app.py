#!/usr/bin/env python3
"""
Smart Roadster Kiosk API Server
Flask-based JSON API server for the kiosk system
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sys
import os
import json
from datetime import datetime
import random
from zundamon_generator import ZundamonGenerator

# 既存モジュールのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)  # フロントエンドからのアクセスを許可

# グローバル変数（簡易的な状態管理）
voice_status = {
    'isPlaying': False,
    'lastMessage': 'システム起動完了'
}

# ずんだもん画像生成器を初期化
zundamon_generator = None

def init_zundamon():
    """ずんだもん生成器を初期化"""
    global zundamon_generator
    try:
        zundamon_generator = ZundamonGenerator()
        print("✅ ずんだもん画像生成器を初期化しました")
    except Exception as e:
        print(f"❌ ずんだもん画像生成器の初期化に失敗: {e}")
        zundamon_generator = None

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
        if not zundamon_generator:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像生成器が初期化されていません',
                'timestamp': datetime.now().isoformat()
            }), 503

        options = zundamon_generator.get_available_options()

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
        if not zundamon_generator:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像生成器が初期化されていません',
                'timestamp': datetime.now().isoformat()
            }), 503

        # パラメータを取得
        data = request.get_json() if request.is_json else {}
        params = data.get('params', {})
        format_type = data.get('format', 'PNG')

        # 画像を生成
        img_buffer = zundamon_generator.generate_image(params, format_type)

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
        if not zundamon_generator:
            return jsonify({
                'success': False,
                'error': 'ずんだもん画像生成器が初期化されていません',
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

        # 画像を生成
        img_buffer = zundamon_generator.generate_image(params, format_type)

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
    print("=" * 40)

    # ずんだもん生成器を初期化
    init_zundamon()

    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        threaded=True
    )
