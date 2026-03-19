import {
  QWeatherNowResponse,
  WeatherData,
  GeoLocationResponse,
  LocationData,
} from "@/types/weather";

const QWEATHER_API_KEY = process.env.QWEATHER_API_KEY;
const QWEATHER_API_HOST = process.env.QWEATHER_API_HOST || "https://devapi.qweather.com";

/**
 * 获取实时天气数据
 * @param location - 位置ID 或 经纬度坐标 (格式: "经度,纬度")
 * @returns 天气数据
 */
export async function getWeatherNow(location: string): Promise<WeatherData | null> {
  if (!QWEATHER_API_KEY) {
    console.error("QWEATHER_API_KEY is not configured");
    return null;
  }

  try {
    const url = `${QWEATHER_API_HOST}/v7/weather/now?location=${location}&lang=zh&key=${QWEATHER_API_KEY}`;
    console.log("Fetching weather from:", url.replace(QWEATHER_API_KEY!, "API_KEY_HIDDEN"));
    
    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Weather API response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: QWeatherNowResponse = await response.json();
    console.log("Weather API response code:", data.code);

    if (data.code !== "200") {
      console.error("QWeather API error:", data.code);
      return null;
    }

    return {
      temp: data.now.temp,
      feelsLike: data.now.feelsLike,
      text: data.now.text,
      icon: data.now.icon,
      windDir: data.now.windDir,
      windScale: data.now.windScale,
      humidity: data.now.humidity,
      vis: data.now.vis,
      obsTime: data.now.obsTime,
    };
  } catch (error) {
    console.error("Failed to fetch weather data:", error);
    return null;
  }
}

/**
 * 根据经纬度获取城市信息
 * @param longitude - 经度
 * @param latitude - 纬度
 * @returns 城市信息
 */
export async function getGeoLocation(
  longitude: number,
  latitude: number
): Promise<LocationData | null> {
  if (!QWEATHER_API_KEY) {
    console.error("QWEATHER_API_KEY is not configured");
    return null;
  }

  try {
    const location = `${longitude.toFixed(2)},${latitude.toFixed(2)}`;
    const url = `${QWEATHER_API_HOST}/geo/v2/city/lookup?location=${location}&lang=zh&key=${QWEATHER_API_KEY}`;
    console.log("Fetching geo location from:", url.replace(QWEATHER_API_KEY!, "API_KEY_HIDDEN"));
    
    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("GeoLocation API response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: GeoLocationResponse = await response.json();
    console.log("GeoLocation API response code:", data.code);

    if (data.code !== "200" || !data.location || data.location.length === 0) {
      console.error("GeoLocation API error:", data.code);
      return null;
    }

    const loc = data.location[0];
    return {
      latitude,
      longitude,
      city: loc.adm2 || loc.name,
      district: loc.name,
      province: loc.adm1,
    };
  } catch (error) {
    console.error("Failed to fetch geo location:", error);
    return null;
  }
}

/**
 * 根据城市名称搜索位置
 * @param cityName - 城市名称
 * @returns 位置信息列表
 */
export async function searchLocation(cityName: string): Promise<GeoLocationResponse["location"]> {
  if (!QWEATHER_API_KEY) {
    console.error("QWEATHER_API_KEY is not configured");
    return [];
  }

  try {
    const url = `${QWEATHER_API_HOST}/geo/v2/city/lookup?location=${encodeURIComponent(cityName)}&lang=zh&key=${QWEATHER_API_KEY}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: GeoLocationResponse = await response.json();

    if (data.code !== "200") {
      console.error("City lookup API error:", data.code);
      return [];
    }

    return data.location || [];
  } catch (error) {
    console.error("Failed to search location:", error);
    return [];
  }
}
