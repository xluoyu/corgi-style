/**
 * DIY 穿搭白板类型定义
 */

export interface SlotClothing {
  id: string;
  category: 'top' | 'bottom' | 'shoes' | 'accessory';
  imageUrl: string;
  name: string;
  color: string;
}

export interface AccessoryItem {
  id: string;
  clothing: SlotClothing;
  position?: { x: number; y: number };
}

export interface DIYOutfitState {
  slots: {
    top: SlotClothing[];
    bottom: SlotClothing | null;
    shoes: SlotClothing | null;
  };
  accessories: AccessoryItem[];
}

export interface DIYOutfitRecord {
  id: string;
  name: string;
  slots: {
    top: string[];
    bottom: string | null;
    shoes: string | null;
  };
  accessories: Array<{
    clothing_id: string;
    position: { x: number; y: number };
  }>;
  generated_image_url?: string;
  prompt?: string;
  created_at: string;
}

export type SlotType = 'top' | 'bottom' | 'shoes' | 'accessory';
