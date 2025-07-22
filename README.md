# Smart Roadster Kiosk System

車載Raspberry Pi用のKioskシステムです。Smart Roadster専用に設計されており、天気予報、GPS位置情報、ずんだもんによる音声案内機能を提供します。

## 🚗 プロジェクト概要

このプロジェクトは、Smart Roadster（雨に弱い車両）のために開発された車載情報システムです。特に雨の接近を事前に警告することで、安全なドライブをサポートします。

### 主な機能

- 🗺️ **簡易地図表示** - Chromium Kioskモードでの地図表示
- 🗣️ **ずんだもん音声案内** - VOICEVOX搭載による可愛い音声案内
- 🎭 **ずんだもん漫談システム** - Ollama + Mistralによる自動漫談生成
- 📍 **GPS位置追跡** - 現在位置の逆ジオコーディングと市区町村の出入り通知
- 🌧️ **天気予報・雨アラート** - OpenWeatherMap APIによる雨の接近警告
- 🔌 **GPIO制御** - エンジンオン/オフに連動した自動起動・シャットダウン

## 🏗️ システム構成

```
kiosk-452/
├── docker/                    # 開発用Docker環境
│   ├── Dockerfile             # Openbox + Chromium + VNC
│   ├── docker-compose.yml     # 開発環境構築
│   ├── start.sh               # コンテナ起動スクリプト
│   └── supervisord.conf       # プロセス管理設定
├── scripts/                   # 本番用セットアップスクリプト
│   └── install.sh             # Raspberry Pi初期セットアップ
├── kiosk/                     # Kioskアプリケーション
│   ├── index.html             # メインUI
│   └── app.js                 # フロントエンドロジック
├── voice/                     # VOICEVOX・ずんだもん関係
│   ├── zundamon.json          # 音声設定・台本
│   └── speak.py               # 音声出力制御
├── sensors/                   # センサー・外部API連携
│   ├── gps_reader.py          # GPS読み取り
│   ├── gpio_shutdown.py       # GPIO監視・シャットダウン
│   └── weather_checker.py     # 天気予報取得
├── assets/                    # 画像・音声素材
├── config/                    # 設定ファイル
│   └── settings.yaml          # システム設定
├── README.md
└── requirements.txt           # Python依存関係
```

## 🎭 ずんだもん漫談システム

### 概要
Ollama + Mistralモデルを使用して、ずんだもんが自動で漫談を生成します。トピックを指定すると、ずんだもんらしい口調で楽しい小話を作成し、適切な表情・ポーズと共に音声で再生します。

### 機能詳細
- **自動テキスト生成**: Mistralモデルによるずんだもん風漫談の生成
- **表情・ポーズ制御**: 漫談内容に応じた適切なずんだもん画像の自動選択
- **音声合成**: VOICEVOX連携による自然な音声再生
- **YAML構造化出力**: LLMからの確実なパラメータ抽出

### 使用技術
- **Ollama**: ローカルLLM実行環境
- **Mistral**: 軽量で高性能な言語モデル
- **YAML**: 構造化されたレスポンス形式
- **WebSocket**: リアルタイム通信
- **並行処理**: 画像生成と音声合成の同時実行

## 🐳 開発環境セットアップ

### 前提条件

- Docker & Docker Compose
- VNCクライアント（Mac標準のScreen Sharing、VNC Viewer等）

### 起動手順

1. **リポジトリのクローン**
   ```bash
   git clone <repository-url>
   cd kiosk-452
   ```

2. **Ollamaセットアップ（初回のみ）**
   ```bash
   ./scripts/setup-ollama.sh
   ```

3. **全サービスの起動**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **アクセス確認**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000
   - Ollama API: http://localhost:11434

5. **漫談機能のテスト**
   - UIの「ずんだもん漫談生成」ボタンをクリック
   - 自動でトピックが選択され、漫談が生成されます

6. **環境の停止**
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

## 🔧 技術スタック

### 開発環境
- **Docker**: コンテナ化による環境統一
- **Debian Bullseye**: ベースOS
- **Openbox**: 軽量ウィンドウマネージャー
- **Chromium**: Kioskモード表示
- **VNC**: リモート開発環境

### 本番環境（予定）
- **Raspberry Pi OS**: Bullseye以降
- **Python 3.9+**: バックエンド処理
- **VOICEVOX**: 音声合成エンジン
- **OpenWeatherMap API**: 天気予報データ
- **GPIO**: ハードウェア制御

## 🎯 開発ロードマップ

### Phase 1: 基盤構築 ✅
- [x] Docker開発環境構築
- [x] プロジェクト構造設計
- [x] VNC接続確認

### Phase 2: コア機能実装
- [ ] GPS モジュール連携
- [ ] OpenWeatherMap API連携
- [ ] VOICEVOX セットアップ
- [ ] 基本UI実装

### Phase 3: 統合・最適化
- [ ] 各機能の統合
- [ ] Raspberry Pi最適化
- [ ] GPIO制御実装
- [ ] 自動起動設定

### Phase 4: 本番デプロイ
- [ ] Raspberry Pi環境構築
- [ ] 車両への組み込み
- [ ] 実地テスト
- [ ] 最終調整

## 🚨 重要な注意事項

### Smart Roadster について
- **雨に弱い車両**のため、天気予報機能は最重要
- 雨の接近は早めの警告が必要
- 屋根の開閉に時間がかかるため、余裕を持った通知

### 開発時の注意
- 現在のファイルは**ダミー実装**です
- 実際の開発時は各ファイルを適切に実装してください
- APIキーは設定ファイルで管理し、リポジトリにコミットしないでください

## 📝 設定

### API設定
`config/settings.yaml` で以下を設定：
- OpenWeatherMap APIキー
- GPS設定
- 音声設定
- GPIO ピン設定

### 開発設定
- VNCパスワード: `raspberry`
- VNCポート: `5900`
- 画面解像度: `1280x800`

## 🤝 コントリビューション

1. 機能追加・バグ修正は適切なブランチで作業
2. コミット前にlintとテストを実行
3. プルリクエストで変更内容を説明

## 📄 ライセンス

このプロジェクトは個人利用目的です。

### 使用素材・ライブラリ
- **ずんだもん**: VOICEVOX利用規約に準拠
- **OpenWeatherMap**: API利用規約に準拠
- **その他ライブラリ**: 各ライブラリのライセンスに準拠

---

**Smart Roadster Kiosk System** - 雨に負けないドライブのために 🌧️🚗
