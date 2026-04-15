'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, X, Pencil, RefreshCw, Bookmark, Loader2 } from 'lucide-react';
import type { DIYOutfitRecord, SlotClothing } from '@/types/diy';
import { mockWardrobeClothes } from '@/app/diy/mock';
import { importFromDIY } from '@/lib/api/collection';

// Mock 数据（暂时使用）
const mockRecords: DIYOutfitRecord[] = [
  {
    id: '1',
    name: '春日休闲穿搭',
    slots: {
      top: ['top-1', 'top-2'],
      bottom: 'bottom-1',
      shoes: 'shoes-1',
    },
    accessories: [{ clothing_id: 'acc-1' }],
    generated_image_url: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=800&fit=crop',
    prompt: '右手提包，位于身体右侧',
    created_at: '2026-04-14T10:30:00Z',
  },
  {
    id: '2',
    name: '通勤穿搭',
    slots: {
      top: ['top-3'],
      bottom: 'bottom-2',
      shoes: 'shoes-2',
    },
    accessories: [{ clothing_id: 'acc-2' }],
    generated_image_url: 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=600&h=800&fit=crop',
    prompt: '银色手表佩戴在左手',
    created_at: '2026-04-13T14:20:00Z',
  },
  {
    id: '3',
    name: '约会搭配',
    slots: {
      top: ['top-4'],
      bottom: 'bottom-3',
      shoes: 'shoes-3',
    },
    accessories: [{ clothing_id: 'acc-3' }, { clothing_id: 'acc-4' }],
    generated_image_url: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=800&fit=crop',
    prompt: '太阳镜戴在头上，双肩包挂在背后',
    created_at: '2026-04-12T09:15:00Z',
  },
];

// 构建 clothing ID 到对象的映射
const clothingMap: Record<string, SlotClothing> = {};
mockWardrobeClothes.forEach((c) => {
  clothingMap[c.id] = c;
});

// Record Card Component
interface RecordCardProps {
  record: DIYOutfitRecord;
  onClick: () => void;
}

