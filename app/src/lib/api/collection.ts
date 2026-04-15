/**
 * 穿搭集 API
 */

import type {
  OutfitCollectionItem,
  AddCollectionInput,
  AddAlternativeInput,
  AlternativeItem,
  DetectedClothing,
} from '@/types/collection';
import { request, uploadRequest } from './request';
import { getUserId } from './config';

/**
 * 获取穿搭集列表
 */
export async function getCollectionItems(): Promise<OutfitCollectionItem[]> {
  const response = await request<{ items: OutfitCollectionItem[] }>('/mock/collection');
  return response.items;
}

/**
 * 获取单条穿搭详情
 */
export async function getCollectionItem(id: string): Promise<OutfitCollectionItem | null> {
  const items = await getCollectionItems();
  return items.find((item) => item.id === id) || null;
}

/**
 * 添加穿搭条目
 */
export async function addCollectionItem(
  data: AddCollectionInput
): Promise<OutfitCollectionItem> {
  const response = await request<{ item: OutfitCollectionItem }>('/mock/collection', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.item;
}

/**
 * 通过 URL 添加穿搭条目
 */
export async function addCollectionByUrl(
  imageUrl: string,
  name?: string
): Promise<OutfitCollectionItem> {
  return addCollectionItem({
    name,
    source: 'url',
    source_url: imageUrl,
    image_url: imageUrl,
  });
}

/**
 * 通过本地上传添加穿搭条目
 */
export async function addCollectionByUpload(
  file: File,
  name?: string
): Promise<OutfitCollectionItem> {
  const formData = new FormData();
  formData.append('file', file);

  // 上传图片到 OSS
  const uploadResult = await uploadRequest<{ image_url: string }>(
    '/clothes/upload',
    formData
  );

  return addCollectionItem({
    name,
    source: 'upload',
    image_url: uploadResult.image_url,
  });
}

/**
 * 更新穿搭条目
 */
export async function updateCollectionItem(
  id: string,
  data: Partial<OutfitCollectionItem>
): Promise<OutfitCollectionItem> {
  const response = await request<{ item: OutfitCollectionItem }>('/mock/collection', {
    method: 'PUT',
    body: JSON.stringify({ id, ...data }),
  });
  return response.item;
}

/**
 * 删除穿搭条目
 */
export async function deleteCollectionItem(id: string): Promise<void> {
  await request('/mock/collection', {
    method: 'DELETE',
  });
}

/**
 * 触发 AI 分析
 */
export async function triggerAnalyze(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/mock/collection/${id}/analyze`, {
    method: 'POST',
  });
}

/**
 * 获取 AI 分析结果
 */
export async function getAnalysisResult(
  id: string,
  force = false
): Promise<{ status: string; results: DetectedClothing[] }> {
  const params = force ? '?force=true' : '';
  return request<{ status: string; results: DetectedClothing[] }>(
    `/mock/collection/${id}/analyze${params}`
  );
}

/**
 * 获取代替推荐
 */
export async function getAlternatives(
  collectionId: string,
  clothingId: string
): Promise<AlternativeItem[]> {
  const response = await request<{
    collection_id: string;
    clothing_id: string;
    alternatives: AlternativeItem[];
  }>(`/mock/collection/${collectionId}/alternatives?clothing_id=${clothingId}`);

  return response.alternatives;
}

/**
 * 添加代替衣物
 */
export async function addAlternative(
  collectionId: string,
  data: AddAlternativeInput
): Promise<AlternativeItem> {
  const response = await request<{ alternative: AlternativeItem }>(
    `/mock/collection/${collectionId}/alternatives`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );
  return response.alternative;
}

/**
 * 从 DIY 记录导入到穿搭集
 */
export async function importFromDIY(
  diyRecord: OutfitCollectionItem
): Promise<OutfitCollectionItem> {
  const { mockWardrobeClothes } = await import('@/app/diy/mock');

  // 将 DIY 记录转换为穿搭集条目
  const detectedClothes: DetectedClothing[] = [];

  // 处理上衣
  diyRecord.slots.top.forEach((id) => {
    const clothing = mockWardrobeClothes.find((c) => c.id === id);
    if (clothing) {
      detectedClothes.push({
        id: `detected-${Date.now()}-${id}`,
        category: clothing.category,
        name: clothing.name,
        color: clothing.color,
      });
    }
  });

  // 处理下装
  if (diyRecord.slots.bottom) {
    const clothing = mockWardrobeClothes.find((c) => c.id === diyRecord.slots.bottom);
    if (clothing) {
      detectedClothes.push({
        id: `detected-${Date.now()}-${diyRecord.slots.bottom}`,
        category: clothing.category,
        name: clothing.name,
        color: clothing.color,
      });
    }
  }

  // 处理鞋子
  if (diyRecord.slots.shoes) {
    const clothing = mockWardrobeClothes.find((c) => c.id === diyRecord.slots.shoes);
    if (clothing) {
      detectedClothes.push({
        id: `detected-${Date.now()}-${diyRecord.slots.shoes}`,
        category: clothing.category,
        name: clothing.name,
        color: clothing.color,
      });
    }
  }

  // 处理配饰
  diyRecord.accessories.forEach((acc) => {
    const clothing = mockWardrobeClothes.find((c) => c.id === acc.clothing_id);
    if (clothing) {
      detectedClothes.push({
        id: `detected-${Date.now()}-${acc.clothing_id}`,
        category: clothing.category,
        name: clothing.name,
        color: clothing.color,
        position: acc.position,
      });
    }
  });

  return addCollectionItem({
    name: diyRecord.name,
    source: 'diy',
    image_url: diyRecord.generated_image_url || '',
    // 直接使用分析完成的数据
  }).then((item) =>
    updateCollectionItem(item.id, {
      detected_clothes: detectedClothes,
      analysis_status: 'completed',
      diy_record_id: diyRecord.id,
    })
  );
}
