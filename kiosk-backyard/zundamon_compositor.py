#!/usr/bin/env python3
"""
Zundamon Image Compositor
静的レイヤー画像を動的に合成してずんだもん画像を生成する
"""

import os
import json
from pathlib import Path
from PIL import Image
from io import BytesIO
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZundamonCompositor:
    def __init__(self, layers_dir: str = "/app/assets/zundamon_layers"):
        """
        ずんだもん合成器を初期化

        Args:
            layers_dir: レイヤー画像ディレクトリのパス
        """
        self.layers_dir = Path(layers_dir)
        self.layer_cache = {}  # メモリキャッシュ
        self.metadata = {}
        self.canvas_size = (1082, 1594)  # デフォルトサイズ

        self.load_metadata()

    def load_metadata(self) -> bool:
        """レイヤーメタデータを読み込む"""
        try:
            metadata_path = self.layers_dir / "layer_metadata.json"

            if not metadata_path.exists():
                logger.error(f"Metadata file not found: {metadata_path}")
                return False

            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

            # キャンバスサイズを更新
            psd_info = self.metadata.get("psd_info", {})
            if "width" in psd_info and "height" in psd_info:
                self.canvas_size = (psd_info["width"], psd_info["height"])

            logger.info(f"Loaded metadata for {len(self.metadata.get('layers', {}))} layers")
            logger.info(f"Canvas size: {self.canvas_size}")

            return True

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return False

    def get_layer_image(self, layer_name: str) -> Optional[Image.Image]:
        """レイヤー画像を取得（キャッシュ機能付き）"""
        try:
            # キャッシュから取得
            if layer_name in self.layer_cache:
                return self.layer_cache[layer_name]

            # メタデータから情報取得
            layer_info = self.metadata.get("layers", {}).get(layer_name)
            if not layer_info:
                logger.warning(f"Layer not found in metadata: {layer_name}")
                return None

            # 画像ファイルを読み込み
            image_path = self.layers_dir / layer_info["file"]
            if not image_path.exists():
                logger.warning(f"Layer image file not found: {image_path}")
                return None

            image = Image.open(image_path)

            # RGBA形式に変換
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # キャッシュに保存
            self.layer_cache[layer_name] = image

            return image

        except Exception as e:
            logger.error(f"Failed to load layer image {layer_name}: {e}")
            return None

    def clear_cache(self):
        """キャッシュをクリア"""
        self.layer_cache.clear()
        logger.info("Layer cache cleared")

    def get_available_options(self) -> Dict[str, List[str]]:
        """利用可能なオプションを取得"""
        try:
            radio_groups = self.metadata.get("radio_groups", {})

            # APIパラメータ形式に変換
            api_options = {}

            # パラメータマッピング（既存システムとの互換性）
            group_mapping = {
                "頭_上向き": "head_direction",
                "頭_正面向き": "head_direction",
                "右腕": "right_arm",
                "左腕": "left_arm",
                "枝豆": "edamame",
                "顔色": "face_color",
                "口": "expression_mouth",
                "目": "expression_eyes",
                "眉": "expression_eyebrows"
            }

            for group_name, options in radio_groups.items():
                # グループ名をAPIパラメータ名に変換
                api_param = group_mapping.get(group_name, group_name.lower().replace(' ', '_'))

                # オプション名をクリーンアップ
                clean_options = []
                for option in options:
                    # プレフィックスを除去してクリーンな名前に
                    clean_option = option.replace('_', ' ').replace('(', '').replace(')', '')
                    clean_options.append(clean_option)

                api_options[api_param] = clean_options

            # something_like_shippo パラメータを追加
            api_options["something_like_shippo"] = ["true", "false"]

            return api_options

        except Exception as e:
            logger.error(f"Failed to get available options: {e}")
            return {}

    def resolve_layer_names(self, params: Dict[str, str]) -> List[str]:
        """パラメータからレイヤー名のリストを解決"""
        try:
            layer_names = []

            # 強制表示レイヤーを追加
            for layer_name, layer_info in self.metadata.get("layers", {}).items():
                if layer_info.get("required", False):
                    layer_names.append(layer_name)

            # パラメータに基づいてレイヤーを選択
            radio_groups = self.metadata.get("radio_groups", {})

            # パラメータマッピング（逆引き）
            param_to_group = {
                "head_direction": ["頭_上向き", "頭_正面向き"],
                "right_arm": ["右腕"],
                "left_arm": ["左腕"],
                "edamame": ["枝豆"],
                "face_color": ["顔色"],
                "expression_mouth": ["口"],
                "expression_eyes": ["目"],
                "expression_eyebrows": ["眉"]
            }

            for param_name, value in params.items():
                if param_name == "something_like_shippo":
                    # 尻尾のような何かレイヤーの処理
                    if value.lower() == "true":
                        layer_names.append("尻尾のような何か")
                elif param_name in param_to_group:
                    # 対応するグループを検索
                    for group_name in param_to_group[param_name]:
                        if group_name in radio_groups:
                            # 値に対応するレイヤーを検索
                            for layer_name in radio_groups[group_name]:
                                layer_info = self.metadata.get("layers", {}).get(layer_name, {})
                                original_name = layer_info.get("original_name", "")

                                # 値とレイヤー名をマッチング
                                if self._match_parameter_value(value, original_name, layer_name):
                                    layer_names.append(layer_name)
                                    break

            return layer_names

        except Exception as e:
            logger.error(f"Failed to resolve layer names: {e}")
            return []

    def _match_parameter_value(self, param_value: str, original_name: str, layer_name: str) -> bool:
        """パラメータ値とレイヤー名のマッチング"""
        # 複数のマッチング方法を試行
        param_clean = param_value.lower().replace(' ', '').replace('(', '').replace(')', '')
        original_clean = original_name.lower().replace('*', '').replace('!', '').replace(' ', '').replace('(', '').replace(')', '')
        layer_clean = layer_name.lower().replace('_', '').replace(' ', '')

        return (param_clean in original_clean or
                param_clean in layer_clean or
                original_clean.endswith(param_clean) or
                layer_clean.endswith(param_clean))

    def compose_image(self, params: Dict[str, str] = None, format: str = 'PNG') -> BytesIO:
        """
        パラメータに基づいて画像を合成

        Args:
            params: レイヤー設定パラメータ
            format: 出力フォーマット ('PNG', 'JPEG')

        Returns:
            BytesIO: 合成された画像データ
        """
        try:
            # デフォルトパラメータ
            if params is None:
                params = {}

            default_params = {
                "head_direction": "正面向き",
                "right_arm": "腰",
                "left_arm": "腰",
                "edamame": "通常",
                "face_color": "ほっぺ基本",
                "expression_mouth": "ほう",
                "expression_eyes": "基本目",
                "expression_eyebrows": "怒り眉",
                "something_like_shippo": "true"
            }

            # デフォルト値で不足分を補完
            for key, value in default_params.items():
                if key not in params:
                    params[key] = value

            # レイヤー名を解決
            layer_names = self.resolve_layer_names(params)

            if not layer_names:
                logger.warning("No layers resolved from parameters")
                layer_names = ["base_body"]  # フォールバック

            logger.info(f"Composing with layers: {layer_names}")

            # キャンバスを作成
            canvas = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))

            # 合成順序に従ってレイヤーを合成
            composition_order = self.metadata.get("composition_order", [])

            # 合成順序に含まれるレイヤーを優先して合成
            for layer_name in composition_order:
                if layer_name in layer_names:
                    self._composite_layer(canvas, layer_name)

            # 順序に含まれていないレイヤーも合成
            for layer_name in layer_names:
                if layer_name not in composition_order:
                    self._composite_layer(canvas, layer_name)

            # 最終画像の形式を調整
            if format.upper() == 'JPEG':
                # JPEGの場合は白背景に変換
                jpeg_image = Image.new('RGB', canvas.size, (255, 255, 255))
                jpeg_image.paste(canvas, mask=canvas.split()[-1])
                final_image = jpeg_image
            else:
                final_image = canvas

            # BytesIOに保存
            img_buffer = BytesIO()
            final_image.save(img_buffer, format=format.upper())
            img_buffer.seek(0)

            logger.info(f"Generated {format} image with {len(layer_names)} layers")
            return img_buffer

        except Exception as e:
            logger.error(f"Failed to compose image: {e}")
            raise

    def _alpha_composite_numpy(self, dst_array: np.ndarray, src_array: np.ndarray, position: Tuple[int, int]) -> np.ndarray:
        """
        NumPyを使用した正しいアルファコンポジティング

        Args:
            dst_array: 背景画像のNumPy配列 (H, W, 4)
            src_array: 前景画像のNumPy配列 (H, W, 4)
            position: 前景画像の配置位置 (x, y)

        Returns:
            合成後の画像のNumPy配列
        """
        dst_h, dst_w = dst_array.shape[:2]
        src_h, src_w = src_array.shape[:2]
        x, y = position

        # 配置範囲を計算
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(dst_w, x + src_w)
        y_end = min(dst_h, y + src_h)

        # 有効な範囲がない場合は元の配列を返す
        if x_start >= x_end or y_start >= y_end:
            return dst_array

        # ソース画像の対応する範囲を計算
        src_x_start = max(0, -x)
        src_y_start = max(0, -y)
        src_x_end = src_x_start + (x_end - x_start)
        src_y_end = src_y_start + (y_end - y_start)

        # 対象領域を抽出
        dst_region = dst_array[y_start:y_end, x_start:x_end].astype(np.float32) / 255.0
        src_region = src_array[src_y_start:src_y_end, src_x_start:src_x_end].astype(np.float32) / 255.0

        # アルファチャンネルを分離
        dst_rgb = dst_region[:, :, :3]
        dst_alpha = dst_region[:, :, 3:4]
        src_rgb = src_region[:, :, :3]
        src_alpha = src_region[:, :, 3:4]

        # アルファコンポジティングの計算
        # result_alpha = src_alpha + dst_alpha * (1 - src_alpha)
        result_alpha = src_alpha + dst_alpha * (1 - src_alpha)

        # ゼロ除算を避けるため、result_alphaが0の場合の処理
        alpha_mask = result_alpha > 0

        # result_color = (src_color * src_alpha + dst_color * dst_alpha * (1 - src_alpha)) / result_alpha
        result_rgb = np.zeros_like(dst_rgb)
        result_rgb[alpha_mask.squeeze()] = (
            (src_rgb * src_alpha + dst_rgb * dst_alpha * (1 - src_alpha))[alpha_mask.squeeze()] /
            result_alpha[alpha_mask.squeeze()]
        )

        # 結果を結合
        result_region = np.concatenate([result_rgb, result_alpha], axis=2)

        # 結果を元の配列にコピー
        result_array = dst_array.copy().astype(np.float32) / 255.0
        result_array[y_start:y_end, x_start:x_end] = result_region

        # 0-255の範囲に戻す
        return (result_array * 255).astype(np.uint8)

    def _composite_layer(self, canvas: Image.Image, layer_name: str) -> bool:
        """レイヤーをキャンバスに合成（改良されたアルファコンポジティング使用）"""
        try:
            layer_image = self.get_layer_image(layer_name)
            if not layer_image:
                return False

            layer_info = self.metadata.get("layers", {}).get(layer_name, {})
            bbox = layer_info.get("bbox")

            if bbox:
                # 位置情報がある場合は指定位置に配置
                position = (bbox["left"], bbox["top"])
            else:
                # 位置情報がない場合は中央配置
                x = (canvas.width - layer_image.width) // 2
                y = (canvas.height - layer_image.height) // 2
                position = (x, y)

            # NumPyを使用した正しいアルファコンポジティング
            canvas_array = np.array(canvas)
            layer_array = np.array(layer_image)

            # アルファコンポジティングを実行
            result_array = self._alpha_composite_numpy(canvas_array, layer_array, position)

            # 結果をPIL Imageに変換してキャンバスを更新
            result_image = Image.fromarray(result_array, 'RGBA')
            canvas.paste(result_image, (0, 0))

            logger.debug(f"Composited layer: {layer_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to composite layer {layer_name}: {e}")
            return False

# テスト用のメイン関数
if __name__ == "__main__":
    compositor = ZundamonCompositor()

    # テスト用パラメータ
    test_params = {
        "head_direction": "正面向き",
        "expression_mouth": "あは",
        "expression_eyes": "にっこり",
        "right_arm": "手を挙げる"
    }

    # 画像合成テスト
    try:
        img_buffer = compositor.compose_image(test_params)

        # ファイルに保存（テスト用）
        with open("test_zundamon_compositor.png", "wb") as f:
            f.write(img_buffer.getvalue())

        print("Test image generated: test_zundamon_compositor.png")
        print("Available options:", compositor.get_available_options())

    except Exception as e:
        print(f"Test failed: {e}")
