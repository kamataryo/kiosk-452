import { useMemo, useRef, useEffect } from 'react';
import type { ZundamonExpression, RPMRange } from '../types/console';

interface SystemAlert {
  level: 'danger' | 'warning' | 'normal';
  message: string;
  type: 'temperature' | 'battery' | 'weather' | 'rpm';
}

const getRPMRange = (rpm: number): RPMRange => {
  if (rpm < 1500) return 'idle';
  if (rpm < 3000) return 'normal';
  if (rpm < 4500) return 'active';
  return 'high';
};

const getExpressionForRPM = (rpmRange: RPMRange): ZundamonExpression => {
  const expressions: Record<RPMRange, ZundamonExpression> = {
    idle: {
      head_direction: '正面向き',
      right_arm: '腰',
      left_arm: '腰',
      edamame: '通常',
      face_color: 'ほっぺ基本',
      expression_mouth: 'ほほえみ',
      expression_eyes: 'なごみ目',
      expression_eyebrows: '基本眉'
    },
    normal: {
      head_direction: '正面向き',
      right_arm: '基本',
      left_arm: '基本',
      edamame: '通常',
      face_color: 'ほっぺ基本',
      expression_mouth: 'えへ',
      expression_eyes: '基本目',
      expression_eyebrows: '基本眉'
    },
    active: {
      head_direction: '正面向き',
      right_arm: '手を挙げる',
      left_arm: '手を挙げる',
      edamame: '立ち',
      face_color: 'ほっぺ赤め',
      expression_mouth: 'あは',
      expression_eyes: 'にっこり',
      expression_eyebrows: '上がり眉'
    },
    high: {
      head_direction: '上向き',
      right_arm: '指差し上',
      left_arm: '手を挙げる',
      edamame: '立ち',
      face_color: '赤面',
      expression_mouth: 'お',
      expression_eyes: '〇〇',
      expression_eyebrows: '上がり眉'
    }
  };

  return expressions[rpmRange];
};

export const useZundamonExpression = (rpm: number, systemAlerts: SystemAlert[] = [], onMessageChange?: (message: string) => void) => {
  const expression = useMemo(() => {
    const rpmRange = getRPMRange(rpm);
    return getExpressionForRPM(rpmRange);
  }, [rpm]);

  const zundamonUrl = useMemo(() => {
    const queryParams = new URLSearchParams();
    Object.entries(expression).forEach(([key, value]) => {
      queryParams.append(key, value);
    });
    return `/api/zundamon/generate?${queryParams.toString()}`;
  }, [expression]);

  // メッセージを取得する関数
  const getMessage = useMemo(() => {
    // 最も重要な警告を取得（優先度: danger > warning > normal）
    const getHighestPriorityAlert = (): SystemAlert | null => {
      if (systemAlerts.length === 0) return null;

      const dangerAlerts = systemAlerts.filter(alert => alert.level === 'danger');
      if (dangerAlerts.length > 0) return dangerAlerts[0];

      const warningAlerts = systemAlerts.filter(alert => alert.level === 'warning');
      if (warningAlerts.length > 0) return warningAlerts[0];

      return systemAlerts[0];
    };

    const getRPMStatusText = () => {
      const rpmRange = getRPMRange(rpm);
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

    const alert = getHighestPriorityAlert();
    if (alert) {
      return alert.message;
    }
    return getRPMStatusText();
  }, [rpm, systemAlerts]);

  // 前回のメッセージを保持するref
  const previousMessageRef = useRef<string>('');

  // メッセージが変更されたときの処理
  useEffect(() => {
    if (getMessage !== previousMessageRef.current) {
      previousMessageRef.current = getMessage;
      if (onMessageChange && getMessage) {
        onMessageChange(getMessage);
      }
    }
  }, [getMessage, onMessageChange]);

  return {
    expression,
    zundamonUrl,
    rpmRange: getRPMRange(rpm),
    message: getMessage
  };
};
