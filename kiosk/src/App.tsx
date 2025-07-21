import { useState, useEffect } from 'react';
import './App.css';

interface GPSData {
  latitude: number;
  longitude: number;
  address: string;
}

interface WeatherData {
  temperature: number;
  condition: string;
  humidity: number;
  rainAlert: boolean;
}

interface VoiceStatus {
  isPlaying: boolean;
  lastMessage: string;
}

function App() {
  const [currentTime, setCurrentTime] = useState<string>('');
  const [gpsData, setGpsData] = useState<GPSData | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // 現在時刻の更新
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('ja-JP'));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // APIからデータを取得
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // GPS データ取得
        const gpsResponse = await fetch('/api/gps');
        if (gpsResponse.ok) {
          const gpsResult = await gpsResponse.json();
          setGpsData(gpsResult.data);
        }

        // 天気データ取得
        const weatherResponse = await fetch('/api/weather');
        if (weatherResponse.ok) {
          const weatherResult = await weatherResponse.json();
          setWeatherData(weatherResult.data);
        }

        // 音声ステータス取得
        const voiceResponse = await fetch('/api/voice/status');
        if (voiceResponse.ok) {
          const voiceResult = await voiceResponse.json();
          setVoiceStatus(voiceResult.data);
        }

      } catch (error) {
        console.error('API通信エラー:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // 30秒ごとにデータを更新
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleVoiceTest = async () => {
    try {
      const response = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: 'こんにちは！Smart Roadsterのキオスクシステムです。'
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('音声再生:', result);
      }
    } catch (error) {
      console.error('音声再生エラー:', error);
    }
  };

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">
          <h2>🚗 Smart Roadster Kiosk</h2>
          <p>システムを起動中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚗 Smart Roadster Kiosk</h1>
        <div className="current-time">{currentTime}</div>
      </header>

      <main className="app-main">
        <div className="status-grid">
          {/* GPS情報 */}
          <div className="status-card gps-card">
            <h2>📍 位置情報</h2>
            {gpsData ? (
              <div>
                <p><strong>緯度:</strong> {gpsData.latitude.toFixed(6)}</p>
                <p><strong>経度:</strong> {gpsData.longitude.toFixed(6)}</p>
                <p><strong>住所:</strong> {gpsData.address}</p>
              </div>
            ) : (
              <p className="error">GPS情報を取得できませんでした</p>
            )}
          </div>

          {/* 天気予報 */}
          <div className={`status-card weather-card ${weatherData?.rainAlert ? 'rain-alert' : ''}`}>
            <h2>🌤️ 天気予報</h2>
            {weatherData ? (
              <div>
                <p><strong>気温:</strong> {weatherData.temperature}°C</p>
                <p><strong>天候:</strong> {weatherData.condition}</p>
                <p><strong>湿度:</strong> {weatherData.humidity}%</p>
                {weatherData.rainAlert && (
                  <div className="rain-alert-message">
                    ⚠️ 雨の接近を検知しました！屋根を閉めることをお勧めします。
                  </div>
                )}
              </div>
            ) : (
              <p className="error">天気情報を取得できませんでした</p>
            )}
          </div>

          {/* 音声システム */}
          <div className="status-card voice-card">
            <h2>🗣️ ずんだもん音声システム</h2>
            {voiceStatus ? (
              <div>
                <p><strong>ステータス:</strong> {voiceStatus.isPlaying ? '再生中' : '待機中'}</p>
                <p><strong>最後のメッセージ:</strong> {voiceStatus.lastMessage}</p>
                <button onClick={handleVoiceTest} className="voice-test-btn">
                  音声テスト
                </button>
              </div>
            ) : (
              <p className="error">音声システムに接続できませんでした</p>
            )}
          </div>

          {/* システム情報 */}
          <div className="status-card system-card">
            <h2>⚙️ システム情報</h2>
            <p><strong>フロントエンド:</strong> React + TypeScript</p>
            <p><strong>バックエンド:</strong> Flask API</p>
            <p><strong>配信:</strong> nginx</p>
            <p><strong>最終更新:</strong> {new Date().toLocaleString('ja-JP')}</p>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Smart Roadster Kiosk System - 雨に負けないドライブのために 🌧️🚗</p>
      </footer>
    </div>
  );
}

export default App;
