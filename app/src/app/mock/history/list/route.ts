import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/history/list
 * 获取穿搭历史列表
 */

// Mock 穿搭历史数据
const mockHistoryList = {
  histories: [
    {
      id: 1,
      occasion: "daily",
      created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      weather_temp: 24,
      weather_city: "上海",
      match_score: 0.92,
      clothes_count: 4,
      description: "清爽夏日风格",
    },
    {
      id: 2,
      occasion: "work",
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      weather_temp: 18,
      weather_city: "上海",
      match_score: 0.88,
      clothes_count: 5,
      description: "简约职业装",
    },
    {
      id: 3,
      occasion: "date",
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      weather_temp: 20,
      weather_city: "上海",
      match_score: 0.95,
      clothes_count: 4,
      description: "优雅约会风格",
    },
  ],
  total: 3,
  page: 1,
  page_size: 10,
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const user_id = searchParams.get("user_id");
  const page = searchParams.get("page");
  const page_size = searchParams.get("page_size");
  const start_date = searchParams.get("start_date");
  const end_date = searchParams.get("end_date");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json(mockHistoryList);
}
