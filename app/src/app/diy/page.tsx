'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  X,
  Plus,
  Sparkles,
  Save,
  Check,
  Shirt,
  History,
  Loader2,
} from 'lucide-react';
import { ClothingCanvas, type CanvasItemData } from '@/components/diy/ClothingCanvas';
import { mockWardrobeClothes, categoryLabels } from './mock';
import type { SlotClothing, DIYOutfitRecord } from '@/types/diy';

// Clothing Card Component (for wardrobe drawer)
interface ClothingCardProps {
  clothing: SlotClothing;
  selected: boolean;
  disabled?: boolean;
  onToggleSelect: () => void;
}

const ClothingCard = ({ clothing, selected, disabled, onToggleSelect }: ClothingCardProps) => {
  return (
    <motion.div
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      onClick={disabled ? undefined : onToggleSelect}
      className={`
        relative rounded-xl p-2 shadow-sm border-2 transition-all
        ${disabled
          ? 'border-slate-200 bg-slate-100 cursor-not-allowed opacity-60'
          : selected
            ? 'border-[#FE8F39] bg-[#FE8F39]/5 cursor-pointer'
            : 'border-slate-100 bg-white hover:border-slate-200 cursor-pointer'
        }
      `}
    >
      <div
        className={`
          absolute top-1.5 right-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all
          ${disabled
            ? 'bg-emerald-500 border-emerald-500'
            : selected
              ? 'bg-[#FE8F39] border-[#FE8F39]'
              : 'border-slate-300 bg-white'
          }
        `}
      >
        {(selected || disabled) && <Check className="w-3 h-3 text-white" />}
      </div>

      {disabled && (
        <div className="absolute inset-0 bg-slate-500/20 rounded-xl z-10" />
      )}

      <div className="aspect-square rounded-lg overflow-hidden bg-slate-50">
        <img
          src={clothing.imageUrl}
          alt={clothing.name}
          className="w-full h-full object-cover"
          draggable={false}
        />
      </div>
      <div className="mt-1.5 px-1">
        <p className="text-[10px] font-medium text-slate-700 truncate">{clothing.name}</p>
        <div className="flex items-center gap-1 mt-0.5">
          <div
            className="w-2.5 h-2.5 rounded-full border border-slate-200"
            style={{ backgroundColor: clothing.color }}
          />
          <span className="text-[9px] text-slate-400">{categoryLabels[clothing.category]}</span>
        </div>
      </div>
    </motion.div>
  );
};

// Wardrobe Drawer Component
interface WardrobeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  clothes: SlotClothing[];
  selectedCategory: string;
  selectedIds: string[];
  addedIds: string[];
  onCategoryChange: (category: string) => void;
  onToggleSelect: (id: string) => void;
  onAddToCanvas: () => void;
}

const WardrobeDrawer = ({
  isOpen,
  onClose,
  clothes,
  selectedCategory,
  selectedIds,
  addedIds,
  onCategoryChange,
  onToggleSelect,
  onAddToCanvas,
}: WardrobeDrawerProps) => {
  const filteredClothes =
    selectedCategory === 'all'
      ? clothes
      : clothes.filter((c) => c.category === selectedCategory);

  const categories = ['all', 'top', 'bottom', 'shoes', 'accessory'];
  const selectedCount = selectedIds.length;

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
          />
        )}
      </AnimatePresence>

      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: isOpen ? 0 : '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed right-0 top-0 bottom-0 w-[280px] bg-white shadow-2xl z-50 flex flex-col"
      >
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-slate-900">我的衣柜</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
            >
              <X className="w-4 h-4 text-slate-600" />
            </button>
          </div>

          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => onCategoryChange(cat)}
                className={`
                  px-3 py-1.5 rounded-full text-[11px] font-medium whitespace-nowrap transition-all
                  ${selectedCategory === cat
                    ? 'bg-[#FE8F39] text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }
                `}
              >
                {categoryLabels[cat]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <div className="grid grid-cols-2 gap-2">
            {filteredClothes.map((clothing) => (
              <ClothingCard
                key={clothing.id}
                clothing={clothing}
                selected={selectedIds.includes(clothing.id)}
                disabled={addedIds.includes(clothing.id)}
                onToggleSelect={() => onToggleSelect(clothing.id)}
              />
            ))}
          </div>
          {filteredClothes.length === 0 && (
            <div className="text-center py-8">
              <Shirt className="w-12 h-12 text-slate-200 mx-auto mb-2" />
              <p className="text-sm text-slate-400">该分类暂无衣物</p>
            </div>
          )}
        </div>

        <div className="p-3 border-t border-slate-100 bg-slate-50">
          <button
            onClick={onAddToCanvas}
            disabled={selectedCount === 0}
            className={`
              w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all
              ${selectedCount > 0
                ? 'bg-[#FE8F39] text-white hover:bg-[#e07d2a]'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              }
            `}
          >
            <Plus className="w-4 h-4" />
            {selectedCount > 0 ? `添加到画布 (${selectedCount})` : '选择衣物添加到画布'}
          </button>
        </div>
      </motion.div>
    </>
  );
};

