import { useEffect, useState, useCallback } from 'react';
import { io, type Socket } from 'socket.io-client';

interface VoiceStatus {
  isPlaying: boolean;
  lastMessage: string;
}

interface SystemStatus {
  connected: boolean;
  voice_status: VoiceStatus;
  voicevox_available: boolean;
  queue_size: number;
}

interface Speaker {
  name: string;
  speaker_uuid: string;
  styles: Array<{
    name: string;
    id: number;
  }>;
}

interface VoiceQueuedData {
  task_id: string;
  queue_position: number;
  text: string;
}

interface VoiceProcessingData {
  task_id: string;
  text: string;
}

interface VoiceReadyData {
  task_id: string;
  audio_data: string;
  format: string;
  text: string;
}

interface VoiceFallbackData {
  task_id: string;
  text: string;
  message: string;
}

interface VoiceErrorData {
  task_id: string;
  error: string;
  text?: string;
}

interface SpeakersListData {
  speakers: Speaker[];
  available: boolean;
  message?: string;
  error?: string;
}

interface VoiceStatusUpdateData {
  voice_status: VoiceStatus;
  voicevox_available: boolean;
  queue_size: number;
}

export const useWebSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Base64をBlobに変換するヘルパー関数
  const base64ToBlob = useCallback((base64: string, mimeType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }, []);

  // ブラウザTTSのフォールバック関数
  const speakWithBrowserTTS = useCallback((text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ja-JP';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      speechSynthesis.speak(utterance);
      console.log('ブラウザTTSで音声再生:', text);
    } else {
      console.warn('ブラウザがTTSをサポートしていません');
    }
  }, []);

  useEffect(() => {
    // WebSocket接続を初期化
    const newSocket = io('http://localhost:8000', {
      transports: ['websocket', 'polling']
    });

    // 接続イベント
    newSocket.on('connect', () => {
      setConnected(true);
      console.log('WebSocket接続成功');
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
      console.log('WebSocket切断');
    });

    // システム状態受信
    newSocket.on('status', (data: SystemStatus) => {
      setSystemStatus(data);
      console.log('システム状態受信:', data);
    });

    // 音声合成キュー追加通知
    newSocket.on('voice_queued', (data: VoiceQueuedData) => {
      console.log('音声合成キューに追加:', data);
      setIsProcessing(true);
    });

    // 音声合成処理中通知
    newSocket.on('voice_processing', (data: VoiceProcessingData) => {
      console.log('音声合成処理中:', data);
    });

    // 音声合成完了（VOICEVOX）
    newSocket.on('voice_ready', (data: VoiceReadyData) => {
      console.log('VOICEVOX音声合成完了:', data.text);
      try {
        // Base64音声データを再生
        const audioBlob = base64ToBlob(data.audio_data, 'audio/wav');
        const audio = new Audio(URL.createObjectURL(audioBlob));

        audio.onended = () => {
          setIsProcessing(false);
          URL.revokeObjectURL(audio.src); // メモリリークを防ぐ
        };

        audio.onerror = (error) => {
          console.error('音声再生エラー:', error);
          setIsProcessing(false);
          // フォールバックとしてブラウザTTSを使用
          speakWithBrowserTTS(data.text);
        };

        audio.play().catch((error) => {
          console.error('音声再生開始エラー:', error);
          setIsProcessing(false);
          // フォールバックとしてブラウザTTSを使用
          speakWithBrowserTTS(data.text);
        });
      } catch (error) {
        console.error('音声データ処理エラー:', error);
        setIsProcessing(false);
        // フォールバックとしてブラウザTTSを使用
        speakWithBrowserTTS(data.text);
      }
    });

    // VOICEVOX利用不可時のフォールバック
    newSocket.on('voice_fallback', (data: VoiceFallbackData) => {
      console.log('VOICEVOXフォールバック:', data.message);
      setIsProcessing(false);
      // ブラウザTTSを使用
      speakWithBrowserTTS(data.text);
    });

    // 音声合成エラー
    newSocket.on('voice_error', (data: VoiceErrorData) => {
      console.error('音声合成エラー:', data.error);
      setIsProcessing(false);
      // フォールバックとしてブラウザTTSを使用
      if (data.text) {
        speakWithBrowserTTS(data.text);
      }
    });

    // 話者一覧受信
    newSocket.on('speakers_list', (data: SpeakersListData) => {
      if (data.available && data.speakers) {
        setSpeakers(data.speakers);
        console.log('話者一覧受信:', data.speakers.length, '人');
      } else {
        console.log('VOICEVOX話者一覧取得失敗:', data.message || data.error);
      }
    });

    // 音声システム状態更新
    newSocket.on('voice_status_update', (data: VoiceStatusUpdateData) => {
      setSystemStatus(prev => prev ? { ...prev, ...data } : null);
    });

    setSocket(newSocket);

    // クリーンアップ
    return () => {
      newSocket.close();
    };
  }, [base64ToBlob, speakWithBrowserTTS]);

  // 音声合成リクエスト
  const synthesizeVoice = useCallback((text: string, speaker: number = 3) => {
    if (socket && connected && text.trim()) {
      socket.emit('voice_synthesize', {
        text: text.trim(),
        speaker,
        priority: 'normal'
      });
    } else {
      console.warn('WebSocket未接続または空のテキスト');
      // フォールバックとしてブラウザTTSを使用
      if (text.trim()) {
        speakWithBrowserTTS(text.trim());
      }
    }
  }, [socket, connected, speakWithBrowserTTS]);

  // 話者一覧取得
  const getSpeakers = useCallback(() => {
    if (socket && connected) {
      socket.emit('get_speakers');
    }
  }, [socket, connected]);

  // 音声システム状態取得
  const getVoiceStatus = useCallback(() => {
    if (socket && connected) {
      socket.emit('get_voice_status');
    }
  }, [socket, connected]);

  return {
    socket,
    connected,
    systemStatus,
    speakers,
    isProcessing,
    synthesizeVoice,
    getSpeakers,
    getVoiceStatus,
    speakWithBrowserTTS
  };
};
