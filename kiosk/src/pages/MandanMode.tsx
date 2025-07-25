import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

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

export const MandanMode = () => {
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
    // systemStatus,
    // isProcessing,
    isMandanProcessing,
    currentMandan,
    ollamaStatus,
    claudeStatus,
    // synthesizeVoice,
    // getSpeakers,
    generateMandan,
    getOllamaStatus,
    getClaudeStatus,
    // speakWithBrowserTTS
  } = useWebSocket();

  console.log(zundamonParams, currentTime, gpsData, weatherData, voiceStatus)
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
    // const interval = setInterval(updateZundamon, 3000);
    // return () => clearInterval(interval);
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

  // 漫談生成テスト（Ollama）
  const handleMandanTestOllama = () => {
    const topics = [
      '料理に関する小話',
      '最近の天気について',
      'ドライブの楽しさ',
      '季節の変わり目',
      '美味しい食べ物の話'
    ];

    const randomTopic = topics[Math.floor(Math.random() * topics.length)];
    generateMandan({
      topic: randomTopic,
      maxlength: 100,
      speaker: 3,
      model: 'mistral',
      provider: 'ollama'
    });
  };

  // 漫談生成テスト（Claude）
  const handleMandanTestClaude = () => {
    const topics = [
      '料理に関する小話',
      '最近の天気',
      '美味しい食べ物の話'
    ];

    const randomTopic = topics[Math.floor(Math.random() * topics.length)];
    generateMandan({
      topic: randomTopic,
      maxlength: 100,
      speaker: 3,
      provider: 'claude'
    });
  };

  // Ollama状態取得
  useEffect(() => {
    if (connected) {
      getOllamaStatus();
      getClaudeStatus();
    }
  }, [connected, getOllamaStatus, getClaudeStatus]);

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">
          <h2>🎭 ずんだもん漫談モード</h2>
          <p>システムを起動中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app mandan-mode">
      <header className="app-header">
        <h1>🎭 ずんだもん漫談モード</h1>
        <div className="current-time">{currentTime}</div>
      </header>

      <main className="app-main">
        <div className="left-panel">
          <div className="status-grid">
            {/* ずんだもん漫談システム */}
            <div className="status-card mandan-card">
              <h2>🎭 ずんだもん漫談システム</h2>
              <div>
                <p><strong>Ollama接続:</strong> {ollamaStatus?.available ? '✅ 接続中' : '❌ 切断'}</p>
                {ollamaStatus?.models && ollamaStatus.models.length > 0 && (
                  <p><strong>利用可能モデル:</strong> {ollamaStatus.models.join(', ')}</p>
                )}
                <p><strong>Claude API:</strong> {claudeStatus?.available ? '✅ 利用可能' : '❌ 利用不可'}</p>
                {claudeStatus && !claudeStatus.api_key_configured && (
                  <p><strong>Claude APIキー:</strong> ❌ 未設定</p>
                )}
                <p><strong>漫談生成状態:</strong> {isMandanProcessing ? '🔄 生成中' : '⏸️ 待機中'}</p>

                {currentMandan && (
                  <div className="current-mandan">
                    <p><strong>最新の漫談:</strong></p>
                    <div className="mandan-content">
                      <p><strong>トピック:</strong> {currentMandan.topic}</p>
                      <p><strong>内容:</strong> {currentMandan.sentence}</p>
                      <p><strong>生成時刻:</strong> {new Date(currentMandan.generatedAt).toLocaleString('ja-JP')}</p>
                    </div>
                  </div>
                )}

                <div className="mandan-controls">
                  <button
                    onClick={handleMandanTestOllama}
                    className="mandan-test-btn ollama-btn"
                    disabled={isMandanProcessing || !ollamaStatus?.available}
                  >
                    {isMandanProcessing ? '漫談生成中...' : 'ずんだもん漫談生成（Ollama）'}
                  </button>

                  <button
                    onClick={handleMandanTestClaude}
                    className="mandan-test-btn claude-btn"
                    disabled={isMandanProcessing || !claudeStatus?.available}
                  >
                    {isMandanProcessing ? '漫談生成中...' : 'ずんだもん漫談生成（Claude）'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="right-panel">
          {currentMandan && currentMandan.zundamonImageUrl ? (
            <img
              src={currentMandan.zundamonImageUrl}
              alt="ずんだもん（漫談中）"
              className="zundamon-image mandan-active"
            />
          ) : zundamonUrl ? (
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

          {currentMandan && (
            <div className="mandan-overlay">
              <div className="mandan-bubble">
                <p>{currentMandan.sentence}</p>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>ずんだもん漫談システム 🎭🗣️</p>
      </footer>
    </div>
  );
};
