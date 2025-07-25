import React from 'react';
import { useZundamonExpression } from '../hooks/useZundamonExpression';

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
  const { zundamonUrl, rpmRange } = useZundamonExpression(rpm);

  const getRPMStatusText = () => {
    switch (rpmRange) {
      case 'idle':
        return 'アイドリング中なのだ';
      case 'normal':
        return '通常走行中なのだ';
      case 'active':
        return '活発に走ってるのだ！';
      case 'high':
        return '高回転で興奮してるのだ！！';
      default:
        return '';
    }
  };

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

  const getDisplayMessage = () => {
    const alert = getHighestPriorityAlert();
    if (alert) {
      return alert.message;
    }
    return getRPMStatusText();
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
          <p>{getDisplayMessage()}</p>
          <div className="rpm-value">
            {rpm.toLocaleString()} RPM
          </div>
        </div>
      </div>
    </div>
  );
};
