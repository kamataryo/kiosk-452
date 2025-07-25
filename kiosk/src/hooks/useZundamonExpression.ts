import { useMemo } from 'react';
import type { ZundamonExpression, RPMRange } from '../types/console';

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

export const useZundamonExpression = (rpm: number) => {
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

  return {
    expression,
    zundamonUrl,
    rpmRange: getRPMRange(rpm)
  };
};