// Outfit Summary Component
interface OutfitSummaryProps {
  items: CanvasItemData[];
  onItemClick: (id: string) => void;
}

const OutfitSummary = ({ items, onItemClick }: OutfitSummaryProps) => {
  if (items.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
        <p className="text-sm text-slate-400 text-center py-2">
          点击衣物添加到画布，开始搭配
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-slate-900">当前搭配</h3>
        <span className="text-[10px] text-slate-400">
          共 {items.length} 件
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={() => onItemClick(item.id)}
            className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-full hover:bg-slate-100 transition-colors"
          >
            <img
              src={item.clothing.imageUrl}
              alt={item.clothing.name}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="text-[10px] text-slate-700 font-medium truncate max-w-[80px]">
              {item.clothing.name}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
};

// Generated Image Modal
interface GeneratedImageModalProps {
  isOpen: boolean;
  imageUrl: string | null;
  onClose: () => void;
  onSave: () => void;
  isLoading: boolean;
}

const GeneratedImageModal = ({ isOpen, imageUrl, onClose, onSave, isLoading }: GeneratedImageModalProps) => {
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
            className="bg-white rounded-3xl p-5 w-full max-w-sm shadow-2xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-900">AI 生成效果</h3>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {isLoading ? (
              <div className="aspect-[3/4] bg-slate-100 rounded-2xl flex flex-col items-center justify-center">
                <div className="w-10 h-10 border-3 border-[#FE8F39] border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-slate-500 mt-3">AI 正在生成穿搭图...</p>
              </div>
            ) : imageUrl ? (
              <div className="aspect-[3/4] bg-slate-100 rounded-2xl overflow-hidden">
                <img
                  src={imageUrl}
                  alt="Generated outfit"
                  className="w-full h-full object-cover"
                />
              </div>
            ) : null}

            <div className="mt-4 flex gap-2">
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                关闭
              </button>
              {imageUrl && (
                <button
                  onClick={onSave}
                  className="flex-1 py-3 rounded-xl bg-[#FE8F39] text-sm font-medium text-white hover:bg-[#e07d2a] transition-colors flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  保存
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Main DIY Page Component
export default function DIYPage() {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [items, setItems] = useState<CanvasItemData[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Calculate next z-index
  const getNextZIndex = useCallback(() => {
    if (items.length === 0) return 1;
    return Math.max(...items.map((i) => i.zIndex)) + 1;
  }, [items]);

  // Get max z-index for "move down" operation
  const getMaxZIndex = useCallback(() => {
    if (items.length === 0) return 1;
    return Math.max(...items.map((i) => i.zIndex));
  }, [items]);

  // Toggle clothing selection in wardrobe
  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );
  }, []);

  // Add selected clothes to canvas center
  const handleAddToCanvas = useCallback(() => {
    const selectedClothes = mockWardrobeClothes.filter((c) => selectedIds.includes(c.id));

    // Calculate center position
    const canvasWidth = 320; // approximate canvas width
    const canvasHeight = 400; // approximate canvas height
    const itemWidth = 90;
    const itemHeight = 110;

    const centerX = (canvasWidth - itemWidth) / 2;
    const centerY = (canvasHeight - itemHeight) / 2;

    // Create new items
    const newItems: CanvasItemData[] = selectedClothes.map((clothing, index) => ({
      id: `canvas-${Date.now()}-${index}`,
      clothing,
      position: {
        x: centerX + (index % 3) * 20 - 20, // slight offset for multiple items
        y: centerY + Math.floor(index / 3) * 20 - 20,
      },
      zIndex: getNextZIndex() + index,
    }));

    setItems((prev) => [...prev, ...newItems]);
    setSelectedIds([]);
    setDrawerOpen(false);
  }, [selectedIds, getNextZIndex]);

  // Handle item selection
  const handleSelectItem = useCallback((id: string | null) => {
    setSelectedItemId(id);
  }, []);

  // Move item up (increase z-index)
  const handleMoveUp = useCallback((id: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, zIndex: item.zIndex + 1 }
          : item
      )
    );
  }, []);

  // Move item down (decrease z-index)
  const handleMoveDown = useCallback((id: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, zIndex: Math.max(1, item.zIndex - 1) }
          : item
      )
    );
  }, []);

  // Delete item from canvas
  const handleDeleteItem = useCallback((id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
    if (selectedItemId === id) {
      setSelectedItemId(null);
    }
  }, [selectedItemId]);

  // Handle position change after drag
  const handlePositionChange = useCallback((id: string, position: { x: number; y: number }) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, position } : item
      )
    );
  }, []);

  // Generate outfit image
  const handleGenerate = useCallback(() => {
    if (items.length === 0) return;

    setIsGenerating(true);
    setShowModal(true);

    // Sort items by z-index (small to large = inner to outer)
    const sortedItems = [...items].sort((a, b) => a.zIndex - b.zIndex);

    // Build prompt
    const promptParts: string[] = [];
    const tops = sortedItems.filter((i) => i.clothing.category === 'top');
    const bottoms = sortedItems.filter((i) => i.clothing.category === 'bottom');
    const shoes = sortedItems.filter((i) => i.clothing.category === 'shoes');
    const accessories = sortedItems.filter((i) => i.clothing.category === 'accessory');

    if (tops.length > 0) {
      promptParts.push(`上装：${tops.map((c) => c.clothing.name).join('、')}`);
    }
    if (bottoms.length > 0) {
      promptParts.push(`下装：${bottoms.map((c) => c.clothing.name).join('、')}`);
    }
    if (shoes.length > 0) {
      promptParts.push(`鞋子：${shoes.map((c) => c.clothing.name).join('、')}`);
    }
    if (accessories.length > 0) {
      promptParts.push(`配饰：${accessories.map((c) => c.clothing.name).join('、')}`);
    }

    const prompt = `真人模特穿搭，${promptParts.join('，')}，正面站姿，简洁背景，高质量`;
    console.log('Generated prompt:', prompt);

    // Simulate AI generation
    setTimeout(() => {
      setGeneratedImage('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=800&fit=crop');
      setIsGenerating(false);
    }, 3000);
  }, [items]);

  // Save outfit
  const handleSave = useCallback(() => {
    console.log('Saving outfit:', { items });
    setShowModal(false);
    setGeneratedImage(null);
  }, [items]);

  // Check if can generate
  const canGenerate = items.length > 0;

  // Get IDs of items already on canvas
  const addedIds = items.map((item) => item.clothing.id);

  return (
    <div className="min-h-screen bg-[#F1F4F9] pb-24">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-[#F1F4F9]/95 backdrop-blur-md">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => window.history.back()}
                className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600" />
              </button>
              <h1 className="text-xl font-bold text-slate-900">DIY穿搭</h1>
            </div>
            <button
              onClick={() => router.push('/diy/records')}
              className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
            >
              <History className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="px-4">
        <div
          ref={canvasRef}
          className="relative bg-white rounded-3xl shadow-lg overflow-hidden border border-slate-100"
          style={{ height: 480 }}
        >
          <ClothingCanvas
            items={items}
            selectedId={selectedItemId}
            onSelect={handleSelectItem}
            onMoveUp={handleMoveUp}
            onMoveDown={handleMoveDown}
            onDelete={handleDeleteItem}
            onPositionChange={handlePositionChange}
          />
        </div>
      </div>

      {/* Outfit Summary */}
      <div className="px-4 mt-4">
        <OutfitSummary
          items={items}
          onItemClick={handleSelectItem}
        />
      </div>

      {/* Add Button (Floating) */}
      <button
        onClick={() => setDrawerOpen(true)}
        className="fixed bottom-28 right-4 w-14 h-14 bg-[#FE8F39] rounded-full shadow-lg shadow-[#FE8F39]/30 flex items-center justify-center hover:bg-[#e07d2a] active:scale-95 transition-all z-30"
      >
        <Plus className="w-6 h-6 text-white" />
      </button>

      {/* Generate Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#F1F4F9] via-[#F1F4F9] to-transparent pt-6">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate}
          className={`
            w-full py-4 rounded-2xl font-bold text-base flex items-center justify-center gap-2 transition-all
            ${canGenerate
              ? 'bg-[#FE8F39] text-white shadow-lg shadow-[#FE8F39]/30 hover:bg-[#e07d2a] active:scale-[0.98]'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }
          `}
        >
          <Sparkles className="w-5 h-5" />
          AI生成穿搭图
        </button>
      </div>

      {/* Wardrobe Drawer */}
      <WardrobeDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        clothes={mockWardrobeClothes}
        selectedCategory={selectedCategory}
        selectedIds={selectedIds}
        addedIds={addedIds}
        onCategoryChange={setSelectedCategory}
        onToggleSelect={handleToggleSelect}
        onAddToCanvas={handleAddToCanvas}
      />

      {/* Generated Image Modal */}
      <GeneratedImageModal
        isOpen={showModal}
        imageUrl={generatedImage}
        onClose={() => {
          setShowModal(false);
          setGeneratedImage(null);
        }}
        onSave={handleSave}
        isLoading={isGenerating}
      />
    </div>
  );
}
