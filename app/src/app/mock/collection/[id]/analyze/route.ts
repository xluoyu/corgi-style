import { NextResponse } from 'next/server';
import type { DetectedClothing } from '@/types/collection';

// Mock AI 分析结果
const mockAnalysisResults: Record<string, DetectedClothing[]> = {
  default: [
    { id: `detected-${Date.now()}-1`, category: 'top', name: '白色棉质T恤', color: '#FFFFFF', confidence: 0.94 },
    { id: `detected-${Date.now()}-2`, category: 'bottom', name: '深色休闲裤', color: '#2F4F4F', confidence: 0.89 },
    { id: `detected-${Date.now()}-3`, category: 'shoes', name: '白色运动鞋', color: '#FFFFFF', confidence: 0.85 },
  ],
};

/**
 * 触发 AI 分析
 * POST /mock/collection/[id]/analyze
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // 模拟异步分析任务
  // 真实场景中，这里会调用后端 AI 服务

  return NextResponse.json({
    status: 'started',
    message: 'AI 分析任务已启动',
    collection_id: id,
  });
}

/**
 * 获取分析状态和结果
 * GET /mock/collection/[id]/analyze
 */
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const force = searchParams.get('force') === 'true';

  // 模拟返回分析结果
  // 真实场景中，这里会返回实际的 AI 分析结果

  const results = mockAnalysisResults.default;

  return NextResponse.json({
    collection_id: id,
    status: 'completed',
    results,
  });
}
