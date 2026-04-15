import { NextResponse } from 'next/server';
import type { DIYOutfitRecord } from '@/types/diy';

const mockRecords: DIYOutfitRecord[] = [
  {
    id: '1',
    name: '春日休闲穿搭',
    slots: {
      top: ['top-1', 'top-2'],
      bottom: 'bottom-1',
      shoes: 'shoes-1',
    },
    accessories: [{ clothing_id: 'acc-1' }],
    generated_image_url: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=800&fit=crop',
    prompt: '右手提包，位于身体右侧',
    created_at: '2026-04-14T10:30:00Z',
  },
  {
    id: '2',
    name: '通勤穿搭',
    slots: {
      top: ['top-3'],
      bottom: 'bottom-2',
      shoes: 'shoes-2',
    },
    accessories: [{ clothing_id: 'acc-2' }],
    generated_image_url: 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=600&h=800&fit=crop',
    prompt: '银色手表佩戴在左手',
    created_at: '2026-04-13T14:20:00Z',
  },
  {
    id: '3',
    name: '约会搭配',
    slots: {
      top: ['top-4'],
      bottom: 'bottom-3',
      shoes: 'shoes-3',
    },
    accessories: [{ clothing_id: 'acc-3' }, { clothing_id: 'acc-4' }],
    generated_image_url: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=800&fit=crop',
    prompt: '太阳镜戴在头上，双肩包挂在背后',
    created_at: '2026-04-12T09:15:00Z',
  },
];

export async function GET() {
  return NextResponse.json({ records: mockRecords });
}
