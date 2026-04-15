'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, RefreshCw, Globe, Upload, Sparkles, Loader2 } from 'lucide-react';
import type { OutfitCollectionItem } from '@/types/collection';
import { SCENE_OPTIONS } from '@/types/collection';
import { getCollectionItems, addCollectionByUrl, addCollectionByUpload } from '@/lib/api/collection';
import { AddCollectionModal } from '@/components/collection/AddModal';

// 来源图标映射
const sourceIcons = {
  url: { icon: Globe, label: 'URL', color: 'bg-blue-500' },
  upload: { icon: Upload, label: '上传', color: 'bg-emerald-500' },
  diy: { icon: Sparkles, label: 'DIY', color: 'bg-amber-500' },
};

// Collection Card Component
interface CollectionCardProps {
  item: OutfitCollectionItem;
  onClick: () => void;
}

const CollectionCard = ({ item, onClick }: CollectionCardProps) => {
  const source = sourceIcons[item.source];
  const SourceIcon = source.icon;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden cursor-pointer"
    >
      {/* 穿搭图 + 来源标记 */}
      <div className="aspect-[3/4] bg-slate-100 relative">
        <img
          src={item.original_image_url}
          alt={item.name}
          className="w-full h-full object-cover"
        />
        {/* 来源标记 */}
        <div
          className={`absolute top-2 left-2 ${source.color} px-2 py-0.5 rounded-full flex items-center gap-1`}
        >
          <SourceIcon className="w-3 h-3 text-white" />
          <span className="text-[10px] font-medium text-white">{source.label}</span>
        </div>
        {/* 分析状态 */}
        {item.analysis_status === 'analyzing' && (
          <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          </div>
        )}
        {item.analysis_status === 'pending' && (
          <div className="absolute bottom-2 right-2 bg-amber-500 px-2 py-0.5 rounded-full">
            <span className="text-[10px] font-medium text-white">待分析</span>
          </div>
        )}
      </div>

      {/* 信息 */}
      <div className="p-3">
        <h3 className="text-sm font-medium text-slate-900 truncate">{item.name}</h3>

        {/* 场景/风格标签 */}
        <div className="flex items-center gap-1 mt-2">
          {item.scene && (
            <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
              {item.scene}
            </span>
          )}
          {item.style && (
            <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
              {item.style}
            </span>
          )}
        </div>

        {/* 识别衣物数量 */}
        {item.analysis_status === 'completed' && item.detected_clothes.length > 0 && (
          <p className="text-[10px] text-slate-400 mt-2">
            识别到 {item.detected_clothes.length} 件衣物
          </p>
        )}
      </div>
    </motion.div>
  );
};

// Main Page Component
export default function CollectionPage() {
  const router = useRouter();
  const [items, setItems] = useState<OutfitCollectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeScene, setActiveScene] = useState<string>('全部');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const data = await getCollectionItems();
      setItems(data);
    } catch (error) {
      console.error('获取穿搭集失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 筛选
  const filteredItems =
    activeScene === '全部'
      ? items
      : items.filter((item) => item.scene === activeScene);

  // 收集所有出现的场景
  const presentScenes = ['全部', ...new Set(items.map((item) => item.scene).filter(Boolean))];

  const handleCardClick = (item: OutfitCollectionItem) => {
    router.push(`/collection/${item.id}`);
  };

  const handleAddSuccess = (newItem: OutfitCollectionItem) => {
    setItems((prev) => [newItem, ...prev]);
    setShowAddModal(false);
  };

  return (
    <div className="min-h-screen bg-[#F1F4F9]">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-[#F1F4F9]/95 backdrop-blur-md">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600" />
              </button>
              <h1 className="text-xl font-bold text-slate-900">穿搭集</h1>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="w-9 h-9 bg-[#FE8F39] rounded-xl shadow-sm flex items-center justify-center hover:bg-[#e07d2a] transition-colors"
            >
              <Plus className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>

        {/* 分类标签 */}
        <div className="px-4 pb-3 overflow-x-auto">
          <div className="flex gap-2">
            {presentScenes.map((scene) => (
              <button
                key={scene}
                onClick={() => setActiveScene(scene)}
                className={`px-4 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  activeScene === scene
                    ? 'bg-[#FE8F39] text-white'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-100'
                }`}
              >
                {scene}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-slate-300" />
            </div>
            <p className="text-slate-400 mb-2">
              {activeScene === '全部' ? '暂无穿搭灵感' : `暂无${activeScene}相关的穿搭`}
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="text-sm font-medium text-[#FE8F39] hover:underline"
            >
              立即添加
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {filteredItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <CollectionCard item={item} onClick={() => handleCardClick(item)} />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Add Modal */}
      <AddCollectionModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={handleAddSuccess}
      />
    </div>
  );
}
