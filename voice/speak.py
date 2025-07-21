#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VOICEVOX音声出力スクリプト - ダミーファイル
このファイルはダミーです。実際の開発時に置き換えてください。
"""

import json
import sys
import os
from pathlib import Path

class ZundamonSpeaker:
    """ずんだもん音声出力クラス（ダミー実装）"""

    def __init__(self, config_path="zundamon.json"):
        """初期化"""
        self.config_path = Path(__file__).parent / config_path
        self.config = self.load_config()
        print(f"[DUMMY] ZundamonSpeaker initialized with config: {config_path}")

    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] Config file not found: {self.config_path}")
            return {}

    def speak(self, text, animation="speaking"):
        """テキストを音声出力（ダミー実装）"""
        print(f"[DUMMY] ずんだもん: {text}")
        print(f"[DUMMY] Animation: {animation}")

        # 実際の実装では以下のような処理を行う予定：
        # 1. VOICEVOX APIに音声合成リクエスト
        # 2. 音声ファイルを取得
        # 3. 音声を再生
        # 4. アニメーション表示

        return True

    def speak_script(self, script_key, animation=None):
        """定型文を音声出力"""
        scripts = self.config.get('scripts', {})
        if script_key in scripts:
            text = scripts[script_key]
            if animation is None:
                animation = "speaking"
            return self.speak(text, animation)
        else:
            print(f"[ERROR] Script key not found: {script_key}")
            return False

    def get_available_scripts(self):
        """利用可能な定型文一覧を取得"""
        return list(self.config.get('scripts', {}).keys())

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("Usage: python speak.py <text_or_script_key>")
        print("Available script keys:")
        speaker = ZundamonSpeaker()
        for key in speaker.get_available_scripts():
            print(f"  - {key}")
        sys.exit(1)

    speaker = ZundamonSpeaker()
    input_text = sys.argv[1]

    # 定型文キーかどうかチェック
    if input_text in speaker.get_available_scripts():
        speaker.speak_script(input_text)
    else:
        speaker.speak(input_text)

if __name__ == "__main__":
    main()
