import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/api/location
 * 获取地理位置信息 (Mock)
 * Query params:
 * - lat: 纬度
 * - lon: 经度
 * - city: 城市名称 (可选，用于搜索)
 */

// Mock 位置数据
const mockLocationData = {
  latitude: 31.23,
  longitude: 121.47,
  city: "上海",
  district: "浦东新区",
  province: "上海市",
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const city = searchParams.get("city");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    success: true,
    data: mockLocationData,
    timestamp: new Date().toISOString(),
  });
}
