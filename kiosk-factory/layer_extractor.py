#!/usr/bin/env python3
"""
Zundamon Layer Extractor
PSDファイルから個別レイヤーを抽出し、静的画像として保存する
"""

import os
import json
from pathlib import Path
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from PIL import Image
import logging
from typing import Dict, List, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZundamonLayerExtractor:
    def __init__(self, psd_path: str = "../assets/zunda.3.2.psd", output_dir: str = "../assets/zundamon_layers"):
        """
        ずんだもんレイヤー抽出器を初期化

        Args:
            psd_path: PSDファイルのパス
            output_dir: 出力ディレクトリ
        """
        self.psd_path = Path(psd_path)
        self.output_dir = Path(output_dir)
        self.psd = None
        self.layer_metadata = {
            "version": "2.0",
            "psd_info": {},
            "layers": {},
            "radio_groups": {},
            "composition_order": []
        }

    def load_psd(self) -> bool:
        """PSDファイルを読み込む"""
        try:
            if not self.psd_path.exists():
                logger.error(f"PSD file not found: {self.psd_path}")
                return False

            logger.info(f"Loading PSD file: {self.psd_path}")
            self.psd = PSDImage.open(str(self.psd_path))

            # PSD基本情報を記録
            self.layer_metadata["psd_info"] = {
                "width": self.psd.width,
                "height": self.psd.height,
                "color_mode": str(self.psd.color_mode),
                "source_file": self.psd_path.name
            }

            logger.info(f"PSD loaded: {self.psd.width}x{self.psd.height}")
            return True

        except Exception as e:
            logger.error(f"Failed to load PSD: {e}")
            return False

    def analyze_layer_structure(self) -> None:
        """レイヤー構造を解析してメタデータを生成"""
        logger.info("Analyzing layer structure...")

        radio_groups = {}
        composition_order = []
        z_index = 0

        def process_layer(layer, parent_group: str = "root", depth: int = 0) -> None:
            nonlocal z_index

            layer_name = layer.name
            logger.debug(f"{'  ' * depth}Processing: {layer_name}")

            # PSDTool独自拡張の検出
            is_radio_button = layer_name.startswith('*')
            is_force_visible = layer_name.startswith('!')

            if isinstance(layer, Group):
                # グループレイヤーの処理
                group_name = layer_name.lstrip('*!')

                # 子レイヤーを処理
                for child in layer:
                    process_layer(child, group_name, depth + 1)

            elif isinstance(layer, PixelLayer):
                # ピクセルレイヤーの処理
                clean_name = self._generate_clean_name(layer_name, parent_group)
                file_path = self._generate_file_path(clean_name, parent_group)

                # バウンディングボックス取得
                bbox = layer.bbox
                bbox_info = None
                if bbox and len(bbox) >= 4:
                    bbox_info = {
                        "left": bbox[0],
                        "top": bbox[1],
                        "right": bbox[2],
                        "bottom": bbox[3],
                        "width": bbox[2] - bbox[0],
                        "height": bbox[3] - bbox[1]
                    }

                # レイヤーメタデータを記録
                layer_info = {
                    "original_name": layer_name,
                    "file": file_path,
                    "bbox": bbox_info,
                    "z_index": z_index,
                    "visible": layer.visible,
                    "opacity": layer.opacity,
                    "blend_mode": str(layer.blend_mode),
                    "required": is_force_visible,
                    "parent_group": parent_group
                }

                if is_radio_button:
                    layer_info["radio_group"] = parent_group

                    # ラジオグループに追加
                    if parent_group not in radio_groups:
                        radio_groups[parent_group] = []
                    radio_groups[parent_group].append(clean_name)

                self.layer_metadata["layers"][clean_name] = layer_info
                composition_order.append(clean_name)
                z_index += 1

        # 全レイヤーを処理
        for layer in self.psd:
            process_layer(layer)

        self.layer_metadata["radio_groups"] = radio_groups
        self.layer_metadata["composition_order"] = composition_order

        logger.info(f"Found {len(self.layer_metadata['layers'])} layers")
        logger.info(f"Found {len(radio_groups)} radio groups")

    def _generate_clean_name(self, layer_name: str, parent_group: str) -> str:
        """レイヤー名からクリーンな名前を生成"""
        # プレフィックスを除去
        clean = layer_name.lstrip('*!')

        # 特殊文字を置換
        clean = clean.replace('(', '').replace(')', '').replace(' ', '_')
        clean = clean.replace('・', '_').replace('、', '_').replace('。', '')

        # 親グループ名をプレフィックスとして追加（rootは除く）
        if parent_group != "root" and not clean.startswith(parent_group.lower()):
            parent_clean = parent_group.lower().replace(' ', '_')
            clean = f"{parent_clean}_{clean}"

        return clean.lower()

    def _generate_file_path(self, clean_name: str, parent_group: str) -> str:
        """ファイルパスを生成"""
        if parent_group == "root":
            return f"base/{clean_name}.png"
        else:
            group_dir = parent_group.lower().replace(' ', '_')
            return f"{group_dir}/{clean_name}.png"

    def _set_all_layers_invisible(self, layer, exclude_layer: PixelLayer = None) -> Dict:
        """全レイヤーを非表示にし、元の状態を記録"""
        states = {}

        def process_recursive(l):
            if isinstance(l, Group):
                # グループの状態を記録・変更
                states[l] = getattr(l, 'visible', True)
                l.visible = False
                if hasattr(l, '_record') and hasattr(l._record, 'visible'):
                    states[f"{l}_record"] = l._record.visible
                    l._record.visible = False

                # 子レイヤーを処理
                for child in l:
                    process_recursive(child)

            elif isinstance(l, PixelLayer):
                if l != exclude_layer:
                    # レイヤーの状態を記録・変更
                    states[l] = getattr(l, 'visible', True)
                    l.visible = False
                    if hasattr(l, '_record') and hasattr(l._record, 'visible'):
                        states[f"{l}_record"] = l._record.visible
                        l._record.visible = False

        for root_layer in self.psd:
            process_recursive(root_layer)

        return states

    def _restore_layer_states(self, states: Dict) -> None:
        """レイヤーの状態を復元"""
        for obj, state in states.items():
            if isinstance(obj, str) and obj.endswith('_record'):
                # _record属性の復元は後で処理
                continue
            else:
                # 通常の可視性復元
                if hasattr(obj, 'visible'):
                    obj.visible = state

        # _record属性の復元
        for obj_key, state in states.items():
            if isinstance(obj_key, str) and obj_key.endswith('_record'):
                obj_name = obj_key.replace('_record', '')
                for obj in states.keys():
                    if not isinstance(obj, str) and str(obj) == obj_name:
                        if hasattr(obj, '_record') and hasattr(obj._record, 'visible'):
                            obj._record.visible = state
                        break

    def extract_layer_image(self, layer: PixelLayer, parent_group_layer: Optional[Group] = None) -> Optional[Image.Image]:
        """レイヤーから画像を抽出（改良版）"""
        try:
            logger.debug(f"Extracting layer: {layer.name}")

            # 方法1: レイヤー単体での抽出を試行
            try:
                layer_image = layer.composite()
                if layer_image and layer_image.size[0] > 0 and layer_image.size[1] > 0:
                    # 透明度チェック
                    if layer_image.mode == 'RGBA':
                        alpha = layer_image.split()[-1]
                        if alpha.getextrema()[1] > 0:  # 透明でない
                            logger.debug(f"Method 1 success for {layer.name}")
                            return self._process_layer_image(layer_image, layer.name)
            except Exception as e:
                logger.debug(f"Method 1 failed for {layer.name}: {e}")

            # 方法2: topil()メソッドを試行
            try:
                layer_image = layer.topil()
                if layer_image and layer_image.size[0] > 0 and layer_image.size[1] > 0:
                    # 透明度チェック
                    if layer_image.mode == 'RGBA':
                        alpha = layer_image.split()[-1]
                        if alpha.getextrema()[1] > 0:  # 透明でない
                            logger.debug(f"Method 2 success for {layer.name}")
                            return self._process_layer_image(layer_image, layer.name)
            except Exception as e:
                logger.debug(f"Method 2 failed for {layer.name}: {e}")

            # 方法3: PSD全体の状態制御による抽出
            logger.debug(f"Trying method 3 for {layer.name}")

            # 全レイヤーを非表示にして状態を保存
            original_states = self._set_all_layers_invisible(layer, exclude_layer=layer)

            try:
                # 対象レイヤーとその親グループを表示状態に
                layer.visible = True
                if hasattr(layer, '_record') and hasattr(layer._record, 'visible'):
                    layer._record.visible = True

                # 親グループチェーンを表示状態に
                current_group = parent_group_layer
                while current_group:
                    current_group.visible = True
                    if hasattr(current_group, '_record') and hasattr(current_group._record, 'visible'):
                        current_group._record.visible = True
                    # 親グループを探す（簡易実装）
                    current_group = None  # TODO: 親グループの取得ロジック

                # PSD全体を合成してレイヤー部分を切り出し
                psd_image = self.psd.composite()
                if psd_image and layer.bbox:
                    bbox = layer.bbox
                    if len(bbox) >= 4 and bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                        layer_image = psd_image.crop(bbox)
                        if layer_image and layer_image.size[0] > 0 and layer_image.size[1] > 0:
                            logger.debug(f"Method 3 success for {layer.name}")
                            return self._process_layer_image(layer_image, layer.name)

            finally:
                # 状態を復元
                self._restore_layer_states(original_states)

            logger.warning(f"All methods failed for layer: {layer.name}")
            return None

        except Exception as e:
            logger.error(f"Failed to extract image from layer {layer.name}: {e}")
            return None

    def _process_layer_image(self, layer_image: Image.Image, layer_name: str) -> Optional[Image.Image]:
        """レイヤー画像の後処理"""
        try:
            # RGBA形式に変換
            if layer_image.mode != 'RGBA':
                layer_image = layer_image.convert('RGBA')

            # 透明度チェック
            if layer_image.mode == 'RGBA':
                alpha = layer_image.split()[-1]
                if alpha.getextrema()[1] == 0:  # 完全に透明
                    logger.warning(f"Layer {layer_name} is completely transparent")
                    return None

            logger.debug(f"Successfully processed layer {layer_name}: {layer_image.size}")
            return layer_image

        except Exception as e:
            logger.error(f"Failed to process layer image {layer_name}: {e}")
            return None

    def extract_all_layers(self, dry_run: bool = False) -> Dict[str, any]:
        """全レイヤーを抽出"""
        if not self.load_psd():
            return {"success": False, "error": "Failed to load PSD"}

        self.analyze_layer_structure()

        # Dry-run情報を計算
        total_layers = len(self.layer_metadata["layers"])
        estimated_size_mb = total_layers * 0.1  # 1レイヤー約100KB想定

        dry_run_info = {
            "total_layers": total_layers,
            "estimated_size_mb": round(estimated_size_mb, 2),
            "radio_groups": len(self.layer_metadata["radio_groups"]),
            "output_directory": str(self.output_dir)
        }

        if dry_run:
            logger.info("=== DRY RUN RESULTS ===")
            logger.info(f"Total layers to extract: {total_layers}")
            logger.info(f"Estimated total size: {estimated_size_mb:.2f} MB")
            logger.info(f"Radio groups: {len(self.layer_metadata['radio_groups'])}")
            logger.info(f"Output directory: {self.output_dir}")
            return {"success": True, "dry_run": True, "info": dry_run_info}

        # 実際の抽出処理
        logger.info(f"Starting extraction of {total_layers} layers...")

        # 出力ディレクトリを作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

        extracted_count = 0
        failed_count = 0

        def extract_layer_recursive(layer, parent_group: str = "root", parent_group_layer: Optional[Group] = None) -> None:
            nonlocal extracted_count, failed_count

            if isinstance(layer, Group):
                group_name = layer.name.lstrip('*!')
                for child in layer:
                    extract_layer_recursive(child, group_name, layer)

            elif isinstance(layer, PixelLayer):
                clean_name = self._generate_clean_name(layer.name, parent_group)

                if clean_name in self.layer_metadata["layers"]:
                    layer_info = self.layer_metadata["layers"][clean_name]
                    file_path = self.output_dir / layer_info["file"]

                    # ディレクトリを作成
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # レイヤー画像を抽出（親グループレイヤー情報を渡す）
                    layer_image = self.extract_layer_image(layer, parent_group_layer)

                    if layer_image:
                        try:
                            layer_image.save(str(file_path), "PNG", optimize=True)
                            logger.info(f"Extracted: {file_path}")
                            extracted_count += 1
                        except Exception as e:
                            logger.error(f"Failed to save {file_path}: {e}")
                            failed_count += 1
                    else:
                        logger.warning(f"No image data for layer: {layer.name}")
                        failed_count += 1

        # 全レイヤーを抽出
        for layer in self.psd:
            extract_layer_recursive(layer)

        # メタデータを保存
        metadata_path = self.output_dir / "layer_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.layer_metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Extraction completed: {extracted_count} success, {failed_count} failed")
        logger.info(f"Metadata saved to: {metadata_path}")

        return {
            "success": True,
            "extracted": extracted_count,
            "failed": failed_count,
            "metadata_path": str(metadata_path),
            "info": dry_run_info
        }

if __name__ == "__main__":
    extractor = ZundamonLayerExtractor()

    # Dry-run実行
    print("=== Zundamon Layer Extractor ===")
    print("Running dry-run analysis...")
    result = extractor.extract_all_layers(dry_run=True)

    if result["success"]:
        print(f"\nDry-run completed successfully!")
        print(f"Layers to extract: {result['info']['total_layers']}")
        print(f"Estimated size: {result['info']['estimated_size_mb']} MB")

        # 実際の抽出を実行するか確認
        response = input("\nProceed with actual extraction? (y/N): ")
        if response.lower() == 'y':
            print("\nStarting actual extraction...")
            result = extractor.extract_all_layers(dry_run=False)

            if result["success"]:
                print(f"\nExtraction completed!")
                print(f"Successfully extracted: {result['extracted']} layers")
                print(f"Failed: {result['failed']} layers")
            else:
                print(f"Extraction failed: {result.get('error', 'Unknown error')}")
        else:
            print("Extraction cancelled.")
    else:
        print(f"Dry-run failed: {result.get('error', 'Unknown error')}")
