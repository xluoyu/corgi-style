/**
 * 和风天气 API 响应类型定义
 */

export interface QWeatherNowResponse {
  code: string;
  updateTime: string;
  fxLink: string;
  now: {
    obsTime: string;
    temp: string;
    feelsLike: string;
    icon: string;
    text: string;
    wind360: string;
    windDir: string;
    windScale: string;
    windSpeed: string;
    humidity: string;
    precip: string;
    pressure: string;
    vis: string;
    cloud: string;
    dew: string;
  };
  refer: {
    sources: string[];
    license: string[];
  };
}

export interface WeatherData {
  temp: string;
  feelsLike: string;
  text: string;
  icon: string;
  windDir: string;
  windScale: string;
  humidity: string;
  vis: string;
  obsTime: string;
}

export interface GeoLocationResponse {
  code: string;
  location: Array<{
    name: string;
    id: string;
    lat: string;
    lon: string;
    adm2: string;
    adm1: string;
    country: string;
    tz: string;
    utcOffset: string;
    isDst: string;
    type: string;
    rank: string;
    fxLink: string;
  }>;
}

export interface LocationData {
  latitude: number;
  longitude: number;
  city: string;
  district: string;
  province: string;
}
