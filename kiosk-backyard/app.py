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
import yaml
import re
from concurrent.futures import ThreadPoolExecutor
import ollama
import anthropic
from zundamon_compositor import ZundamonCompositor
import hashlib
from pathlib import Path

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
        # キャッシュ設定
        self.cache_dir = Path("/app/cache/voice/")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = 512 * 1024 * 1024  # 512MB

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

    def _generate_cache_key(self, text, speaker_id):
        """キャッシュキーを生成"""
        key_string = f"{text}_{speaker_id}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def _get_cache_size(self):
        """現在のキャッシュサイズを取得"""
        total_size = 0
        try:
            for cache_file in self.cache_dir.glob("*.wav"):
                total_size += cache_file.stat().st_size
        except Exception as e:
            print(f"キャッシュサイズ取得エラー: {e}")
        return total_size

    def _cleanup_cache(self):
        """キャッシュサイズが上限を超えた場合、古いファイルを削除"""
        try:
            current_size = self._get_cache_size()
            if current_size <= self.max_cache_size:
                return

            # ファイルを最終アクセス時刻でソート（古い順）
            cache_files = []
            for cache_file in self.cache_dir.glob("*.wav"):
                try:
                    stat = cache_file.stat()
                    cache_files.append((cache_file, stat.st_atime, stat.st_size))
                except Exception:
                    continue

            cache_files.sort(key=lambda x: x[1])  # アクセス時刻でソート

            # 上限以下になるまで古いファイルを削除
            for cache_file, _, file_size in cache_files:
                if current_size <= self.max_cache_size:
                    break
                try:
                    cache_file.unlink()
                    current_size -= file_size
                    print(f"キャッシュファイル削除: {cache_file.name}")
                except Exception as e:
                    print(f"キャッシュファイル削除エラー: {e}")

        except Exception as e:
            print(f"キャッシュクリーンアップエラー: {e}")

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

    def synthesize_with_cache(self, text, speaker_id=3, cache_mode='use'):
        """キャッシュ機能付き音声合成"""
        try:
            cache_key = self._generate_cache_key(text, speaker_id)
            cache_file = self.cache_dir / f"{cache_key}.wav"

            # bypassモード: キャッシュを使わず、保存もしない
            if cache_mode == 'bypass':
                print(f"[キャッシュ] bypass モード: {text[:30]}...")
                return self.synthesize(text, speaker_id)

            # invalidateモード: キャッシュファイルを削除
            if cache_mode == 'invalidate':
                if cache_file.exists():
                    cache_file.unlink()
                    print(f"[キャッシュ] invalidate: {cache_file.name}")

            # useモード: キャッシュがあれば使用
            if cache_mode in ['use', 'invalidate'] and cache_file.exists():
                print(f"[キャッシュ] ヒット: {cache_file.name}")
                # ファイルのアクセス時刻を更新（LRU用）
                cache_file.touch()
                return cache_file.read_bytes()

            # キャッシュがない場合は音声合成を実行
            print(f"[キャッシュ] ミス: {text[:30]}...")
            audio_data = self.synthesize(text, speaker_id)

            # bypassモード以外はキャッシュに保存
            if cache_mode != 'bypass':
                try:
                    # キャッシュサイズをチェックしてクリーンアップ
                    self._cleanup_cache()

                    # キャッシュファイルに保存
                    cache_file.write_bytes(audio_data)
                    print(f"[キャッシュ] 保存: {cache_file.name}")
                except Exception as e:
                    print(f"[キャッシュ] 保存エラー: {e}")

            return audio_data

        except Exception as e:
            print(f"キャッシュ付き音声合成エラー: {e}")
            raise

# VOICEVOX クライアントを初期化
voicevox_client = VoicevoxClient()

