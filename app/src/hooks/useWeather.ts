"use client";

import { useState, useEffect, useCallback } from "react";
import { WeatherData, LocationData } from "@/types/weather";

interface UseWeatherResult {
  weather: WeatherData | null;
  location: LocationData | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

interface WeatherApiResponse {
  success: boolean;
  data: WeatherData;
  timestamp: string;
}

interface LocationApiResponse {
  success: boolean;
  data: LocationData;
  timestamp: string;
}

interface CachedWeatherData {
  weather: WeatherData;
  location: LocationData;
  timestamp: number;
  coords: {
    lat: number;
    lon: number;
  };
}

const CACHE_KEY = "corgi_weather_cache";
const CACHE_DURATION = 30 * 60 * 1000;

/**
 * 从 sessionStorage 获取缓存的天气数据
 * @returns 缓存数据或 null
 */
function getCachedWeather(): CachedWeatherData | null {
  if (typeof window === "undefined") return null;

  try {
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const data: CachedWeatherData = JSON.parse(cached);
    const now = Date.now();

    if (now - data.timestamp > CACHE_DURATION) {
      sessionStorage.removeItem(CACHE_KEY);
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

/**
 * 将天气数据缓存到 sessionStorage
 * @param weather - 天气数据
 * @param location - 位置数据
 * @param lat - 纬度
 * @param lon - 经度
 */
function setCachedWeather(
  weather: WeatherData,
  location: LocationData,
  lat: number,
  lon: number
): void {
  if (typeof window === "undefined") return;

  try {
    const cacheData: CachedWeatherData = {
      weather,
      location,
      timestamp: Date.now(),
      coords: { lat, lon },
    };
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
  } catch {
    console.error("Failed to cache weather data");
  }
}

/**
 * useWeather - 天气数据获取 Hook
 * 自动获取用户地理位置并获取实时天气数据
 * 支持 sessionStorage 缓存，优先从缓存获取数据
 */
export function useWeather(): UseWeatherResult {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [location, setLocation] = useState<LocationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherData = useCallback(async (lat: number, lon: number) => {
    try {
      const locationParam = `${lon.toFixed(2)},${lat.toFixed(2)}`;
      const [weatherRes, locationRes] = await Promise.all([
        fetch(`/api/weather?location=${locationParam}`),
        fetch(`/api/location?lat=${lat}&lon=${lon}`),
      ]);

      if (!weatherRes.ok || !locationRes.ok) {
        throw new Error("Failed to fetch weather or location data");
      }

      const weatherData: WeatherApiResponse = await weatherRes.json();
      const locationData: LocationApiResponse = await locationRes.json();

      if (weatherData.success && locationData.success) {
        setWeather(weatherData.data);
        setLocation(locationData.data);
        setError(null);

        setCachedWeather(weatherData.data, locationData.data, lat, lon);
      } else {
        throw new Error("API returned unsuccessful response");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  }, []);

  const getLocationAndWeather = useCallback(async () => {
    setLoading(true);
    setError(null);

    const cached = getCachedWeather();
    if (cached) {
      setWeather(cached.weather);
      setLocation(cached.location);
      setLoading(false);
      return;
    }

    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        await fetchWeatherData(latitude, longitude);
      },
      (err) => {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError("用户拒绝了地理位置请求");
            break;
          case err.POSITION_UNAVAILABLE:
            setError("位置信息不可用");
            break;
          case err.TIMEOUT:
            setError("获取位置超时");
            break;
          default:
            setError("获取位置时发生未知错误");
        }
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      }
    );
  }, [fetchWeatherData]);

  const refetch = useCallback(() => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(CACHE_KEY);
    }
    getLocationAndWeather();
  }, [getLocationAndWeather]);

  useEffect(() => {
    getLocationAndWeather();
  }, [getLocationAndWeather]);

  return { weather, location, loading, error, refetch };
}

/**
 * getWeatherIcon - 根据天气图标代码获取对应的图标名称
 * @param iconCode - 和风天气图标代码
 * @returns 图标名称
 */
export function getWeatherIconName(iconCode: string): string {
  const iconMap: Record<string, string> = {
    "100": "Sun",
    "101": "Cloud",
    "102": "Cloud",
    "103": "Cloud",
    "104": "Cloud",
    "150": "Sun",
    "151": "Cloud",
    "300": "CloudRain",
    "301": "CloudRain",
    "302": "CloudLightning",
    "303": "CloudLightning",
    "304": "CloudLightning",
    "305": "CloudRain",
    "306": "CloudRain",
    "307": "CloudRain",
    "308": "CloudRain",
    "309": "CloudRain",
    "310": "CloudRain",
    "311": "CloudRain",
    "312": "CloudRain",
    "313": "CloudRain",
    "314": "CloudRain",
    "315": "CloudRain",
    "316": "CloudRain",
    "317": "CloudRain",
    "318": "CloudRain",
    "350": "CloudRain",
    "351": "CloudRain",
    "399": "CloudRain",
    "400": "CloudSnow",
    "401": "CloudSnow",
    "402": "CloudSnow",
    "403": "CloudSnow",
    "404": "CloudSnow",
    "405": "CloudSnow",
    "406": "CloudSnow",
    "407": "CloudSnow",
    "408": "CloudSnow",
    "409": "CloudSnow",
    "410": "CloudSnow",
    "456": "CloudSnow",
    "457": "CloudSnow",
    "499": "CloudSnow",
    "500": "CloudFog",
    "501": "CloudFog",
    "502": "CloudFog",
    "503": "CloudFog",
    "504": "CloudFog",
    "507": "Wind",
    "508": "Wind",
    "509": "Wind",
    "510": "Wind",
    "511": "Wind",
    "512": "Wind",
    "513": "Wind",
    "514": "Wind",
    "515": "Wind",
    "800": "Sun",
    "801": "Sun",
    "802": "Sun",
    "803": "Sun",
    "804": "Sun",
    "805": "Sun",
    "806": "Sun",
    "807": "Sun",
    "900": "Thermometer",
    "901": "Thermometer",
    "999": "HelpCircle",
  };

  return iconMap[iconCode] || "Sun";
}
