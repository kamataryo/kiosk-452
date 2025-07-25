import React, { useCallback } from 'react';
import { useZundamonExpression } from '../hooks/useZundamonExpression';
import { useWebSocket } from '../hooks/useWebSocket';

interface SystemAlert {
  level: 'danger' | 'warning' | 'normal';
  message: string;
  type: 'temperature' | 'battery' | 'weather' | 'rpm';
}

interface ZundamonDisplayProps {
  rpm: number;
  systemAlerts?: SystemAlert[];
  className?: string;
}

export const ZundamonDisplay: React.FC<ZundamonDisplayProps> = ({
  rpm,
  systemAlerts = [],
  className = ''
}) => {
  const { synthesizeVoice } = useWebSocket();

  // メッセージが変更されたときの音声再生コールバック
  const handleMessageChange = useCallback((message: string) => {
    if (message && message.trim()) {
      // cache: use オプションを使用してキャッシュ機能を活用
      synthesizeVoice(message, 3, 'use'); // speaker 3 = ずんだもん, cache = use
    }
  }, [synthesizeVoice]);

  const { zundamonUrl, rpmRange, message } = useZundamonExpression(rpm, systemAlerts, handleMessageChange);

  const getRPMStatusClass = () => {
    switch (rpmRange) {
      case 'idle':
        return 'rpm-status-idle';
      case 'normal':
        return 'rpm-status-normal';
      case 'active':
        return 'rpm-status-active';
      case 'high':
        return 'rpm-status-high';
      default:
        return '';
    }
  };

  // 最も重要な警告を取得（優先度: danger > warning > normal）
  const getHighestPriorityAlert = (): SystemAlert | null => {
    if (systemAlerts.length === 0) return null;

    const dangerAlerts = systemAlerts.filter(alert => alert.level === 'danger');
    if (dangerAlerts.length > 0) return dangerAlerts[0];

    const warningAlerts = systemAlerts.filter(alert => alert.level === 'warning');
    if (warningAlerts.length > 0) return warningAlerts[0];

    return systemAlerts[0];
  };

  const getDisplayClass = () => {
    const alert = getHighestPriorityAlert();
    if (alert) {
      switch (alert.level) {
        case 'danger':
          return 'rpm-status-danger';
        case 'warning':
          return 'rpm-status-warning';
        default:
          return getRPMStatusClass();
      }
    }
    return getRPMStatusClass();
  };

  return (
    <div className={`zundamon-display ${className}`}>
      <div className="zundamon-container">
        {zundamonUrl ? (
          <img
            src={zundamonUrl}
            alt="ずんだもん"
            className="zundamon-image console-mode"
          />
        ) : (
          <div className="zundamon-loading">
            <p>ずんだもんを読み込み中...</p>
          </div>
        )}
      </div>

      <div className={`rpm-status ${getDisplayClass()}`}>
        <div className="rpm-bubble">
          <p>{message}</p>
          <div className="rpm-value">
            {rpm.toLocaleString()} RPM
          </div>
        </div>
      </div>
    </div>
  );
};
