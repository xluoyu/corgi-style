/**
 * API 类型定义
 */

// ============ 用户相关 ============

export interface UserInfo {
  id: string;
  device_fingerprint: string;
  last_active_at: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  gender?: string;
  style_preferences: string[];
  season_preference: string[];
  default_occasion: string;
  created_at: string;
  updated_at: string;
}

export interface GetUserOrCreateRequest {
  device_fingerprint: string;
}

export interface UpdateUserInfoRequest {
  user_id: string;
  gender?: string;
  style_preferences?: string[];
  season_preference?: string[];
  default_occasion?: string;
}

// ============ 衣物相关 ============

export type ClothingCategory = "top" | "bottom" | "outerwear" | "inner" | "accessory";
export type TemperatureRange = "hot" | "warm" | "mild" | "cool" | "cold";
export type Scene = "daily" | "work" | "formal" | "sport" | "date" | "party";
export type WearMethod = "casual" | "formal" | "sport";

export interface ClothingItem {
  id: string;
  user_id: string;
  image_url: string;
  name?: string;
  category: string;
  color: string;
  material?: string;
  temperature_range?: string;
  wear_method?: string;
  scene?: string;
  generated_image_url?: string;
  analysis_completed: number;
  generated_completed: number;
  wear_count?: number;
  created_at: string;
}

export interface AddClothesRequest {
  user_id: string;
  image_url: string;
  category: ClothingCategory;
  color: string;
  temperature_range?: TemperatureRange;
  scene?: Scene;
  wear_method?: WearMethod;
  brand?: string;
  description?: string;
}

export interface AddClothesResponse {
  clothes_id: string;
  message: string;
}

export interface ClothesListResponse {
  clothes: ClothingItem[];
  total: number;
}
export interface DeleteClothesRequest {
  user_id: string;
  clothes_id: string;
}

export interface DeleteClothesResponse {
  message: string;
}

export interface UploadClothesResponse {
  clothes_id: string;
  message: string;
  image_url: string;
  generated_image_url?: string;
  color?: string;
  category?: ClothingCategory;
  material?: string;
  temperature_range?: TemperatureRange;
  wear_method?: WearMethod;
  scene?: Scene;
  completed_tasks: string[];
}

export interface ClothesStatusResponse {
  clothes_id: string;
  analysis_completed: number;
  generated_completed: number;
  generated_image_url?: string;
  color?: string;
  category?: ClothingCategory;
  material?: string;
  temperature_range?: TemperatureRange;
  wear_method?: WearMethod;
  scene?: Scene;
}

// ============ 穿搭相关 ============

export interface OutfitItem {
  slot: string;
  description: string;
  color: string;
}

export interface GenerateOutfitRequest {
  city: string;
  temperature: number;
  scene?: Scene;
}

export interface GenerateOutfitResponse {
  description: string;
  temperature: number;
  city: string;
  scene: Scene;
  image_url: string;
  outfit_items: OutfitItem[];
  cached: boolean;
}

export interface OutfitFeedbackRequest {
  user_id: string;
  outfit_id: string;
  feedback: "like" | "dislike" | "neutral";
}

export interface OutfitFeedbackResponse {
  message: string;
}

// ============ 穿搭历史相关 ============

export interface OutfitHistoryItem {
  id: number;
  occasion: string;
  created_at: string;
  weather_temp?: number;
  weather_city?: string;
  match_score: number;
  clothes_count: number;
  description?: string;
}

export interface OutfitHistoryDetail {
  id: number;
  occasion: string;
  created_at: string;
  weather_temp?: number;
  weather_city?: string;
  match_score: number;
  scheme_description?: string;
  clothes: {
    id: number;
    image_url: string;
    category: string;
    color: string;
  }[];
}

export interface OutfitHistoryListResponse {
  histories: OutfitHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface OutfitStatsSummary {
  total_count: number;
  avg_match_score: number;
  occasion_distribution: Record<string, number>;
  period_days: number;
}

export interface SaveOutfitSnapshotRequest {
  user_id: string;
  occasion: string;
  weather_temp?: number;
  weather_city?: string;
}

export interface SaveOutfitSnapshotResponse {
  message: string;
  history_id: number;
}

// ============ 通用类型 ============

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}
