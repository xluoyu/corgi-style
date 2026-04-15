'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, Check } from 'lucide-react';
import type { DetectedClothing, AlternativeItem } from '@/types/collection';
import { mockWardrobeClothes } from '@/app/diy/mock';
import { getAlternatives } from '@/lib/api/collection';

// 分类颜色映射（复用）
const categoryColors = {
  top: { bg: 'bg-rose-50', border: 'border-rose-100', text: 'text-rose-700' },
  bottom: { bg: 'bg-blue-50', border: 'border-blue-100', text: 'text-blue-700' },
  shoes: { bg: 'bg-amber-50', border: 'border-amber-100', text: 'text-amber-700' },
  accessory: { bg: 'bg-emerald-50', border: 'border-emerald-100', text: 'text-emerald-700' },
  outer: { bg: 'bg-purple-50', border: 'border-purple-100', text: 'text-purple-700' },
  inner: { bg: 'bg-pink-50', border: 'border-pink-100', text: 'text-pink-700' },
} as const;

interface FindSimilarModalProps {
  isOpen: boolean;
  onClose: () => void;
  detectedClothing: DetectedClothing;
  onSelect: (wardrobeClothingId: string) => void;
  existingAlternativeIds: string[];
}

export function FindSimilarModal({
  isOpen,
  onClose,
  detectedClothing,
  onSelect,
  existingAlternativeIds,
}: FindSimilarModalProps) {
  const [loading, setLoading] = useState(true);
  const [alternatives, setAlternatives] = useState<AlternativeItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && detectedClothing) {
      fetchAlternatives();
    }
  }, [isOpen, detectedClothing]);

  const fetchAlternatives = async () => {
    setLoading(true);
    try {
      // 模拟从衣柜获取相似衣物（实际调用 API）
      const sameCategoryClothes = mockWardrobeClothes.filter(
        (c) => c.category === detectedClothing.category && c.id !== detectedClothing.id
      );

      // 构造替代项
      const mockAlternatives: AlternativeItem[] = sameCategoryClothes.map((c, index) => ({
        id: `alt-${Date.now()}-${index}`,
        original_detected_id: detectedClothing.id,
        wardrobe_clothing_id: c.id,
        wardrobe_clothing: c,
        similarity_score: 0.75 + Math.random() * 0.2,
        reason: '与你衣柜中的衣物风格相似',
      }));

      setAlternatives(mockAlternatives);
    } catch (error) {
      console.error('获取代替推荐失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedId) return;
    setSubmitting(true);
    try {
      onSelect(selectedId);
    } finally {
      setSubmitting(false);
    }
  };

  const colorConfig = categoryColors[detectedClothing.category] || categoryColors.top;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end justify-center"
        >
          <motion.div
            initial={{ opacity: 0, y: '100%' }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="bg-white rounded-t-3xl w-full max-w-md max-h-[80vh] shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100 flex-shrink-0">
              <div>
                <h3 className="text-lg font-bold text-slate-900">找相似</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  为「{detectedClothing.name}」找代替
                </p>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
                </div>
              ) : alternatives.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-slate-400">你的衣柜中暂无相似衣物</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {alternatives.map((alt) => {
                    const clothing = alt.wardrobe_clothing;
                    if (!clothing) return null;
                    const isSelected = selectedId === clothing.id;
                    const isAlreadyAdded = existingAlternativeIds.includes(clothing.id);

                    return (
                      <button
                        key={alt.id}
                        onClick={() => !isAlreadyAdded && setSelectedId(clothing.id)}
                        disabled={isAlreadyAdded}
                        className={`relative p-3 rounded-xl border transition-all text-left ${
                          isSelected
                            ? 'border-[#FE8F39] bg-orange-50'
                            : isAlreadyAdded
                            ? 'border-slate-100 bg-slate-50 opacity-50'
                            : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        {/* 图片 */}
                        <div className="aspect-square rounded-lg overflow-hidden bg-slate-100 mb-2">
                          <img
                            src={clothing.imageUrl}
                            alt={clothing.name}
                            className="w-full h-full object-cover"
                          />
                        </div>

                        {/* 信息 */}
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {clothing.name}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">{clothing.color}</p>

                        {/* 相似度 */}
                        <div className="flex items-center gap-1 mt-1">
                          <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${(alt.similarity_score || 0) * 100}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {Math.round((alt.similarity_score || 0) * 100)}%
                          </span>
                        </div>

                        {/* 已添加标记 */}
                        {isAlreadyAdded && (
                          <div className="absolute top-2 right-2 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                            <Check className="w-4 h-4 text-white" />
                          </div>
                        )}

                        {/* 选中标记 */}
                        {isSelected && !isAlreadyAdded && (
                          <div className="absolute top-2 right-2 w-6 h-6 bg-[#FE8F39] rounded-full flex items-center justify-center">
                            <Check className="w-4 h-4 text-white" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-100 flex-shrink-0">
              <button
                onClick={handleSubmit}
                disabled={!selectedId || submitting}
                className="w-full py-3 rounded-xl bg-[#FE8F39] text-white font-medium text-sm hover:bg-[#e07d2a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                确认添加
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
