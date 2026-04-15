import { NextResponse } from 'next/server';
import type { AlternativeItem, SlotClothing } from '@/types/collection';
import { mockWardrobeClothes } from '@/app/diy/mock';

// 模拟从衣柜筛选相似衣物的逻辑
function findSimilarClothes(detectedClothing: {
  category: string;
  color: string;
  name: string;
}): SlotClothing[] {
  // 从 mockWardrobeClothes 中查找同类别的衣物
  const sameCategory = mockWardrobeClothes.filter(
    (c) => c.category === detectedClothing.category
  );

  // 简单模拟：返回同类别的前3件衣物
  return sameCategory.slice(0, 3).map((c) => ({
    id: c.id,
    category: c.category,
    name: c.name,
    imageUrl: c.imageUrl,
    color: c.color,
  }));
}

/**
 * 获取代替推荐
 * GET /mock/collection/[id]/alternatives?clothing_id=xxx
 */
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const clothingId = searchParams.get('clothing_id');

  if (!clothingId) {
    return NextResponse.json({ error: 'Missing clothing_id parameter' }, { status: 400 });
  }

  // 模拟返回相似衣物
  // 真实场景中，这里会调用 AI 服务来匹配相似衣物
  const similarClothes = findSimilarClothes({
    category: 'top',
    color: '#FFFFFF',
    name: '白色衬衫',
  });

  const alternatives: AlternativeItem[] = similarClothes.map((c, index) => ({
    id: `alt-${id}-${clothingId}-${index}`,
    original_detected_id: clothingId,
    wardrobe_clothing_id: c.id,
    wardrobe_clothing: c,
    similarity_score: 0.85 + Math.random() * 0.1,
    reason: '与你衣柜中的衣物风格相似',
  }));

  return NextResponse.json({
    collection_id: id,
    clothing_id: clothingId,
    alternatives,
  });
}

/**
 * 添加代替衣物到列表
 * POST /mock/collection/[id]/alternatives
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const body = await request.json();
    const { original_detected_id, wardrobe_clothing_id } = body;

    if (!original_detected_id || !wardrobe_clothing_id) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // 查找衣柜衣物详情
    const wardrobeClothing = mockWardrobeClothes.find(
      (c) => c.id === wardrobe_clothing_id
    );

    const newAlternative: AlternativeItem = {
      id: `alt-${Date.now()}`,
      original_detected_id,
      wardrobe_clothing_id,
      wardrobe_clothing: wardrobeClothing,
      similarity_score: 0.9,
      reason: '与你衣柜中的衣物风格相似',
    };

    return NextResponse.json({ alternative: newAlternative }, { status: 201 });
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}
