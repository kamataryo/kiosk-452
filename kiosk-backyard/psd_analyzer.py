#!/usr/bin/env python3
"""
PSD ファイル構造解析スクリプト
ずんだもんPSDファイルの構造を解析し、レイヤー情報を取得する
"""

import os
import sys
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
import json

def analyze_psd_structure(psd_path):
    """PSDファイルの構造を解析する"""
    if not os.path.exists(psd_path):
        print(f"Error: PSD file not found: {psd_path}")
        return None

    try:
        psd = PSDImage.open(psd_path)
        print(f"PSD File: {psd_path}")
        print(f"Size: {psd.width} x {psd.height}")
        print(f"Color Mode: {psd.color_mode}")
        print("=" * 50)

        structure = {
            "width": psd.width,
            "height": psd.height,
            "color_mode": str(psd.color_mode),
            "layers": []
        }

        def analyze_layer(layer, depth=0):
            """レイヤーを再帰的に解析"""
            indent = "  " * depth
            layer_info = {
                "name": layer.name,
                "type": type(layer).__name__,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "blend_mode": str(layer.blend_mode),
                "depth": depth
            }

            # PSDTool独自拡張の検出
            extensions = []
            if layer.name.startswith('*'):
                extensions.append("radio_button")
            if layer.name.startswith('!'):
                extensions.append("force_visible")
            if layer.name.endswith(':flipx'):
                extensions.append("flip_x")
            elif layer.name.endswith(':flipy'):
                extensions.append("flip_y")
            elif layer.name.endswith(':flipxy'):
                extensions.append("flip_xy")

            layer_info["extensions"] = extensions

            print(f"{indent}{layer.name} ({type(layer).__name__})")
            print(f"{indent}  Visible: {layer.visible}, Opacity: {layer.opacity}")
            if extensions:
                print(f"{indent}  Extensions: {', '.join(extensions)}")

            if isinstance(layer, Group):
                layer_info["children"] = []
                for child in layer:
                    child_info = analyze_layer(child, depth + 1)
                    layer_info["children"].append(child_info)
            elif isinstance(layer, PixelLayer):
                # ピクセルレイヤーの場合、バウンディングボックス情報を取得
                bbox = layer.bbox
                if bbox and len(bbox) >= 4:
                    layer_info["bbox"] = {
                        "left": bbox[0],
                        "top": bbox[1],
                        "right": bbox[2],
                        "bottom": bbox[3],
                        "width": bbox[2] - bbox[0],
                        "height": bbox[3] - bbox[1]
                    }
                    print(f"{indent}  BBox: {bbox}")
                else:
                    layer_info["bbox"] = None
                    print(f"{indent}  BBox: None")

            return layer_info

        print("Layer Structure:")
        print("-" * 30)

        for layer in psd:
            layer_info = analyze_layer(layer)
            structure["layers"].append(layer_info)

        return structure

    except Exception as e:
        print(f"Error analyzing PSD file: {e}")
        return None

def find_radio_groups(structure):
    """ラジオボタングループを特定する"""
    radio_groups = {}

    def find_radio_layers(layers, parent_name="root"):
        for layer in layers:
            if "radio_button" in layer.get("extensions", []):
                # 親グループ名をキーとしてラジオボタンをグループ化
                if parent_name not in radio_groups:
                    radio_groups[parent_name] = []
                radio_groups[parent_name].append(layer["name"])

            if "children" in layer:
                find_radio_layers(layer["children"], layer["name"])

    find_radio_layers(structure["layers"])
    return radio_groups

def generate_api_parameters(structure):
    """API パラメータ構造を生成する"""
    radio_groups = find_radio_groups(structure)

    api_params = {}
    for group_name, options in radio_groups.items():
        # レイヤー名から * を除去してクリーンな名前にする
        clean_options = [opt.lstrip('*') for opt in options]
        api_params[group_name.lower().replace(' ', '_')] = clean_options

    return api_params

if __name__ == "__main__":
    # PSDファイルのパスを指定
    psd_path = "/app/assets/zunda.3.2.psd"

    if len(sys.argv) > 1:
        psd_path = sys.argv[1]

    print("Zundamon PSD Structure Analyzer")
    print("=" * 50)

    structure = analyze_psd_structure(psd_path)

    if structure:
        print("\n" + "=" * 50)
        print("Radio Button Groups:")
        print("-" * 30)

        radio_groups = find_radio_groups(structure)
        for group, options in radio_groups.items():
            print(f"{group}: {options}")

        print("\n" + "=" * 50)
        print("Suggested API Parameters:")
        print("-" * 30)

        api_params = generate_api_parameters(structure)
        for param, options in api_params.items():
            print(f"{param}: {options}")

        # 結果をJSONファイルに保存
        output_file = "zundamon_psd_structure.json"
        output_data = {
            "structure": structure,
            "radio_groups": radio_groups,
            "api_parameters": api_params
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\nStructure saved to: {output_file}")
