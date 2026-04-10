import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/history/stats/summary
 * 获取穿搭统计摘要
 */

// Mock 穿搭统计数据
const mockStatsSummary = {
  total_count: 28,
  avg_match_score: 0.87,
  occasion_distribution: {
    daily: 15,
    work: 8,
    date: 3,
    party: 2,
  },
  period_days: 30,
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const user_id = searchParams.get("user_id");
  const days = searchParams.get("days");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json(mockStatsSummary);
}
