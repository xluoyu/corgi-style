/**
 * AI 聊天类型定义
 */

// 流式事件类型
export type ChatEventType =
  | 'thinking'
  | 'tool_call'
  | 'tool_called'
  | 'tool_result'
  | 'text'
  | 'outfit_card'
  | 'suggestions'
  | 'done'
  | 'error';

// Tool 调用相关
export interface ToolCalledItem {
  tool: string;
  tool_name: string;
  args: Record<string, any>;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
}

export interface ToolResultItem {
  tool: string;
  tool_name: string;
  result: string;
  success: boolean;
  timestamp: number;
}

// 流式事件
export interface ChatStreamEvent {
  event: ChatEventType;
  content: any;
}

// SSE 事件类型
export type SSEEvent =
  | { event: 'thinking'; content: any }
  | { event: 'text'; content: string }
  | { event: 'outfit_card'; content: any }
  | { event: 'suggestions'; content: any }
  | { event: 'tool_called'; content: ToolCalledItem }
  | { event: 'tool_result'; content: ToolResultItem }
  | { event: 'done'; content: { session_id: string } }
  | { event: 'error'; content: { message: string } };

// 思考过程项
export interface ThinkingItem {
  node: string;
  node_name: string;
  text: string;
  timestamp: number;
  status?: 'pending' | 'success' | 'error';
}

// 穿搭方案
export interface OutfitPlan {
  plan_id: string;
  description: string;
  items: Record<string, {
    color: string;
    style: string;
    reason?: string;
    matched?: boolean;
    clothes_id?: string;
  }>;
  missing_advice?: string;
  color_harmony?: string;
  scene_appropriateness?: string;
  temperature_suitability?: string;
}

// 衣物项
export interface ClothesItem {
  id: string;
  category: string;
  color: string;
  description?: string;
  image_url?: string;
  style?: string;
  tags?: {
    colors?: string[];
    materials?: string[];
    styles?: string[];
    occasions?: string[];
    seasons?: string[];
    thickness?: string;
  };
  wear_count?: number;
  is_deleted?: boolean;
}

// 穿搭卡片
export interface OutfitCard {
  plan: OutfitPlan;
  clothes: Record<string, ClothesItem>;
  match_score: number;
  scene?: string;
  temperature?: number;
  city?: string;
}

// 建议项
export interface Suggestion {
  type: 'action' | 'text';
  text: string;
  action?: string;
}

// 聊天消息
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  outfitCard?: OutfitCard;
  suggestions?: Suggestion[];
  timestamp: string;
}

// 用户消息（带图片）
export interface UserMessageWithImage {
  text: string;
  imageUrl?: string;
}

// 聊天请求参数
export interface ChatStreamParams {
  user_id: string;
  session_id?: string;
  message: string;
  context?: Record<string, any>;
}
