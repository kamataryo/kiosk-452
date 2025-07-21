# Assets ディレクトリ - ダミーファイル

このディレクトリはダミーです。実際の開発時に以下のファイルを配置してください。

## 予定しているアセット

### ずんだもんアニメーション素材
- `zundamon_idle.gif` - 待機状態のアニメーション
- `zundamon_speaking.gif` - 話している時のアニメーション  
- `zundamon_happy.gif` - 嬉しい時のアニメーション
- `zundamon_warning.gif` - 警告時のアニメーション

### 地図関連素材
- `map_icons/` - 地図上で使用するアイコン類
  - `current_location.png` - 現在位置マーカー
  - `destination.png` - 目的地マーカー
  - `gas_station.png` - ガソリンスタンドアイコン
  - `parking.png` - 駐車場アイコン

### UI素材
- `ui_icons/` - ユーザーインターフェース用アイコン
  - `weather_sunny.png` - 晴れアイコン
  - `weather_cloudy.png` - 曇りアイコン
  - `weather_rainy.png` - 雨アイコン
  - `gps_signal.png` - GPS信号アイコン
  - `volume_on.png` - 音量オンアイコン
  - `volume_off.png` - 音量オフアイコン

### 背景画像
- `backgrounds/` - 背景画像
  - `smart_roadster_bg.jpg` - Smart Roadster の背景画像
  - `dashboard_bg.png` - ダッシュボード背景
  - `night_mode_bg.jpg` - ナイトモード用背景

### 音声ファイル
- `sounds/` - 効果音・通知音
  - `startup.wav` - 起動音
  - `shutdown.wav` - シャットダウン音
  - `alert.wav` - アラート音
  - `notification.wav` - 通知音

## ファイル形式について

### 画像ファイル
- **PNG**: 透明度が必要なアイコン類
- **JPG**: 写真・背景画像
- **GIF**: アニメーション（ずんだもん）
- **SVG**: ベクター画像（スケーラブルなアイコン）

### 音声ファイル
- **WAV**: 高品質な効果音
- **MP3**: 圧縮が必要な長い音声ファイル

## 推奨サイズ

### アイコン
- 小: 24x24px
- 中: 48x48px  
- 大: 96x96px

### アニメーション
- ずんだもん: 200x200px 程度
- フレームレート: 15-30fps

### 背景画像
- メイン画面: 1280x800px（画面解像度に合わせる）
- ダッシュボード: 適宜調整

## 著作権について

- ずんだもん関連素材: 利用規約に従って使用
- その他のアイコン: フリー素材またはオリジナル作成
- 音声ファイル: VOICEVOX利用規約に準拠

## 実装時の注意点

1. ファイルサイズの最適化
2. Raspberry Pi での表示性能を考慮
3. 夜間モード対応
4. 高DPI対応（必要に応じて）
