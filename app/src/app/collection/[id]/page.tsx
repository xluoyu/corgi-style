'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  MoreVertical,
  Pencil,
  Trash2,
  Loader2,
  Sparkles,
  RefreshCw,
  Globe,
  Upload,
  SparklesIcon,
} from 'lucide-react';
import type { OutfitCollectionItem, DetectedClothing, AlternativeItem } from '@/types/collection';
import { SCENE_OPTIONS, STYLE_OPTIONS } from '@/types/collection';
import { mockWardrobeClothes } from '@/app/diy/mock';
import {
  getCollectionItem,
  updateCollectionItem,
  deleteCollectionItem,
  triggerAnalyze,
  getAlternatives,
  addAlternative,
} from '@/lib/api/collection';
import { FindSimilarModal } from '@/components/collection/FindSimilarModal';

// 来源图标映射
const sourceIcons = {
  url: { icon: Globe, label: 'URL', color: 'bg-blue-500' },
  upload: { icon: Upload, label: '上传', color: 'bg-emerald-500' },
  diy: { icon: SparklesIcon, label: 'DIY', color: 'bg-amber-500' },
};

// 分类颜色映射
const categoryColors = {
  top: { bg: 'bg-rose-50', border: 'border-rose-100', text: 'text-rose-700', label: '上身' },
  bottom: { bg: 'bg-blue-50', border: 'border-blue-100', text: 'text-blue-700', label: '下身' },
  shoes: { bg: 'bg-amber-50', border: 'border-amber-100', text: 'text-amber-700', label: '鞋子' },
  accessory: { bg: 'bg-emerald-50', border: 'border-emerald-100', text: 'text-emerald-700', label: '配饰' },
  outer: { bg: 'bg-purple-50', border: 'border-purple-100', text: 'text-purple-700', label: '外套' },
  inner: { bg: 'bg-pink-50', border: 'border-pink-100', text: 'text-pink-700', label: '内搭' },
} as const;

// Detected Clothes Panel
interface DetectedClothesPanelProps {
  clothes: DetectedClothing[];
  onFindSimilar: (clothing: DetectedClothing) => void;
  alternatives: AlternativeItem[];
}

