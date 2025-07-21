#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPS読み取りスクリプト - ダミーファイル
このファイルはダミーです。実際の開発時に置き換えてください。
"""

import time
import json
import random
from datetime import datetime

class GPSReader:
    """GPS読み取りクラス（ダミー実装）"""

    def __init__(self, device_path="/dev/ttyUSB0"):
        """初期化"""
        self.device_path = device_path
        self.is_connected = False
        self.current_location = None
        print(f"[DUMMY] GPSReader initialized for device: {device_path}")

    def connect(self):
        """GPS デバイスに接続（ダミー実装）"""
        print("[DUMMY] Connecting to GPS device...")
        # 実際の実装では serial ポートを開く
        self.is_connected = True
        print("[DUMMY] GPS device connected successfully")
        return True

    def disconnect(self):
        """GPS デバイスから切断"""
        print("[DUMMY] Disconnecting from GPS device...")
        self.is_connected = False
        print("[DUMMY] GPS device disconnected")

    def read_position(self):
        """現在位置を読み取り（ダミー実装）"""
        if not self.is_connected:
            print("[ERROR] GPS device not connected")
            return None

        # ダミーデータ（東京駅周辺の座標をランダムに生成）
        base_lat = 35.6812
        base_lon = 139.7671

        # 少しランダムに変動させる
        lat = base_lat + random.uniform(-0.001, 0.001)
        lon = base_lon + random.uniform(-0.001, 0.001)

        position_data = {
            "timestamp": datetime.now().isoformat(),
            "latitude": lat,
            "longitude": lon,
            "altitude": random.uniform(0, 50),  # 高度（メートル）
            "speed": random.uniform(0, 60),     # 速度（km/h）
            "heading": random.uniform(0, 360),  # 方位角
            "satellites": random.randint(4, 12), # 衛星数
            "quality": "good"  # GPS品質
        }

        self.current_location = position_data
        print(f"[DUMMY] GPS Position: {lat:.6f}, {lon:.6f}")
        return position_data

    def get_current_location(self):
        """現在位置を取得"""
        return self.current_location

    def reverse_geocode(self, lat, lon):
        """逆ジオコーディング（ダミー実装）"""
        print(f"[DUMMY] Reverse geocoding: {lat}, {lon}")

        # ダミーの住所データ
        dummy_address = {
            "country": "日本",
            "prefecture": "東京都",
            "city": "千代田区",
            "district": "丸の内",
            "postal_code": "100-0005",
            "formatted_address": "東京都千代田区丸の内1丁目"
        }

        print(f"[DUMMY] Address: {dummy_address['formatted_address']}")
        return dummy_address

    def start_monitoring(self, callback=None, interval=1):
        """位置監視を開始"""
        print(f"[DUMMY] Starting GPS monitoring (interval: {interval}s)")

        try:
            while self.is_connected:
                position = self.read_position()
                if position and callback:
                    callback(position)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[INFO] GPS monitoring stopped by user")
        except Exception as e:
            print(f"[ERROR] GPS monitoring error: {e}")

def main():
    """メイン関数"""
    gps = GPSReader()

    try:
        gps.connect()

        # 単発で位置を取得
        position = gps.read_position()
        if position:
            print(f"Current position: {json.dumps(position, indent=2, ensure_ascii=False)}")

            # 逆ジオコーディング
            address = gps.reverse_geocode(position['latitude'], position['longitude'])
            print(f"Address: {json.dumps(address, indent=2, ensure_ascii=False)}")

    finally:
        gps.disconnect()

if __name__ == "__main__":
    main()
