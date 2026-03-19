import { NextRequest, NextResponse } from "next/server";
import { getGeoLocation, searchLocation } from "@/lib/weather";
import { LocationData } from "@/types/weather";

/**
 * 使用 Nominatim (OpenStreetMap) 进行反向地理编码作为备用方案
 * @param latitude - 纬度
 * @param longitude - 经度
 * @returns 城市信息
 */
async function reverseGeocode(latitude: number, longitude: number): Promise<LocationData | null> {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&accept-language=zh`;
    
    const response = await fetch(url, {
      headers: {
        "User-Agent": "CorgiStyleApp/1.0",
      },
    });

    if (!response.ok) {
      console.error("Nominatim API error:", response.status);
      return null;
    }

    const data = await response.json();
    const address = data.address || {};

    return {
      latitude,
      longitude,
      city: address.city || address.town || address.county || address.state || "未知城市",
      district: address.district || address.suburb || address.town || "",
      province: address.province || address.state || "",
    };
  } catch (error) {
    console.error("Failed to reverse geocode:", error);
    return null;
  }
}

/**
 * GET /api/location
 * 获取地理位置信息
 * Query params:
 * - lat: 纬度
 * - lon: 经度
 * - city: 城市名称 (可选，用于搜索)
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const city = searchParams.get("city");

  if (city) {
    const locations = await searchLocation(city);
    return NextResponse.json({
      success: true,
      data: locations,
      timestamp: new Date().toISOString(),
    });
  }

  if (!lat || !lon) {
    return NextResponse.json(
      { error: "Latitude and longitude parameters are required" },
      { status: 400 }
    );
  }

  const latitude = parseFloat(lat);
  const longitude = parseFloat(lon);

  if (isNaN(latitude) || isNaN(longitude)) {
    return NextResponse.json(
      { error: "Invalid latitude or longitude" },
      { status: 400 }
    );
  }

  let locationData = await getGeoLocation(longitude, latitude);

  if (!locationData) {
    console.log("GeoAPI failed, using Nominatim as fallback");
    locationData = await reverseGeocode(latitude, longitude);
  }

  if (!locationData) {
    return NextResponse.json(
      { error: "Failed to fetch location data" },
      { status: 500 }
    );
  }

  return NextResponse.json({
    success: true,
    data: locationData,
    timestamp: new Date().toISOString(),
  });
}
