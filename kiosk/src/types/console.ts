export interface LocationData {
  latitude: number;
  longitude: number;
  address: string;
}

export interface WeatherData {
  temperature: number;
  condition: string;
  humidity: number;
  rainAlert: boolean;
}

export interface EngineData {
  rpm: number;
  temperature: number; // クーラント水温
}

export interface BatteryData {
  voltage: number;
  chargeLevel: number; // 0-100%
}

export interface ConsoleData {
  location: LocationData;
  weather: WeatherData;
  engine: EngineData;
  battery: BatteryData;
  timestamp: string;
}

export interface ZundamonExpression {
  head_direction: string;
  right_arm: string;
  left_arm: string;
  edamame: string;
  face_color: string;
  expression_mouth: string;
  expression_eyes: string;
  expression_eyebrows: string;
}

export type RPMRange = 'idle' | 'normal' | 'active' | 'high';
