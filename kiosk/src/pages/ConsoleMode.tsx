import React, { useState, useEffect } from 'react';
import { useDummyData } from '../hooks/useDummyData';
import { ConsoleCard, DataRow, Gauge } from '../components/ConsoleCard';
import { ZundamonDisplay } from '../components/ZundamonDisplay';

interface SystemAlert {
  level: 'danger' | 'warning' | 'normal';
  message: string;
  type: 'temperature' | 'battery' | 'weather' | 'rpm';
}

export const ConsoleMode: React.FC = () => {
  const { data: consoleData, isLoading, error } = useDummyData();
  const [currentTime, setCurrentTime] = useState<string>('');

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

  if (isLoading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">
          <h2>🚗 Smart Roadster Console</h2>
          <p>システムを起動中...</p>
        </div>
      </div>
    );
  }

  if (error || !consoleData) {
    return (
      <div className="app loading">
        <div className="loading-spinner">
          <h2>❌ システムエラー</h2>
          <p>データの取得に失敗しました</p>
        </div>
      </div>
    );
  }

  const getTemperatureAlert = (temp: number) => {
    if (temp >= 100) return 'danger';
    if (temp >= 95) return 'warning';
    return 'normal';
  };

  const getBatteryAlert = (voltage: number) => {
    if (voltage < 12.0) return 'danger';
    if (voltage < 12.5) return 'warning';
    return 'normal';
  };

  // システム警告を生成
  const generateSystemAlerts = (): SystemAlert[] => {
    const alerts: SystemAlert[] = [];

    // 水温警告
    if (consoleData.engine.temperature >= 100) {
      alerts.push({
        level: 'danger',
        message: '水温が危険レベルなのだ！すぐに停車するのだ！',
        type: 'temperature'
      });
    } else if (consoleData.engine.temperature >= 95) {
      alerts.push({
        level: 'warning',
        message: '水温が高めなのだ。注意が必要なのだ。',
        type: 'temperature'
      });
    }

    // バッテリー警告
    if (consoleData.battery.voltage < 12.0) {
      alerts.push({
        level: 'danger',
        message: 'バッテリーが危険なのだ！交換が必要なのだ！',
        type: 'battery'
      });
    } else if (consoleData.battery.voltage < 12.5) {
      alerts.push({
        level: 'warning',
        message: 'バッテリーが弱ってるのだ。要注意なのだ。',
        type: 'battery'
      });
    }

    // 雨警報
    if (consoleData.weather.rainAlert) {
      alerts.push({
        level: 'warning',
        message: '雨が近づいてるのだ！屋根を閉めるのだ！',
        type: 'weather'
      });
    }

    return alerts;
  };

  const systemAlerts = generateSystemAlerts();

  return (
    <div className="app console-mode">
      <header className="app-header">
        <h1>🚗 Smart Roadster Console</h1>
        <div className="current-time">
          {currentTime}
        </div>
      </header>

      <main className="app-main">
        <div className="left-panel">
          <div className="status-grid">
            {/* 位置情報および天気予報 */}
            <ConsoleCard
              title="位置情報・天気予報"
              icon="🌍"
            >
              <div className="location-weather-grid">
                <div className="location-section">
                  <h3>📍 現在位置</h3>
                  <DataRow
                    label="緯度"
                    value={consoleData.location.latitude.toFixed(6)}
                  />
                  <DataRow
                    label="経度"
                    value={consoleData.location.longitude.toFixed(6)}
                  />
                  <DataRow
                    label="住所"
                    value={consoleData.location.address}
                  />
                </div>
                <div className="weather-section">
                  <h3>🌤️ 天気情報</h3>
                  <DataRow
                    label="気温"
                    value={consoleData.weather.temperature}
                    unit="°C"
                  />
                  <DataRow
                    label="天候"
                    value={consoleData.weather.condition}
                  />
                  <DataRow
                    label="湿度"
                    value={consoleData.weather.humidity}
                    unit="%"
                  />
                </div>
              </div>
            </ConsoleCard>

            {/* クーラント水温 */}
            <ConsoleCard
              title="クーラント水温"
              icon="🌡️"
              alertLevel={getTemperatureAlert(consoleData.engine.temperature)}
            >
              <Gauge
                value={consoleData.engine.temperature}
                min={60}
                max={120}
                unit="°C"
                label="水温"
                warningThreshold={95}
                dangerThreshold={100}
              />
              <DataRow
                label="現在温度"
                value={consoleData.engine.temperature}
                unit="°C"
                highlight={consoleData.engine.temperature >= 95}
              />
              <DataRow
                label="状態"
                value={
                  consoleData.engine.temperature >= 100 ? '危険' :
                  consoleData.engine.temperature >= 95 ? '警告' : '正常'
                }
              />
            </ConsoleCard>

            {/* エンジン回転数 */}
            <ConsoleCard
              title="エンジン回転数"
              icon="⚙️"
            >
              <Gauge
                value={consoleData.engine.rpm}
                min={0}
                max={7000}
                unit="RPM"
                label="回転数"
                warningThreshold={5000}
                dangerThreshold={6000}
              />
              <DataRow
                label="現在回転数"
                value={consoleData.engine.rpm.toLocaleString()}
                unit="RPM"
              />
              <DataRow
                label="エンジン状態"
                value={
                  consoleData.engine.rpm < 1500 ? 'アイドリング' :
                  consoleData.engine.rpm < 3000 ? '通常走行' :
                  consoleData.engine.rpm < 4500 ? '活発走行' : '高回転'
                }
              />
            </ConsoleCard>

            {/* バッテリー電圧 */}
            <ConsoleCard
              title="バッテリー電圧"
              icon="🔋"
              alertLevel={getBatteryAlert(consoleData.battery.voltage)}
            >
              <Gauge
                value={consoleData.battery.voltage}
                min={10}
                max={15}
                unit="V"
                label="電圧"
                warningThreshold={12.5}
                dangerThreshold={12.0}
              />
              <DataRow
                label="現在電圧"
                value={consoleData.battery.voltage}
                unit="V"
                highlight={consoleData.battery.voltage < 12.5}
              />
              <DataRow
                label="充電レベル"
                value={consoleData.battery.chargeLevel}
                unit="%"
              />
              <DataRow
                label="バッテリー状態"
                value={
                  consoleData.battery.voltage < 12.0 ? '要交換' :
                  consoleData.battery.voltage < 12.5 ? '要注意' : '良好'
                }
              />
            </ConsoleCard>
          </div>
        </div>

        <div className="right-panel">
          <ZundamonDisplay rpm={consoleData.engine.rpm} systemAlerts={systemAlerts} />
        </div>
      </main>

      <footer className="app-footer">
        <p>Smart Roadster Console System 🚗⚙️</p>
      </footer>
    </div>
  );
};
