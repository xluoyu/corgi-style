import { NextResponse } from 'next/server';
import type { OutfitCollectionItem, DetectedClothing } from '@/types/collection';

// 内存存储（Mock 数据）
let mockCollection: OutfitCollectionItem[] = [
  {
    id: '1',
    name: '韩系休闲穿搭',
    source: 'url',
    source_url: 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&h=800&fit=crop',
    original_image_url: 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&h=800&fit=crop',
    analysis_status: 'completed',
    detected_clothes: [
      { id: 'd1', category: 'top', name: '米色针织开衫', color: '#F5F5DC', confidence: 0.95 },
      { id: 'd2', category: 'bottom', name: '深蓝色牛仔裤', color: '#1E3A5F', confidence: 0.92 },
      { id: 'd3', category: 'shoes', name: '白色帆布鞋', color: '#FFFFFF', confidence: 0.88 },
      { id: 'd4', category: 'accessory', name: '棕色皮带', color: '#8B4513', confidence: 0.85 },
    ],
    scene: '日常',
    style: '休闲',
    alternatives: [],
    created_at: '2026-04-14T10:30:00Z',
    updated_at: '2026-04-14T10:30:00Z',
  },
  {
    id: '2',
    name: '职场优雅穿搭',
    source: 'upload',
    original_image_url: 'https://images.unsplash.com/photo-1485967121215-cba0b0ba4d8a?w=600&h=800&fit=crop',
    analysis_status: 'completed',
    detected_clothes: [
      { id: 'd5', category: 'top', name: '白色衬衫', color: '#FFFFFF', confidence: 0.98 },
      { id: 'd6', category: 'outer', name: '黑色西装外套', color: '#1A1A1A', confidence: 0.94 },
      { id: 'd7', category: 'bottom', name: '灰色西裤', color: '#808080', confidence: 0.91 },
      { id: 'd8', category: 'shoes', name: '黑色高跟鞋', color: '#1A1A1A', confidence: 0.89 },
    ],
    scene: '职场',
    style: '正式',
    alternatives: [],
    created_at: '2026-04-13T14:20:00Z',
    updated_at: '2026-04-13T14:20:00Z',
  },
  {
    id: '3',
    name: '春日约会搭配',
    source: 'diy',
    diy_record_id: '1',
    original_image_url: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=800&fit=crop',
    analysis_status: 'completed',
    detected_clothes: [
      { id: 'd9', category: 'top', name: '碎花连衣裙', color: '#FFC0CB', confidence: 0.96 },
      { id: 'd10', category: 'shoes', name: '裸色高跟鞋', color: '#E3BC9A', confidence: 0.87 },
    ],
    scene: '约会',
    style: '潮流',
    alternatives: [],
    created_at: '2026-04-12T09:15:00Z',
    updated_at: '2026-04-12T09:15:00Z',
  },
  {
    id: '4',
    name: '运动健身穿搭',
    source: 'url',
    source_url: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&h=800&fit=crop',
    original_image_url: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&h=800&fit=crop',
    analysis_status: 'analyzing',
    detected_clothes: [],
    scene: '运动',
    style: '运动',
    alternatives: [],
    created_at: '2026-04-11T16:45:00Z',
    updated_at: '2026-04-11T16:45:00Z',
  },
];

/**
 * 获取穿搭集列表
 */
export async function GET() {
  return NextResponse.json({ items: mockCollection });
}

/**
 * 添加穿搭条目
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, source, source_url, image_url } = body;

    const newItem: OutfitCollectionItem = {
      id: String(Date.now()),
      name: name || `穿搭 ${mockCollection.length + 1}`,
      source,
      source_url,
      original_image_url: image_url,
      analysis_status: 'pending',
      detected_clothes: [],
      alternatives: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockCollection.unshift(newItem);

    return NextResponse.json({ item: newItem }, { status: 201 });
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}

/**
 * 更新穿搭条目
 */
export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { id, ...updates } = body;

    const index = mockCollection.findIndex((item) => item.id === id);
    if (index === -1) {
      return NextResponse.json({ error: 'Item not found' }, { status: 404 });
    }

    mockCollection[index] = {
      ...mockCollection[index],
      ...updates,
      updated_at: new Date().toISOString(),
    };

    return NextResponse.json({ item: mockCollection[index] });
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}

/**
 * 删除穿搭条目
 */
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({ error: 'Missing id parameter' }, { status: 400 });
    }

    const index = mockCollection.findIndex((item) => item.id === id);
    if (index === -1) {
      return NextResponse.json({ error: 'Item not found' }, { status: 404 });
    }

    mockCollection.splice(index, 1);

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
