# Zundamon Layer Factory

PSDファイルから個別レイヤーを抽出し、静的画像として保存する開発・メンテナンス用ツール群です。

## 概要

このツールは、ずんだもんPSDファイル（`zunda.3.2.psd`）から全レイヤーを個別のPNG画像として抽出し、本番システムで使用する静的レイヤー画像を生成します。

## 特徴

- **レイヤー単位抽出**: PSDの全レイヤーを個別PNG画像として抽出
- **メタデータ生成**: 合成に必要な位置情報・グループ情報を自動生成
- **Dry-runモード**: 実際の抽出前に容量・時間を予測
- **プログレスバー**: 抽出進捗をリアルタイム表示
- **エラーハンドリング**: 失敗したレイヤーの詳細レポート

## インストール

```bash
cd kiosk-factory
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```bash
# Dry-run（予測のみ）
python extract_layers.py --dry-run

# 実際の抽出実行
python extract_layers.py

# 確認なしで実行
python extract_layers.py --force
```

### オプション

```bash
python extract_layers.py [OPTIONS]

Options:
  -p, --psd-path TEXT     PSDファイルのパス [default: ../assets/zunda.3.2.psd]
  -o, --output-dir TEXT   出力ディレクトリ [default: ../assets/zundamon_layers]
  -d, --dry-run          実際の抽出を行わず、予測のみ実行
  -f, --force            確認なしで実行
  -v, --verbose          詳細ログを表示
  --help                 ヘルプを表示
```

### 使用例

```bash
# カスタムパスでDry-run
python extract_layers.py -p /path/to/custom.psd -o /path/to/output --dry-run

# 詳細ログ付きで実行
python extract_layers.py --verbose --force

# 別のPSDファイルを処理
python extract_layers.py -p ../assets/other.psd -o ../assets/other_layers
```

## 出力構造

抽出されたレイヤーは以下の構造で保存されます：

```
assets/zundamon_layers/
├── layer_metadata.json          # レイヤー情報・合成メタデータ
├── base/                        # 基本レイヤー（強制表示）
│   ├── tail.png                 # 尻尾のような何か
│   └── body.png                 # 体
├── head_direction/              # 頭の向き
│   ├── up.png                   # 上向き
│   └── front.png                # 正面向き
├── right_arm/                   # 右腕
│   ├── hidden.png               # 非表示
│   ├── waist.png                # 腰
│   └── ...
├── left_arm/                    # 左腕
├── edamame/                     # 枝豆
├── face_color/                  # 顔色
├── mouth/                       # 口
├── eyes/                        # 目
└── eyebrows/                    # 眉
```

## メタデータ形式

`layer_metadata.json`には以下の情報が含まれます：

```json
{
  "version": "2.0",
  "psd_info": {
    "width": 1082,
    "height": 1594,
    "color_mode": "3",
    "source_file": "zunda.3.2.psd"
  },
  "layers": {
    "layer_name": {
      "original_name": "*レイヤー名",
      "file": "group/layer_name.png",
      "bbox": {
        "left": 100, "top": 200,
        "right": 300, "bottom": 400,
        "width": 200, "height": 200
      },
      "z_index": 10,
      "visible": true,
      "opacity": 255,
      "blend_mode": "BlendMode.NORMAL",
      "required": false,
      "parent_group": "group_name",
      "radio_group": "group_name"
    }
  },
  "radio_groups": {
    "head_direction": ["up", "front"],
    "right_arm": ["hidden", "waist", "point_side", ...]
  },
  "composition_order": ["base_tail", "base_body", ...]
}
```

## トラブルシューティング

### よくある問題

1. **PSDファイルが見つからない**
   ```
   Error: PSD file not found: ../assets/zunda.3.2.psd
   ```
   → PSDファイルのパスを確認してください

2. **メモリ不足**
   ```
   MemoryError: Unable to allocate array
   ```
   → より多くのメモリを持つ環境で実行してください

3. **権限エラー**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   → 出力ディレクトリの書き込み権限を確認してください

### ログレベル

- `INFO`: 基本的な進捗情報
- `DEBUG`: 詳細なレイヤー処理情報（`--verbose`で有効）
- `WARNING`: 問題があるが続行可能な状況
- `ERROR`: 処理を停止する重大な問題

## 開発者向け情報

### ファイル構成

- `layer_extractor.py`: メインの抽出ロジック
- `extract_layers.py`: CLI インターフェース
- `requirements.txt`: 依存関係

### 拡張方法

新しい機能を追加する場合：

1. `ZundamonLayerExtractor`クラスにメソッドを追加
2. 必要に応じて`extract_layers.py`にオプションを追加
3. テストを実行して動作確認

### パフォーマンス

- **処理時間**: 約1-5分（レイヤー数による）
- **メモリ使用量**: 約500MB-2GB（PSDサイズによる）
- **出力サイズ**: 約5-20MB（レイヤー数・内容による）

## 本番システムとの連携

抽出されたレイヤーは`kiosk-backyard`の合成システムで使用されます：

1. `kiosk-factory`でレイヤー抽出
2. `assets/zundamon_layers/`に静的画像保存
3. `kiosk-backyard`で動的合成実行

## ライセンス

このプロジェクトの一部として、同じライセンスが適用されます。
