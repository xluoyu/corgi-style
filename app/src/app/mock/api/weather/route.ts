import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/api/weather
 * 获取实时天气数据 (Mock)
 * Query params:
 * - location: 位置ID 或 经纬度坐标 (格式: "经度,纬度")
 */

// Mock 天气数据
const mockWeatherData = {
  temp: "22",
  feelsLike: "21",
  text: "多云",
  icon: "101",
  windDir: "东南风",
  windScale: "3级",
  humidity: "65",
  vis: "25",
  obsTime: new Date().toISOString(),
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const location = searchParams.get("location");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json({
    success: true,
    data: mockWeatherData,
    timestamp: new Date().toISOString(),
  });
}