const DetectedClothesPanel = ({ clothes, onFindSimilar, alternatives }: DetectedClothesPanelProps) => {
  // 按分类分组
  const groupedClothes = clothes.reduce(
    (acc, item) => {
      const category = item.category;
      if (!acc[category]) acc[category] = [];
      acc[category].push(item);
      return acc;
    },
    {} as Record<string, DetectedClothing[]>
  );

  const categoryOrder: Array<keyof typeof categoryColors> = ['top', 'outer', 'inner', 'bottom', 'shoes', 'accessory'];

  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-slate-700 mb-3">AI 识别的衣物</h4>
      {clothes.length === 0 ? (
        <div className="text-center py-6 text-slate-400 text-sm">
          暂无识别结果
        </div>
      ) : (
        <div className="space-y-4">
          {categoryOrder.map((category) => {
            const items = groupedClothes[category];
            if (!items || items.length === 0) return null;
            const colorConfig = categoryColors[category];

            return (
              <div key={category}>
                <p className="text-xs text-slate-500 mb-2">{colorConfig.label}</p>
                <div className="flex flex-wrap gap-2">
                  {items.map((item) => {
                    const hasAlternative = alternatives.some(
                      (alt) => alt.original_detected_id === item.id
                    );
                    return (
                      <div
                        key={item.id}
                        className={`flex items-center gap-2 px-3 py-2 ${colorConfig.bg} ${colorConfig.border} border rounded-full`}
                      >
                        <span className={`text-sm font-medium ${colorConfig.text}`}>
                          {item.name}
                        </span>
                        <span className="text-xs text-slate-400">({item.color})</span>
                        <button
                          onClick={() => onFindSimilar(item)}
                          className={`ml-1 px-2 py-0.5 text-xs rounded-full transition-colors ${
                            hasAlternative
                              ? 'bg-emerald-100 text-emerald-600'
                              : 'bg-white text-slate-500 hover:bg-slate-100 border border-slate-200'
                          }`}
                        >
                          {hasAlternative ? '已添加' : '找相似'}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Alternatives Panel
interface AlternativesPanelProps {
  alternatives: AlternativeItem[];
  onRemove: (altId: string) => void;
}

const AlternativesPanel = ({ alternatives, onRemove }: AlternativesPanelProps) => {
  if (alternatives.length === 0) {
    return (
      <div className="mb-4">
        <h4 className="text-sm font-medium text-slate-700 mb-3">代替模块</h4>
        <div className="text-center py-6 text-slate-400 text-sm">
          点击衣物旁边的「找相似」添加代替衣物
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-slate-700 mb-3">
        代替模块 ({alternatives.length})
      </h4>
      <div className="space-y-3">
        {alternatives.map((alt) => {
          const wardrobeClothing = mockWardrobeClothes.find(
            (c) => c.id === alt.wardrobe_clothing_id
          );
          if (!wardrobeClothing) return null;

          return (
            <div
              key={alt.id}
              className="flex items-center gap-3 p-3 bg-white border border-slate-100 rounded-xl"
            >
              <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-100">
                <img
                  src={wardrobeClothing.imageUrl}
                  alt={wardrobeClothing.name}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">
                  {wardrobeClothing.name}
                </p>
                <p className="text-xs text-slate-500">
                  相似度 {Math.round((alt.similarity_score || 0) * 100)}%
                </p>
              </div>
              <button
                onClick={() => onRemove(alt.id)}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-red-50 hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Main Page Component
export default function CollectionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [item, setItem] = useState<OutfitCollectionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [showMenu, setShowMenu] = useState(false);
  const [showFindSimilar, setShowFindSimilar] = useState(false);
  const [selectedClothing, setSelectedClothing] = useState<DetectedClothing | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchItem();
  }, [id]);

  const fetchItem = async () => {
    setLoading(true);
    try {
      const data = await getCollectionItem(id);
      setItem(data);
      if (data) {
        setNameInput(data.name);
      }
    } catch (error) {
      console.error('获取穿搭详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNameSave = async () => {
    if (!item || !nameInput.trim()) return;
    if (nameInput === item.name) {
      setEditingName(false);
      return;
    }

    try {
      const updated = await updateCollectionItem(item.id, { name: nameInput.trim() });
      setItem(updated);
      setEditingName(false);
    } catch (error) {
      console.error('更新名称失败:', error);
    }
  };

  const handleDelete = async () => {
    if (!item) return;
    if (!confirm('确定要删除这条穿搭记录吗？')) return;

    try {
      await deleteCollectionItem(item.id);
      router.back();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const handleAnalyze = async () => {
    if (!item) return;
    setAnalyzing(true);
    try {
      await triggerAnalyze(item.id);
      // 模拟分析完成后更新状态
      setTimeout(async () => {
        await fetchItem();
        setAnalyzing(false);
      }, 2000);
    } catch (error) {
      console.error('触发分析失败:', error);
      setAnalyzing(false);
    }
  };

  const handleFindSimilar = (clothing: DetectedClothing) => {
    setSelectedClothing(clothing);
    setShowFindSimilar(true);
  };

  const handleAddAlternative = async (wardrobeClothingId: string) => {
    if (!item || !selectedClothing) return;

    try {
      const newAlt = await addAlternative(item.id, {
        original_detected_id: selectedClothing.id,
        wardrobe_clothing_id: wardrobeClothingId,
      });
      setItem((prev) =>
        prev
          ? {
              ...prev,
              alternatives: [...prev.alternatives, newAlt],
            }
          : null
      );
      setShowFindSimilar(false);
      setSelectedClothing(null);
    } catch (error) {
      console.error('添加代替失败:', error);
    }
  };

  const handleRemoveAlternative = async (altId: string) => {
    if (!item) return;
    // 简化：直接从本地移除（Mock API 不支持删除单个代替）
    setItem((prev) =>
      prev
        ? {
            ...prev,
            alternatives: prev.alternatives.filter((alt) => alt.id !== altId),
          }
        : null
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F1F4F9] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-screen bg-[#F1F4F9] flex items-center justify-center">
        <p className="text-slate-400">穿搭不存在</p>
      </div>
    );
  }

  const source = sourceIcons[item.source];
  const SourceIcon = source.icon;

  return (
    <div className="min-h-screen bg-[#F1F4F9]">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-[#F1F4F9]/95 backdrop-blur-md">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600" />
            </button>

            {/* 操作菜单 */}
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
              >
                <MoreVertical className="w-5 h-5 text-slate-600" />
              </button>

              <AnimatePresence>
                {showMenu && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute right-0 top-12 w-40 bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden"
                  >
                    <button
                      onClick={handleDelete}
                      className="w-full px-4 py-3 text-left text-sm text-red-500 hover:bg-red-50 flex items-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      删除
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4 pb-20">
        {/* 大图 */}
        <div className="aspect-[3/4] bg-slate-100 rounded-2xl overflow-hidden mb-4">
          <img
            src={item.original_image_url}
            alt={item.name}
            className="w-full h-full object-cover"
          />
        </div>

        {/* 名称 */}
        <div className="mb-4">
          {editingName ? (
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onBlur={handleNameSave}
              onKeyDown={(e) => e.key === 'Enter' && handleNameSave()}
              autoFocus
              className="w-full px-3 py-2 text-xl font-bold border border-[#FE8F39] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FE8F39]"
            />
          ) : (
            <div
              onClick={() => setEditingName(true)}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <h1 className="text-xl font-bold text-slate-900">{item.name}</h1>
              <Pencil className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          )}
        </div>

        {/* 标签 */}
        <div className="flex items-center flex-wrap gap-2 mb-6">
          {/* 来源 */}
          <div className={`${source.color} px-2 py-0.5 rounded-full flex items-center gap-1`}>
            <SourceIcon className="w-3 h-3 text-white" />
            <span className="text-[10px] font-medium text-white">{source.label}</span>
          </div>

          {/* 场景 */}
          {item.scene && (
            <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
              {item.scene}
            </span>
          )}

          {/* 风格 */}
          {item.style && (
            <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
              {item.style}
            </span>
          )}

          {/* 分析状态 */}
          {item.analysis_status === 'pending' && (
            <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-600 rounded-full">
              待分析
            </span>
          )}
          {item.analysis_status === 'analyzing' && (
            <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              分析中
            </span>
          )}
          {item.analysis_status === 'failed' && (
            <span className="text-xs px-2 py-0.5 bg-red-100 text-red-600 rounded-full">
              分析失败
            </span>
          )}
        </div>

        {/* AI 识别结果 */}
        <DetectedClothesPanel
          clothes={item.detected_clothes}
          onFindSimilar={handleFindSimilar}
          alternatives={item.alternatives}
        />

        {/* 代替模块 */}
        <AlternativesPanel
          alternatives={item.alternatives}
          onRemove={handleRemoveAlternative}
        />

        {/* 重新分析按钮 */}
        {item.analysis_status !== 'analyzing' && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="w-full py-3 rounded-xl bg-slate-100 text-slate-600 font-medium text-sm flex items-center justify-center gap-2 hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                AI 分析中...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                重新 AI 分析
              </>
            )}
          </button>
        )}
      </div>

      {/* Find Similar Modal */}
      {showFindSimilar && selectedClothing && (
        <FindSimilarModal
          isOpen={showFindSimilar}
          onClose={() => {
            setShowFindSimilar(false);
            setSelectedClothing(null);
          }}
          detectedClothing={selectedClothing}
          onSelect={handleAddAlternative}
          existingAlternativeIds={item.alternatives
            .filter((alt) => alt.original_detected_id === selectedClothing.id)
            .map((alt) => alt.wardrobe_clothing_id)}
        />
      )}
    </div>
  );
}
