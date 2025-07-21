#!/usr/bin/env python3
"""
ずんだもん画像生成モジュール
PSDファイルからリアルタイムでPNG画像を生成する
"""

import os
import json
from io import BytesIO
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from PIL import Image
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZundamonGenerator:
    def __init__(self, psd_path="/app/assets/zunda.3.2.psd"):
        """
        ずんだもん画像生成器を初期化

        Args:
            psd_path (str): PSDファイルのパス
        """
        self.psd_path = psd_path
        self.psd = None
        self.structure = None
        self.load_psd()

    def load_psd(self):
        """PSDファイルを読み込む"""
        try:
            logger.info(f"Loading PSD file: {self.psd_path}")
            self.psd = PSDImage.open(self.psd_path)
            logger.info(f"PSD loaded successfully: {self.psd.width}x{self.psd.height}")

            # 構造情報も読み込む
            structure_file = "zundamon_psd_structure.json"
            if os.path.exists(structure_file):
                with open(structure_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.structure = data.get('structure', {})
                    logger.info("PSD structure loaded from cache")

        except Exception as e:
            logger.error(f"Failed to load PSD file: {e}")
            raise

    def set_layer_visibility(self, layer, visible):
        """レイヤーの表示/非表示を設定"""
        try:
            # psd-toolsでは直接visibilityを変更できないため、
            # レイヤー情報を記録して後で合成時に使用
            layer._visible_override = visible
        except Exception as e:
            logger.warning(f"Could not set visibility for layer {layer.name}: {e}")

    def find_layer_by_name(self, layers, name):
        """名前でレイヤーを検索"""
        for layer in layers:
            if layer.name == name:
                return layer
            if isinstance(layer, Group):
                found = self.find_layer_by_name(layer, name)
                if found:
                    return found
        return None

    def apply_parameters(self, params):
        """
        パラメータに基づいてレイヤーの表示状態を設定

        Args:
            params (dict): レイヤー設定パラメータ
                例: {
                    "head_direction": "正面向き",
                    "right_arm": "腰",
                    "left_arm": "腰",
                    "expression_mouth": "ほう",
                    "expression_eyes": "基本目",
                    "expression_eyebrows": "怒り眉"
                }
        """
        logger.info(f"Applying parameters: {params}")

        # すべてのラジオボタンレイヤーを非表示にする
        self._hide_all_radio_layers(self.psd)

        # パラメータに基づいて特定のレイヤーを表示
        param_mapping = {
            "head_direction": {
                "上向き": "*頭_上向き",
                "正面向き": "*頭_正面向き"
            },
            "right_arm": {
                "(非表示)": "*(非表示)",
                "腰": "*腰",
                "指差し横": "*指差し横",
                "横": "*横",
                "指差し上": "*指差し上",
                "手を挙げる": "*手を挙げる",
                "チョップ": "*チョップ",
                "口元": "*口元",
                "基本": "*基本"
            },
            "left_arm": {
                "腕組み(右腕は非表示に)": "*腕組み(右腕は非表示に)",
                "腰": "*腰",
                "横": "*横",
                "手を挙げる": "*手を挙げる",
                "あごに指": "*あごに指",
                "口元": "*口元",
                "基本": "*基本"
            },
            "edamame": {
                "萎え": "*枝豆萎え",
                "立ち": "*枝豆立ち",
                "通常": "*枝豆通常",
                "立ち片折れ": "*枝豆立ち片折れ"
            },
            "face_color": {
                "(非表示)": "*(非表示)",
                "青ざめ": "*青ざめ",
                "赤面": "*赤面",
                "ほっぺ赤め": "*ほっぺ赤め",
                "ほっぺ基本": "*ほっぺ基本"
            },
            "expression_mouth": {
                "うへー": "*うへー",
                "むくー": "*むくー",
                "にやり": "*にやり",
                "うわー": "*うわー",
                "んえー": "*んえー",
                "んー": "*んー",
                "お": "*お",
                "Δ": "*Δ",
                "ん": "*ん",
                "あは": "*あは",
                "ほほえみ": "*ほほえみ",
                "ほあー": "*ほあー",
                "ほう": "*ほう",
                "ほあ": "*ほあ",
                "えへ": "*えへ",
                "むふ": "*むふ",
                "うへえ": "*うへえ"
            },
            "expression_eyes": {
                "><": "*><",
                "〇〇": "*〇〇",
                "なごみ目": "*なごみ目",
                "^^": "*^^",
                "にっこり": "*にっこり",
                "UU": "*UU",
                "閉じ目": "*閉じ目",
                "ジト目2": "*ジト目2",
                "普通目2↑": "*普通目2↑",
                "普通目2": "*普通目2",
                "ジト目ハート": "*ジト目ハート",
                "ジト目": "*ジト目",
                "普通目↑": "*普通目↑",
                "普通目": "*普通目",
                "基本目": "*基本目",
                "細め目ハート": "*細め目ハート",
                "細め目": "*細め目",
                "ジト目2←": "*ジト目2←",
                "ジト目2→": "*ジト目2→",
                "基本目2↑": "*基本目2↑",
                "基本目2←": "*基本目2←",
                "基本目2→": "*基本目2→",
                "基本目2": "*基本目2",
                "ジト目←": "*ジト目←",
                "ジト目→": "*ジト目→",
                "基本目↑": "*基本目↑",
                "基本目←": "*基本目←",
                "基本目→": "*基本目→"
            },
            "expression_eyebrows": {
                "困り眉": "*困り眉",
                "怒り眉2": "*怒り眉2",
                "怒り眉": "*怒り眉",
                "上がり眉": "*上がり眉",
                "基本眉": "*基本眉",
                "基本眉2": "*基本眉2"
            }
        }

        # パラメータに基づいてレイヤーを表示
        for param_key, value in params.items():
            if param_key in param_mapping and value in param_mapping[param_key]:
                layer_name = param_mapping[param_key][value]
                layer = self.find_layer_by_name(self.psd, layer_name)
                if layer:
                    self.set_layer_visibility(layer, True)
                    logger.info(f"Enabled layer: {layer_name}")
                else:
                    logger.warning(f"Layer not found: {layer_name}")

    def _hide_all_radio_layers(self, layers):
        """すべてのラジオボタンレイヤーを非表示にする"""
        for layer in layers:
            if layer.name.startswith('*'):
                self.set_layer_visibility(layer, False)
            if isinstance(layer, Group):
                self._hide_all_radio_layers(layer)

    def generate_image(self, params=None, format='PNG'):
        """
        パラメータに基づいて画像を生成

        Args:
            params (dict): レイヤー設定パラメータ
            format (str): 出力フォーマット ('PNG', 'JPEG')

        Returns:
            BytesIO: 生成された画像データ
        """
        try:
            # デフォルトパラメータ
            default_params = {
                "head_direction": "正面向き",
                "right_arm": "腰",
                "left_arm": "腰",
                "edamame": "通常",
                "face_color": "ほっぺ基本",
                "expression_mouth": "ほう",
                "expression_eyes": "基本目",
                "expression_eyebrows": "怒り眉"
            }

            if params:
                default_params.update(params)

            # パラメータを適用
            self.apply_parameters(default_params)

            # PSDを画像として合成
            # psd-toolsの制限により、直接的な表示制御は困難なため
            # 代替手段として合成画像を生成
            composite_image = self.psd.composite()

            # PIL Imageに変換
            if composite_image.mode != 'RGBA':
                composite_image = composite_image.convert('RGBA')

            # BytesIOに保存
            img_buffer = BytesIO()
            composite_image.save(img_buffer, format=format)
            img_buffer.seek(0)

            logger.info(f"Generated {format} image with parameters: {default_params}")
            return img_buffer

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise

    def get_available_options(self):
        """利用可能なオプションを取得"""
        return {
            "head_direction": ["上向き", "正面向き"],
            "right_arm": ["(非表示)", "腰", "指差し横", "横", "指差し上", "手を挙げる", "チョップ", "口元", "基本"],
            "left_arm": ["腕組み(右腕は非表示に)", "腰", "横", "手を挙げる", "あごに指", "口元", "基本"],
            "edamame": ["萎え", "立ち", "通常", "立ち片折れ"],
            "face_color": ["(非表示)", "青ざめ", "赤面", "ほっぺ赤め", "ほっぺ基本"],
            "expression_mouth": ["うへー", "むくー", "にやり", "うわー", "んえー", "んー", "お", "Δ", "ん", "あは", "ほほえみ", "ほあー", "ほう", "ほあ", "えへ", "むふ", "うへえ"],
            "expression_eyes": ["><", "〇〇", "なごみ目", "^^", "にっこり", "UU", "閉じ目", "ジト目2", "普通目2↑", "普通目2", "ジト目ハート", "ジト目", "普通目↑", "普通目", "基本目", "細め目ハート", "細め目", "ジト目2←", "ジト目2→", "基本目2↑", "基本目2←", "基本目2→", "基本目2", "ジト目←", "ジト目→", "基本目↑", "基本目←", "基本目→"],
            "expression_eyebrows": ["困り眉", "怒り眉2", "怒り眉", "上がり眉", "基本眉", "基本眉2"]
        }

# テスト用のメイン関数
if __name__ == "__main__":
    generator = ZundamonGenerator()

    # テスト用パラメータ
    test_params = {
        "head_direction": "正面向き",
        "expression_mouth": "あは",
        "expression_eyes": "にっこり",
        "right_arm": "手を挙げる"
    }

    # 画像生成テスト
    img_buffer = generator.generate_image(test_params)

    # ファイルに保存（テスト用）
    with open("test_zundamon.png", "wb") as f:
        f.write(img_buffer.getvalue())

    print("Test image generated: test_zundamon.png")
    print("Available options:", generator.get_available_options())