const RecordCard = ({ record, onClick }: RecordCardProps) => {
  // 收集所有衣物 ID
  const allClothingIds = [
    ...record.slots.top,
    record.slots.bottom,
    record.slots.shoes,
    ...record.accessories.map((a) => a.clothing_id),
  ].filter(Boolean);

  const displayClothes = allClothingIds.slice(0, 6);
  const extraCount = allClothingIds.length - 6;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}-${date.getDate()}`;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden cursor-pointer"
    >
      {/* 穿搭图 */}
      <div className="aspect-[3/4] bg-slate-100 relative">
        {record.generated_image_url ? (
          <img
            src={record.generated_image_url}
            alt={record.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-300">
            暂无图片
          </div>
        )}
      </div>

      {/* 信息 */}
      <div className="p-3">
        <h3 className="text-sm font-medium text-slate-900 truncate">{record.name}</h3>

        {/* 衣物缩略图网格 */}
        <div className="flex items-center gap-1 mt-2">
          {displayClothes.map((id) => {
            const clothing = clothingMap[id];
            if (!clothing) return null;
            return (
              <div
                key={id}
                className="w-8 h-8 rounded-lg overflow-hidden bg-slate-50 border border-slate-100"
              >
                <img
                  src={clothing.imageUrl}
                  alt={clothing.name}
                  className="w-full h-full object-cover"
                />
              </div>
            );
          })}
          {extraCount > 0 && (
            <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-100 flex items-center justify-center">
              <span className="text-[10px] text-slate-500">+{extraCount}</span>
            </div>
          )}
        </div>

        <p className="text-[10px] text-slate-400 mt-2">{formatDate(record.created_at)}</p>
      </div>
    </motion.div>
  );
};

// Detail Modal Component
interface DetailModalProps {
  record: DIYOutfitRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onTitleChange: (id: string, name: string) => void;
  onReEdit: (record: DIYOutfitRecord) => void;
  onAddToCollection?: (record: DIYOutfitRecord) => Promise<void>;
}

const DetailModal = ({ record, isOpen, onClose, onTitleChange, onReEdit, onAddToCollection }: DetailModalProps) => {
  const [editingTitle, setEditingTitle] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [addingToCollection, setAddingToCollection] = useState(false);

  useEffect(() => {
    if (record) {
      setEditingTitle(record.name);
      setIsEditing(false);
    }
  }, [record]);

  if (!record) return null;

  const handleTitleSave = () => {
    if (editingTitle.trim() && editingTitle !== record.name) {
      onTitleChange(record.id, editingTitle.trim());
    }
    setIsEditing(false);
  };

  const handleAddToCollection = async () => {
    if (!record || !onAddToCollection) return;
    setAddingToCollection(true);
    try {
      await onAddToCollection(record);
    } finally {
      setAddingToCollection(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="bg-white rounded-3xl w-full max-w-md shadow-2xl max-h-[90vh] flex flex-col"
          >
            {/* Header - 固定在顶部 */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100 flex-shrink-0">
              <h3 className="text-lg font-bold text-slate-900">穿搭详情</h3>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {/* Content - 可滚动 */}
            <div className="flex-1 overflow-y-auto p-4">
              {/* 大图 */}
              <div className="aspect-[3/4] bg-slate-100 rounded-2xl overflow-hidden mb-4">
                {record.generated_image_url ? (
                  <img
                    src={record.generated_image_url}
                    alt={record.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-300">
                    暂无图片
                  </div>
                )}
              </div>

              {/* 可编辑标题 */}
              <div className="mb-4">
                {isEditing ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={handleTitleSave}
                    onKeyDown={(e) => e.key === 'Enter' && handleTitleSave()}
                    autoFocus
                    className="w-full px-3 py-2 text-base font-medium border border-[#FE8F39] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FE8F39]"
                  />
                ) : (
                  <div
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2 cursor-pointer group"
                  >
                    <h2 className="text-lg font-bold text-slate-900">{record.name}</h2>
                    <Pencil className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                )}
              </div>

              {/* 配饰描述 */}
              {record.prompt && (
                <div className="mb-4 p-3 bg-amber-50 rounded-xl">
                  <p className="text-xs text-amber-700">
                    <span className="font-medium">配饰说明：</span>
                    {record.prompt}
                  </p>
                </div>
              )}

              {/* 衣物信息（只读，按分类展示） */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-slate-700 mb-3">衣物信息</h4>

                {/* 上身 */}
                {record.slots.top.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 mb-2">上身</p>
                    <div className="flex flex-wrap gap-2">
                      {record.slots.top.map((id) => {
                        const clothing = clothingMap[id];
                        if (!clothing) return null;
                        return (
                          <div key={id} className="flex items-center gap-2 px-2 py-1 bg-rose-50 rounded-full">
                            <div className="w-8 h-8 rounded-lg overflow-hidden bg-white border border-rose-100">
                              <img src={clothing.imageUrl} alt={clothing.name} className="w-full h-full object-cover" />
                            </div>
                            <span className="text-xs text-rose-700 font-medium">{clothing.name}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 下身 */}
                {record.slots.bottom && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 mb-2">下身</p>
                    <div className="flex items-center gap-2 px-2 py-1 bg-blue-50 rounded-full">
                      <div className="w-8 h-8 rounded-lg overflow-hidden bg-white border border-blue-100">
                        <img src={clothingMap[record.slots.bottom]?.imageUrl} alt={clothingMap[record.slots.bottom]?.name} className="w-full h-full object-cover" />
                      </div>
                      <span className="text-xs text-blue-700 font-medium">{clothingMap[record.slots.bottom]?.name}</span>
                    </div>
                  </div>
                )}

                {/* 鞋子 */}
                {record.slots.shoes && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 mb-2">鞋子</p>
                    <div className="flex items-center gap-2 px-2 py-1 bg-amber-50 rounded-full">
                      <div className="w-8 h-8 rounded-lg overflow-hidden bg-white border border-amber-100">
                        <img src={clothingMap[record.slots.shoes]?.imageUrl} alt={clothingMap[record.slots.shoes]?.name} className="w-full h-full object-cover" />
                      </div>
                      <span className="text-xs text-amber-700 font-medium">{clothingMap[record.slots.shoes]?.name}</span>
                    </div>
                  </div>
                )}

                {/* 配饰 */}
                {record.accessories.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 mb-2">配饰</p>
                    <div className="flex flex-wrap gap-2">
                      {record.accessories.map((acc) => {
                        const clothing = clothingMap[acc.clothing_id];
                        if (!clothing) return null;
                        return (
                          <div key={acc.clothing_id} className="flex items-center gap-2 px-2 py-1 bg-emerald-50 rounded-full">
                            <div className="w-8 h-8 rounded-lg overflow-hidden bg-white border border-emerald-100">
                              <img src={clothing.imageUrl} alt={clothing.name} className="w-full h-full object-cover" />
                            </div>
                            <span className="text-xs text-emerald-700 font-medium">{clothing.name}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* 重新编辑按钮 */}
              <button
                onClick={() => onReEdit(record)}
                className="w-full py-3 rounded-xl bg-[#FE8F39] text-white font-medium text-sm flex items-center justify-center gap-2 hover:bg-[#e07d2a] transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                重新编辑
              </button>

              {/* 收藏到穿搭集按钮 */}
              <button
                onClick={handleAddToCollection}
                disabled={addingToCollection}
                className="w-full py-3 rounded-xl bg-emerald-500 text-white font-medium text-sm flex items-center justify-center gap-2 hover:bg-emerald-600 transition-colors disabled:opacity-50"
              >
                {addingToCollection ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Bookmark className="w-4 h-4" />
                )}
                收藏到穿搭集
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Main Page Component
export default function DIYRecordsPage() {
  const router = useRouter();
  const [records, setRecords] = useState<DIYOutfitRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<DIYOutfitRecord | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    // 暂时使用 Mock 数据
    setRecords(mockRecords);
    setLoading(false);
  }, []);

  const handleCardClick = (record: DIYOutfitRecord) => {
    setSelectedRecord(record);
    setModalOpen(true);
  };

  const handleTitleChange = (id: string, name: string) => {
    setRecords((prev) =>
      prev.map((r) => (r.id === id ? { ...r, name } : r))
    );
    if (selectedRecord?.id === id) {
      setSelectedRecord((prev) => (prev ? { ...prev, name } : null));
    }
  };

  const handleReEdit = (record: DIYOutfitRecord) => {
    // 将记录数据存入 localStorage
    localStorage.setItem('diy_edit_record', JSON.stringify(record));
    // 跳转到 DIY 页面
    router.push('/diy');
  };

  const handleAddToCollection = async (record: DIYOutfitRecord) => {
    // 将 DIY 记录导入到穿搭集
    await importFromDIY(record);
    // 显示成功提示
    alert('已收藏到穿搭集');
  };

  return (
    <div className="min-h-screen bg-[#F1F4F9]">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-[#F1F4F9]/95 backdrop-blur-md">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600" />
            </button>
            <h1 className="text-xl font-bold text-slate-900">DIY穿搭记录</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="w-6 h-6 text-slate-400 animate-spin" />
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-400">暂无穿搭记录</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {records.map((record, index) => (
              <motion.div
                key={record.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <RecordCard
                  record={record}
                  onClick={() => handleCardClick(record)}
                />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <DetailModal
        record={selectedRecord}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onTitleChange={handleTitleChange}
        onReEdit={handleReEdit}
        onAddToCollection={handleAddToCollection}
      />
    </div>
  );
}
