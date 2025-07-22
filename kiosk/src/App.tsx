import { useState, useEffect } from 'react';
import './App.css';
import { useWebSocket } from './hooks/useWebSocket';

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

interface ZundamonParams {
  head_direction: string;
  right_arm: string;
  left_arm: string;
  edamame: string;
  face_color: string;
  expression_mouth: string;
  expression_eyes: string;
  expression_eyebrows: string;
}

function App() {
  const [currentTime, setCurrentTime] = useState<string>('');
  const [gpsData, setGpsData] = useState<GPSData | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [zundamonParams, setZundamonParams] = useState<ZundamonParams | null>(null);
  const [zundamonUrl, setZundamonUrl] = useState<string>('');

  // WebSocket接続とVOICEVOX音声システム
  const {
    connected,
    systemStatus,
    isProcessing,
    synthesizeVoice,
    getSpeakers,
    speakWithBrowserTTS
  } = useWebSocket();

  console.log(currentTime, gpsData, weatherData, voiceStatus)
  // ずんだもんのランダムパラメータ生成
  const generateRandomZundamonParams = (): ZundamonParams => {
    const options = {
      head_direction: ['正面向き', '上向き'],
      right_arm: ['腰', '指差し横', '手を挙げる', '基本', '横', '指差し上'],
      left_arm: ['腰', '横', '手を挙げる', '基本', 'あごに指', '口元'],
      edamame: ['通常', '立ち', '萎え', '立ち片折れ'],
      face_color: ['ほっぺ基本', 'ほっぺ赤め', '赤面', '青ざめ', '非表示'],
      expression_mouth: ['ほう', 'あは', 'ほほえみ', 'えへ', 'にやり', 'むふ', 'お', 'ん'],
      expression_eyes: ['基本目', 'にっこり', '^^', 'なごみ目', '閉じ目', 'ジト目', '〇〇'],
      expression_eyebrows: ['基本眉', '怒り眉', '困り眉', '上がり眉', '怒り眉2']
    };

    return {
      head_direction: options.head_direction[Math.floor(Math.random() * options.head_direction.length)],
      right_arm: options.right_arm[Math.floor(Math.random() * options.right_arm.length)],
      left_arm: options.left_arm[Math.floor(Math.random() * options.left_arm.length)],
      edamame: options.edamame[Math.floor(Math.random() * options.edamame.length)],
      face_color: options.face_color[Math.floor(Math.random() * options.face_color.length)],
      expression_mouth: options.expression_mouth[Math.floor(Math.random() * options.expression_mouth.length)],
      expression_eyes: options.expression_eyes[Math.floor(Math.random() * options.expression_eyes.length)],
      expression_eyebrows: options.expression_eyebrows[Math.floor(Math.random() * options.expression_eyebrows.length)]
    };
  };

  // ずんだもんURLを生成
  const generateZundamonUrl = (params: ZundamonParams): string => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      queryParams.append(key, value);
    });
    return `/api/zundamon/generate?${queryParams.toString()}`;
  };

  // ずんだもんの3秒間隔更新
  useEffect(() => {
    const updateZundamon = () => {
      const params = generateRandomZundamonParams();
      const url = generateZundamonUrl(params);
      setZundamonParams(params);
      setZundamonUrl(url);
    };

    updateZundamon(); // 初回実行
    const interval = setInterval(updateZundamon, 3000);
    return () => clearInterval(interval);
  }, []);

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
    // const interval = setInterval(fetchData, 30000);
    // return () => clearInterval(interval);
  }, []);

  // VOICEVOX音声テスト
  const handleVoiceTest = () => {
    const testMessages = [
      'こんにちは！Smart Roadsterのキオスクシステムなのだ！',
      'ずんだもんが音声でお知らせするのだ！',
      'VOICEVOX音声合成システムが動作中なのだ！',
      'WebSocketで音声データを送信しているのだ！'
    ];

    const randomMessage = testMessages[Math.floor(Math.random() * testMessages.length)];
    synthesizeVoice(randomMessage, 3); // 3 = ずんだもん
  };

  // ブラウザTTSテスト
  const handleBrowserTTSTest = () => {
    const testMessage = 'ブラウザの音声合成機能でテストしています。';
    speakWithBrowserTTS(testMessage);
  };

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">
          <h2>🚗 Car Assistant System - KIOSK</h2>
          <p>システムを起動中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* <header className="app-header">
        <h1>🚗 Car Assistant System - KIOSK</h1>
        <div className="current-time">{currentTime}</div>
      </header> */}

      <main className="app-main">
        <div className="left-panel">
          <div className="status-grid">
            {/* GPS情報 */}
            {/* <div className="status-card gps-card">
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
            </div> */}

            {/* 天気予報 */}
            {/*
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
            */}

            {/* 音声システム */}
            <div className="status-card voice-card">
              <h2>🗣️ ずんだもん音声システム</h2>
              <div>
                <p><strong>WebSocket接続:</strong> {connected ? '✅ 接続中' : '❌ 切断'}</p>
                <p><strong>VOICEVOX:</strong> {systemStatus?.voicevox_available ? '✅ 利用可能' : '❌ 利用不可'}</p>
                <p><strong>処理状態:</strong> {isProcessing ? '🔄 処理中' : '⏸️ 待機中'}</p>
                {systemStatus?.voice_status?.lastMessage && (
                  <p><strong>最後のメッセージ:</strong> {systemStatus.voice_status.lastMessage}</p>
                )}

                <div className="voice-controls">
                  <button
                    onClick={handleVoiceTest}
                    className="voice-test-btn"
                    disabled={isProcessing}
                  >
                    {isProcessing ? '音声合成中...' : 'VOICEVOX音声テスト'}
                  </button>

                  <button
                    onClick={handleBrowserTTSTest}
                    className="voice-test-btn browser-tts"
                    disabled={isProcessing}
                  >
                    ブラウザTTSテスト
                  </button>

                  {/* <button
                    onClick={getSpeakers}
                    className="voice-test-btn speakers-btn"
                  >
                    話者一覧取得
                  </button> */}
                </div>
              </div>
            </div>

            {/* システム情報 */}
            {/*
            <div className="status-card system-card">
              <h2>⚙️ システム情報</h2>
              <p><strong>フロントエンド:</strong> React + TypeScript</p>
              <p><strong>バックエンド:</strong> Flask API</p>
              <p><strong>配信:</strong> nginx</p>
              <p><strong>最終更新:</strong> {new Date().toLocaleString('ja-JP')}</p>
            </div>
            */}

            {/* ずんだもんURL表示カード */}
            <div className="status-card zundamon-url-card">
              <h2>🎭 ずんだもんURL</h2>
              {zundamonParams && zundamonUrl ? (
                <div>
                  <p><strong>URL:</strong></p>
                  <div className="url-display">{zundamonUrl}</div>
                  <p><strong>パラメータ:</strong></p>
                  <div className="params-display">
                    <p>頭の向き: {zundamonParams.head_direction}</p>
                    <p>右腕: {zundamonParams.right_arm}</p>
                    <p>左腕: {zundamonParams.left_arm}</p>
                    <p>枝豆: {zundamonParams.edamame}</p>
                    <p>顔色: {zundamonParams.face_color}</p>
                    <p>口: {zundamonParams.expression_mouth}</p>
                    <p>目: {zundamonParams.expression_eyes}</p>
                    <p>眉: {zundamonParams.expression_eyebrows}</p>
                  </div>
                </div>
              ) : (
                <p>ずんだもんを生成中...</p>
              )}
            </div>
          </div>
        </div>

        <div className="right-panel">
          {zundamonUrl ? (
            <img
              src={zundamonUrl}
              alt="ずんだもん"
              className="zundamon-image"
            />
          ) : (
            <div className="zundamon-loading">
              <p>ずんだもんを読み込み中...</p>
            </div>
          )}
        </div>
      </main>

      {/* <footer className="app-footer">
        <p>Car Assistant System - KIOSK System 🌧️🚗</p>
      </footer> */}
    </div>
  );
}

export default App;