class OllamaClient:
    """Ollama LLMクライアント"""

    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('OLLAMA_URL', 'http://ollama:11434')
        self.client = ollama.Client(host=self.base_url)

    def is_available(self):
        """Ollamaが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self):
        """利用可能なモデル一覧を取得"""
        try:
            return self.client.list()
        except Exception as e:
            print(f"モデル一覧取得エラー: {e}")
            return {'models': []}

    def pull_model(self, model_name):
        """モデルをダウンロード"""
        try:
            return self.client.pull(model_name)
        except Exception as e:
            print(f"モデルダウンロードエラー: {e}")
            raise

    def generate(self, model, prompt, **kwargs):
        """テキスト生成"""
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                **kwargs
            )
            return response['response']
        except Exception as e:
            print(f"テキスト生成エラー: {e}")
            raise

# Ollama クライアントを初期化
ollama_client = OllamaClient()

class ClaudeClient:
    """Claude API クライアント"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"Claude APIクライアント初期化エラー: {e}")
                self.client = None

    def is_available(self):
        """Claude APIが利用可能かチェック"""
        if not self.api_key or not self.client:
            return False
        try:
            # 簡単なテストリクエストでAPIキーの有効性を確認
            # 実際のリクエストは避けて、クライアントの初期化状態のみチェック
            return True
        except Exception:
            return False

    def generate(self, prompt, max_tokens=1000):
        """テキスト生成"""
        try:
            if not self.client:
                raise Exception("Claude APIクライアントが初期化されていません")

            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text
        except Exception as e:
            print(f"Claude API テキスト生成エラー: {e}")
            raise

# Claude クライアントを初期化
claude_client = ClaudeClient()

# 漫談生成用のプロンプトテンプレート
MANDAN_PROMPT = """あなたはずんだもんです。与えられたトピックについて、ずんだもんらしい短い漫談を作ってください。

トピック: {topic}
最大文字数: {maxlength}

以下の YAML 形式で厳密に出力してください：

--- ← YAMLドキュメントの開始を示す
sentence: "ここに漫談の内容"
zundamonImage:
  edamame: ['通常', '立ち', '萎え', '立ち片折れ'] のいずれかを1つ選んで記述
  expression_eyebrows: ['基本眉', '怒り眉', '困り眉', '上がり眉', '怒り眉2'] のいずれかを1つ選んで記述
  expression_eyes: ['基本目', 'にっこり', '^^', 'なごみ目', '閉じ目', 'ジト目', '〇〇'] のいずれかを1つ選んで記述
  expression_mouth: ['ほう', 'あは', 'ほほえみ', 'えへ', 'にやり', 'むふ', 'お', 'ん'] のいずれかを1つ選んで記述
  face_color: ['ほっぺ基本', 'ほっぺ赤め', '赤面', '青ざめ', '非表示'] のいずれかを1つ選んで記述
  left_arm: ['腰', '横', '手を挙げる', '基本', 'あごに指', '口元'] のいずれかを1つ選んで記述
  right_arm: ['腰', '指差し横', '手を挙げる', '基本', '横', '指差し上'] のいずれかを1つ選んで記述
--- ← YAMLドキュメントの終了を示す

注意：
- 漫談は{maxlength}文字以内
- ずんだもんの口調（のだ）を使用
- zundamonImageのすべての項目は必須
- 値は必ず指定された候補から1つを厳密に選ぶこと
- YAML形式を厳密に守ること
- YAML の前後に開始と終了を示す --- をつけること
- YAML 以外の内容は絶対に出力しないこと
- 楽しく親しみやすい内容にする"""

# デフォルトのずんだもんパラメータ
DEFAULT_ZUNDAMON_PARAMS = {
    'head_direction': '正面向き',
    'right_arm': '腰',
    'left_arm': '腰',
    'expression_mouth': 'ほう',
    'expression_eyes': '基本目',
    'expression_eyebrows': '怒り眉'
}

