/**
 * API 客户端 - 统一导出
 * 保持向后兼容，从子模块重新导出所有 API
 */

// 配置
export { USE_MOCK, getBaseUrl, getMockPrefix, generateDeviceFingerprint, getDeviceFingerprint, getUserId } from "./config";
export { request, uploadRequest } from "./request";

// 用户 API
export { getUserOrCreate, updateUserInfo, getUserPreference, getUserProfile } from "./user";

// 衣物 API
export { addClothes, getClothesList, deleteClothes, uploadClothesImage, getClothesStatus, pollClothesStatus } from "./clothes";

// 穿搭 API
export { generateTodayOutfit, refreshOutfit, submitOutfitFeedback } from "./outfit";

// 穿搭历史 API
export { getOutfitHistory, getOutfitHistoryDetail, saveOutfitSnapshot, getOutfitStatsSummary } from "./history";

// 聊天 API
export { chatMessageStream, chatMessage, chatMessageStreamV3, chatMessageV3 } from "./chat";
