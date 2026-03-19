import { NextRequest, NextResponse } from "next/server";
import { getWeatherNow } from "@/lib/weather";

/**
 * GET /api/weather
 * 获取实时天气数据
 * Query params:
 * - location: 位置ID 或 经纬度坐标 (格式: "经度,纬度")
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const location = searchParams.get("location");

  if (!location) {
    return NextResponse.json(
      { error: "Location parameter is required" },
      { status: 400 }
    );
  }

  const weatherData = await getWeatherNow(location);

  if (!weatherData) {
    return NextResponse.json(
      { error: "Failed to fetch weather data" },
      { status: 500 }
    );
  }

  return NextResponse.json({
    success: true,
    data: weatherData,
    timestamp: new Date().toISOString(),
  });
}