def extract_yaml_from_response(response_text: str) -> str:
    """レスポンスからYAML部分を抽出"""
    pattern = r'---\s*\n(.*?)\n---'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        raise ValueError("YAML形式が見つかりません")

def generate_zundamon_image_url(params: dict) -> str:
    """ずんだもん画像のURLを生成"""
    if not zundamon_compositor:
        return '/api/zundamon/generate'

    try:
        # 画像を生成してBase64データURLとして返す
        img_buffer = zundamon_compositor.compose_image(params, 'PNG')
        img_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_b64}"
    except Exception as e:
        print(f"ずんだもん画像生成エラー: {e}")
        return '/api/zundamon/generate'

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
            # VOICEVOX で音声合成（キャッシュ機能付き）
            if voicevox_client.is_available():
                cache_mode = task.get('cache_mode', 'use')
                audio_data = voicevox_client.synthesize_with_cache(
                    task['text'],
                    task['speaker_id'],
                    cache_mode
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
        cache_mode = data.get('cache', 'use')  # キャッシュ制御パラメータ

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
            'cache_mode': cache_mode,
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

@socketio.on('generate_mandan')
def handle_generate_mandan(data):
    """漫談生成リクエストの処理"""
    try:
        topic = data.get('topic', '日常の話')
        maxlength = data.get('maxlength', 1000)
        speaker_id = data.get('speaker', 3)  # デフォルトはずんだもん
        model = data.get('model', 'mistral')
        provider = data.get('provider', 'ollama')  # 'ollama' または 'claude'

        print(f"漫談生成開始: プロバイダー={provider}, トピック={topic}, 最大文字数={maxlength}")

        # 処理開始通知
        emit('mandan_processing', {
            'topic': topic,
            'maxlength': maxlength,
            'provider': provider
        })

        def generate_text():
            """テキスト生成"""
            try:
                prompt = MANDAN_PROMPT.format(topic=topic, maxlength=maxlength)

                if provider == 'claude':
                    if not claude_client.is_available():
                        raise Exception("Claude APIが利用できません")

                    response = claude_client.generate(prompt, max_tokens=1500)

                    # デバッグ出力を追加
                    print(f"=== Claudeレスポンス ===")
                    print(f"レスポンス長: {len(response)}")
                    print(f"レスポンス内容: {response}")
                    print(f"=== レスポンス終了 ===")

                    return response
                else:  # ollama
                    if not ollama_client.is_available():
                        raise Exception("Ollamaサーバーに接続できません")

                    response = ollama_client.generate(model, prompt)

                    # デバッグ出力を追加
                    print(f"=== Ollamaレスポンス ===")
                    print(f"レスポンス長: {len(response)}")
                    print(f"レスポンス内容: {response}")
                    print(f"=== レスポンス終了 ===")

                    return response
            except Exception as e:
                print(f"テキスト生成エラー ({provider}): {e}")
                raise

        def generate_image_and_voice(sentence, zundamon_params):
            """画像と音声を並行生成"""
            def generate_image():
                try:
                    return generate_zundamon_image_url(zundamon_params), zundamon_params
                except Exception as e:
                    print(f"画像生成エラー: {e}")
                    return '/api/zundamon/generate', DEFAULT_ZUNDAMON_PARAMS

            def generate_voice():
                try:
                    if voicevox_client.is_available():
                        # 生成AIテキストはbypassモードで音声合成（キャッシュしない）
                        return voicevox_client.synthesize_with_cache(sentence, speaker_id, 'bypass')
                    return None
                except Exception as e:
                    print(f"音声生成エラー: {e}")
                    return None

            with ThreadPoolExecutor(max_workers=2) as executor:
                image_future = executor.submit(generate_image)
                voice_future = executor.submit(generate_voice)

                image_url, final_params = image_future.result()
                audio_data = voice_future.result()

                return image_url, final_params, audio_data

        # 1. テキスト生成
        try:
            response_text = generate_text()
            yaml_content = extract_yaml_from_response(response_text)
            parsed_data = yaml.safe_load(yaml_content)

            sentence = parsed_data.get('sentence', '')
            zundamon_params = parsed_data.get('zundamonImage', DEFAULT_ZUNDAMON_PARAMS)

            if not sentence:
                raise ValueError("漫談テキストが生成されませんでした")

        except Exception as e:
            print(f"YAML解析エラー: {e}")
            print(f"生のレスポンス（最初の500文字）: {response_text[:500]}...")
            print(f"生のレスポンス（最後の500文字）: ...{response_text[-500:]}")

            # YAML抽出の詳細デバッグ
            try:
                yaml_content = extract_yaml_from_response(response_text)
                print(f"抽出されたYAML: {yaml_content}")
            except Exception as yaml_error:
                print(f"YAML抽出失敗: {yaml_error}")

            # フォールバック: シンプルな漫談を生成
            sentence = f"{topic}について話すのだ！面白い話があるのだ〜"
            zundamon_params = DEFAULT_ZUNDAMON_PARAMS

        # 2. 画像と音声を並行生成
        try:
            image_url, final_params, audio_data = generate_image_and_voice(sentence, zundamon_params)
        except Exception as e:
            print(f"画像・音声生成エラー: {e}")
            image_url = '/api/zundamon/generate'
            final_params = DEFAULT_ZUNDAMON_PARAMS
            audio_data = None

        # 3. レスポンス構築
        response_data = {
            'sentence': sentence,
            'zundamonImageUrl': image_url,
            'zundamonParams': final_params,
            'topic': topic,
            'generatedAt': datetime.now().isoformat()
        }

        # 音声データがある場合は追加
        if audio_data:
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            response_data['audio'] = {
                'audioData': audio_b64,
                'format': 'wav',
                'speaker': speaker_id
            }

        # 完了通知
        emit('mandan_ready', response_data)
        print(f"漫談生成完了: {sentence[:50]}...")

    except Exception as e:
        print(f"漫談生成エラー: {e}")
        emit('mandan_error', {
            'error': str(e),
            'topic': data.get('topic', ''),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_ollama_status')
def handle_get_ollama_status():
    """Ollamaシステム状態取得"""
    try:
        available = ollama_client.is_available()
        models = ollama_client.list_models() if available else {'models': []}

        emit('ollama_status', {
            'available': available,
            'models': [model['name'] for model in models.get('models', [])],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('ollama_status', {
            'available': False,
            'models': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_claude_status')
def handle_get_claude_status():
    """Claude APIシステム状態取得"""
    try:
        available = claude_client.is_available()
        api_key_configured = bool(claude_client.api_key)

        emit('claude_status', {
            'available': available,
            'api_key_configured': api_key_configured,
            'model': 'claude-3-haiku-20240307',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('claude_status', {
            'available': False,
            'api_key_configured': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
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

    # Ollama接続確認
    if ollama_client.is_available():
        print("✅ Ollama接続確認済み")
        try:
            models = ollama_client.list_models()
            model_names = [model['name'] for model in models.get('models', [])]
            if model_names:
                print(f"   利用可能なモデル: {', '.join(model_names)}")
            else:
                print("   モデルが見つかりません。mistralモデルをダウンロードしてください。")
        except Exception as e:
            print(f"   モデル一覧取得エラー: {e}")
    else:
        print("⚠️  Ollamaに接続できません（漫談機能は利用できません）")

    # Claude API接続確認
    if claude_client.is_available():
        print("✅ Claude API接続確認済み")
        print(f"   利用モデル: claude-3-haiku-20240307")
    else:
        if not claude_client.api_key:
            print("⚠️  Claude APIキーが設定されていません（.envrcファイルでCLAUDE_API_KEYを設定してください）")
        else:
            print("⚠️  Claude APIに接続できません（APIキーを確認してください）")

    # SocketIOサーバーを起動
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
