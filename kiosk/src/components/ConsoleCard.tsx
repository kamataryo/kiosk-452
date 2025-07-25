import React from 'react';

interface ConsoleCardProps {
  title: string;
  icon: string;
  children: React.ReactNode;
  className?: string;
  alertLevel?: 'normal' | 'warning' | 'danger';
}

export const ConsoleCard: React.FC<ConsoleCardProps> = ({
  title,
  icon,
  children,
  className = '',
  alertLevel = 'normal'
}) => {
  const getAlertClass = () => {
    switch (alertLevel) {
      case 'warning':
        return 'console-card-warning';
      case 'danger':
        return 'console-card-danger';
      default:
        return '';
    }
  };

  return (
    <div className={`status-card console-card ${getAlertClass()} ${className}`}>
      <h2>
        {icon} {title}
      </h2>
      <div className="console-card-content">
        {children}
      </div>
    </div>
  );
};

interface DataRowProps {
  label: string;
  value: string | number;
  unit?: string;
  highlight?: boolean;
}

export const DataRow: React.FC<DataRowProps> = ({ label, value, unit, highlight = false }) => (
  <p className={highlight ? 'data-row-highlight' : ''}>
    <strong>{label}:</strong> {value}{unit && ` ${unit}`}
  </p>
);

interface GaugeProps {
  value: number;
  min: number;
  max: number;
  unit: string;
  label: string;
  warningThreshold?: number;
  dangerThreshold?: number;
}

export const Gauge: React.FC<GaugeProps> = ({
  value,
  min,
  max,
  unit,
  label,
  warningThreshold,
  dangerThreshold
}) => {
  const percentage = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);

  const getGaugeColor = () => {
    if (dangerThreshold && value >= dangerThreshold) return '#FF5722';
    if (warningThreshold && value >= warningThreshold) return '#FF9800';
    return '#4CAF50';
  };

  return (
    <div className="gauge-container">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <span className="gauge-value">{value} {unit}</span>
      </div>
      <div className="gauge-bar">
        <div
          className="gauge-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: getGaugeColor()
          }}
        />
      </div>
      <div className="gauge-range">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};
