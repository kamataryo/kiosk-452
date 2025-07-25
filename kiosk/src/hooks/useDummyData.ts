import { useQuery } from '@tanstack/react-query';
import type { ConsoleData } from '../types/console';

// ダミーデータ生成関数
const generateDummyData = (): ConsoleData => {
  const addresses = [
    '東京都渋谷区神南1-1-1',
    '神奈川県横浜市中区本町1-1',
    '大阪府大阪市北区梅田1-1-1',
    '愛知県名古屋市中区栄1-1-1',
    '福岡県福岡市博多区博多駅前1-1-1'
  ];

  const conditions = ['晴れ', '曇り', '雨', '小雨', '快晴', '薄曇り'];

  return {
    location: {
      latitude: 35.6762 + (Math.random() - 0.5) * 0.1,
      longitude: 139.6503 + (Math.random() - 0.5) * 0.1,
      address: addresses[Math.floor(Math.random() * addresses.length)]
    },
    weather: {
      temperature: Math.floor(Math.random() * 20) + 10, // 10-30°C
      condition: conditions[Math.floor(Math.random() * conditions.length)],
      humidity: Math.floor(Math.random() * 40) + 40, // 40-80%
      rainAlert: Math.random() < 0.2 // 20%の確率で雨警報
    },
    engine: {
      rpm: Math.floor(Math.random() * 5200) + 800, // 800-6000 RPM
      temperature: Math.floor(Math.random() * 25) + 80 // 80-105°C
    },
    battery: {
      voltage: Math.round((Math.random() * 3 + 11.5) * 10) / 10, // 11.5-14.5V
      chargeLevel: Math.floor(Math.random() * 40) + 60 // 60-100%
    },
    timestamp: new Date().toISOString()
  };
};

export const useDummyData = () => {
  return useQuery({
    queryKey: ['consoleData'],
    queryFn: generateDummyData,
    refetchInterval: 3000, // 3秒ごとに更新
    refetchIntervalInBackground: true,
    staleTime: 0, // 常に新しいデータを取得
  });
};
