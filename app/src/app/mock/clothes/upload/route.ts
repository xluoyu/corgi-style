import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/clothes/upload
 * 上传衣物图片
 */
export async function POST(request: NextRequest) {
  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 800));

  return NextResponse.json({
    clothes_id: Date.now(),
    message: "图片上传成功",
    image_url: `https://picsum.photos/seed/${Date.now()}/400/600`,
  });
}
