/**
 * DIY 页面 Mock 数据
 */

import type { SlotClothing } from '@/types/diy';

export const mockWardrobeClothes: SlotClothing[] = [
  // 上装
  {
    id: 'top-1',
    category: 'top',
    imageUrl: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=200&h=200&fit=crop',
    name: '白色圆领T恤',
    color: '#FFFFFF',
  },
  {
    id: 'top-2',
    category: 'top',
    imageUrl: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=200&h=200&fit=crop',
    name: '浅蓝色衬衫',
    color: '#89CFF0',
  },
  {
    id: 'top-3',
    category: 'top',
    imageUrl: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=200&h=200&fit=crop',
    name: '灰色连帽卫衣',
    color: '#808080',
  },
  {
    id: 'top-4',
    category: 'top',
    imageUrl: 'https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=200&h=200&fit=crop',
    name: '黑色针织衫',
    color: '#1A1A1A',
  },
  // 下装
  {
    id: 'bottom-1',
    category: 'bottom',
    imageUrl: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=200&h=200&fit=crop',
    name: '深蓝色牛仔裤',
    color: '#1E3A5F',
  },
  {
    id: 'bottom-2',
    category: 'bottom',
    imageUrl: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=200&h=200&fit=crop',
    name: '卡其色休闲裤',
    color: '#C3B091',
  },
  {
    id: 'bottom-3',
    category: 'bottom',
    imageUrl: 'https://images.unsplash.com/photo-1584370848010-d7fe6bc4ec9a?w=200&h=200&fit=crop',
    name: '黑色西装裤',
    color: '#2C2C2C',
  },
  // 鞋子
  {
    id: 'shoes-1',
    category: 'shoes',
    imageUrl: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=200&h=200&fit=crop',
    name: '白色运动鞋',
    color: '#FFFFFF',
  },
  {
    id: 'shoes-2',
    category: 'shoes',
    imageUrl: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=200&h=200&fit=crop',
    name: '棕色皮质乐福鞋',
    color: '#8B4513',
  },
  {
    id: 'shoes-3',
    category: 'shoes',
    imageUrl: 'https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=200&h=200&fit=crop',
    name: '黑色帆布鞋',
    color: '#1A1A1A',
  },
  // 配饰
  {
    id: 'acc-1',
    category: 'accessory',
    imageUrl: 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=200&h=200&fit=crop',
    name: '棕色手提包',
    color: '#8B4513',
  },
  {
    id: 'acc-2',
    category: 'accessory',
    imageUrl: 'https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=200&h=200&fit=crop',
    name: '银色手表',
    color: '#C0C0C0',
  },
  {
    id: 'acc-3',
    category: 'accessory',
    imageUrl: 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=200&h=200&fit=crop',
    name: '黑色太阳镜',
    color: '#1A1A1A',
  },
  {
    id: 'acc-4',
    category: 'accessory',
    imageUrl: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=200&h=200&fit=crop',
    name: '黑色双肩包',
    color: '#1A1A1A',
  },
];

export const categoryLabels: Record<string, string> = {
  all: '全部',
  top: '上装',
  bottom: '下装',
  shoes: '鞋子',
  accessory: '配饰',
};

export const slotLabels: Record<string, string> = {
  top: '上身',
  bottom: '下身',
  shoes: '鞋子',
  accessory: '配饰',
};
