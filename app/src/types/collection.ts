/**
 * 穿搭集类型定义
 */

import type { SlotClothing } from './diy';

/**
 * 穿搭集条目来源
 */
export type CollectionSource = 'url' | 'upload' | 'diy';

/**
 * AI 分析状态
 */
export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'failed';

/**
 * AI 识别的衣物
 */
export interface DetectedClothing {
  id: string;
  category: 'top' | 'bottom' | 'shoes' | 'accessory' | 'outer' | 'inner';
  name: string;
  color: string;
  position?: { x: number; y: number }; // 衣物在图片中的位置
  confidence?: number; // AI 识别置信度
  image_url?: string; // 裁剪出的单品图
}

/**
 * 代替衣物项
 */
export interface AlternativeItem {
  id: string;
  original_detected_id: string; // 对应哪件识别出的衣物
  wardrobe_clothing_id: string; // 衣柜中对应的衣物 ID
  wardrobe_clothing?: SlotClothing; // 衣柜衣物详情（懒加载）
  similarity_score?: number; // 相似度分数
  reason?: string; // 代替理由
}

/**
 * 穿搭集条目
 */
export interface OutfitCollectionItem {
  id: string;
  name: string; // 用户自定义名称/自动生成
  source: CollectionSource; // 来源标记
  source_url?: string; // 原始 URL（来源为 url 时）
  original_image_url: string; // 展示用图片
  thumbnail_url?: string; // 缩略图

  // AI 分析结果
  analysis_status: AnalysisStatus;
  detected_clothes: DetectedClothing[]; // AI 识别的衣物
  scene?: string; // 场景标签
  style?: string; // 风格标签

  // 代替模块
  alternatives: AlternativeItem[]; // 代替衣物列表

  // 来源于 DIY 时关联原始记录
  diy_record_id?: string;

  created_at: string;
  updated_at: string;
}

/**
 * 添加穿搭集条目的输入
 */
export interface AddCollectionInput {
  name?: string;
  source: CollectionSource;
  source_url?: string;
  image_url: string; // 必填，上传后的图片URL或原始URL
}

/**
 * 添加代替衣物的输入
 */
export interface AddAlternativeInput {
  original_detected_id: string;
  wardrobe_clothing_id: string;
}

/**
 * 场景/风格标签选项
 */
export const SCENE_OPTIONS = ['职场', '日常', '运动', '约会', '派对', '度假'] as const;
export type SceneType = (typeof SCENE_OPTIONS)[number];

export const STYLE_OPTIONS = ['休闲', '正式', '运动', '潮流', '复古', '文艺', '街头'] as const;
export type StyleType = (typeof STYLE_OPTIONS)[number];
