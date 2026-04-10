import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/clothes/status/[id]
 * 获取衣物处理状态
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    clothes_id: id,
    analysis_completed: 1,
    generated_completed: 1,
    generated_image_url: `https://picsum.photos/seed/${id}/400/600`,
    color: "白色",
    category: "top",
    material: "纯棉",
    temperature_range: "summer",
    wear_method: "casual",
    scene: "daily",
  });
}
