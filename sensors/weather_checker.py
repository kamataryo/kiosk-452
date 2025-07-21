#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天気予報チェッカー - ダミーファイル
このファイルはダミーです。実際の開発時に置き換えてください。
"""

import json
import random
import time
from datetime import datetime, timedelta

class WeatherChecker:
    """天気予報チェッククラス（ダミー実装）"""

    def __init__(self, api_key=None):
        """初期化"""
        self.api_key = api_key or "dummy_api_key"
        self.base_url = "https://api.openweathermap.org/data/2.5"
        print(f"[DUMMY] WeatherChecker initialized")

    def get_current_weather(self, lat, lon):
        """現在の天気を取得（ダミー実装）"""
        print(f"[DUMMY] Getting current weather for {lat}, {lon}")

        # ダミーの天気データ
        weather_conditions = ["sunny", "cloudy", "rainy", "partly_cloudy"]
        current_weather = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "current": {
                "temperature": random.uniform(15, 30),  # 気温（℃）
                "humidity": random.uniform(40, 80),     # 湿度（%）
                "pressure": random.uniform(1000, 1020), # 気圧（hPa）
                "wind_speed": random.uniform(0, 15),    # 風速（m/s）
                "wind_direction": random.uniform(0, 360), # 風向（度）
                "condition": random.choice(weather_conditions),
                "description": "晴れ時々曇り",
                "visibility": random.uniform(5, 20)     # 視界（km）
            }
        }

        print(f"[DUMMY] Current weather: {current_weather['current']['condition']}, {current_weather['current']['temperature']:.1f}°C")
        return current_weather

    def get_forecast(self, lat, lon, days=5):
        """天気予報を取得（ダミー実装）"""
        print(f"[DUMMY] Getting {days}-day forecast for {lat}, {lon}")

        forecast_data = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "forecast": []
        }

        weather_conditions = ["sunny", "cloudy", "rainy", "partly_cloudy"]

        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            daily_forecast = {
                "date": date.strftime("%Y-%m-%d"),
                "condition": random.choice(weather_conditions),
                "temperature": {
                    "max": random.uniform(20, 35),
                    "min": random.uniform(10, 20)
                },
                "humidity": random.uniform(40, 80),
                "precipitation_probability": random.uniform(0, 100),
                "precipitation_amount": random.uniform(0, 10) if random.random() > 0.7 else 0,
                "wind_speed": random.uniform(0, 15),
                "description": "晴れ時々曇り"
            }
            forecast_data["forecast"].append(daily_forecast)

        print(f"[DUMMY] Forecast retrieved for {days} days")
        return forecast_data

    def check_rain_alert(self, lat, lon, hours_ahead=3):
        """雨アラートをチェック（ダミー実装）"""
        print(f"[DUMMY] Checking rain alert for next {hours_ahead} hours")

        # ダミーの雨予報データ
        rain_alert = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "alert": {
                "is_rain_expected": random.choice([True, False]),
                "hours_until_rain": random.uniform(0.5, hours_ahead) if random.random() > 0.5 else None,
                "intensity": random.choice(["light", "moderate", "heavy"]),
                "duration_hours": random.uniform(0.5, 3),
                "probability": random.uniform(60, 95)
            }
        }

        if rain_alert["alert"]["is_rain_expected"]:
            hours = rain_alert["alert"]["hours_until_rain"]
            intensity = rain_alert["alert"]["intensity"]
            print(f"[DUMMY] RAIN ALERT: {intensity} rain expected in {hours:.1f} hours")
        else:
            print("[DUMMY] No rain expected in the next few hours")

        return rain_alert

    def get_weather_summary(self, lat, lon):
        """天気サマリーを取得"""
        current = self.get_current_weather(lat, lon)
        rain_alert = self.check_rain_alert(lat, lon)

        summary = {
            "current_condition": current["current"]["condition"],
            "current_temperature": current["current"]["temperature"],
            "rain_alert": rain_alert["alert"]["is_rain_expected"],
            "recommendation": self.get_driving_recommendation(current, rain_alert)
        }

        return summary

    def get_driving_recommendation(self, current_weather, rain_alert):
        """ドライブ推奨度を判定"""
        condition = current_weather["current"]["condition"]
        temp = current_weather["current"]["temperature"]
        rain_expected = rain_alert["alert"]["is_rain_expected"]

        if rain_expected:
            return "雨が予想されます。Smart Roadsterでのドライブは控えめに。"
        elif condition == "sunny" and 20 <= temp <= 28:
            return "絶好のドライブ日和です！Smart Roadsterで出かけましょう！"
        elif condition == "cloudy":
            return "曇りですが、ドライブには問題ありません。"
        else:
            return "天候を確認してからドライブしてください。"

def main():
    """メイン関数"""
    # ダミーの座標（東京駅）
    lat, lon = 35.6812, 139.7671

    weather = WeatherChecker()

    try:
        # 現在の天気
        current = weather.get_current_weather(lat, lon)
        print(f"Current weather: {json.dumps(current, indent=2, ensure_ascii=False)}")

        # 雨アラート
        rain_alert = weather.check_rain_alert(lat, lon)
        print(f"Rain alert: {json.dumps(rain_alert, indent=2, ensure_ascii=False)}")

        # サマリー
        summary = weather.get_weather_summary(lat, lon)
        print(f"Weather summary: {json.dumps(summary, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"[ERROR] Weather check failed: {e}")

if __name__ == "__main__":
    main()
