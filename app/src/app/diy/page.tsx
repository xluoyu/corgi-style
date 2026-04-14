'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import {
  ArrowLeft,
  X,
  Plus,
  Shirt,
  Sparkles,
  Save,
  Check,
  PlusCircle,
  Pencil,
  Trash,
  GripVertical,
} from 'lucide-react';
import { mockWardrobeClothes, categoryLabels, slotLabels } from './mock';
import type { SlotClothing, AccessoryItem } from '@/types/diy';

// Mannequin Image Component
interface MannequinImageProps {
  src?: string;
}

const MannequinImage = ({ src }: MannequinImageProps) => {
  const defaultSrc = '/images/body.png';

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <img
        src={src || defaultSrc}
        alt="模特"
        className="w-full h-full object-contain"
        draggable={false}
      />
    </div>
  );
};

// Slot Zone Component
interface SlotZoneProps {
  type: 'top' | 'bottom' | 'shoes';
  clothes: SlotClothing[];
  onRemove: (id: string) => void;
  onClick: () => void;
  onEdit?: () => void;
}

const SlotZone = ({ type, clothes, onRemove, onClick, onEdit }: SlotZoneProps) => {
  const positions = {
    top: { top: '20%', left: '50%', transform: 'translateX(-50%)' },
    bottom: { top: '48%', left: '50%', transform: 'translateX(-50%)' },
    shoes: { top: '86%', left: '50%', transform: 'translateX(-50%)' },
  };

  return (
    <div
      className="absolute"
      style={positions[type]}
    >
      {/* Edit button for top slot */}
      {type === 'top' && clothes.length > 0 && onEdit && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          className="absolute -left-10 top-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-lg shadow-md border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors z-10"
        >
          <Pencil className="w-4 h-4 text-slate-600" />
        </button>
      )}

      {/* Drop Zone Indicator */}
      <div
        className={`
          relative flex flex-col items-center justify-center
          border-2 border-dashed rounded-2xl
          transition-all duration-300
          ${clothes.length > 0
            ? 'border-emerald-300 bg-emerald-50/50'
            : 'border-slate-200 bg-white/50 hover:border-slate-300 hover:bg-white cursor-pointer'
          }
        `}
        style={{
          width: type === 'shoes' ? 120 : 100,
          height: type === 'shoes' ? 60 : type === 'top' ? 120 : 100,
        }}
        onClick={clothes.length === 0 ? onClick : undefined}
      >
        {/* Slot Label */}
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-white rounded-full shadow-sm border border-slate-100">
          <span className="text-[10px] font-medium text-slate-500">{slotLabels[type]}</span>
        </div>

        {/* Clothes in this slot */}
        <div className="flex flex-wrap items-center justify-center gap-1 p-2">
          {clothes.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="relative group"
              onClick={(e) => e.stopPropagation()}
            >
              <div
                className="w-12 h-12 rounded-lg overflow-hidden border-2 border-white shadow-md"
                style={{ zIndex: clothes.length - index }}
              >
                <img
                  src={item.imageUrl}
                  alt={item.name}
                  className="w-full h-full object-cover"
                  draggable={false}
                />
              </div>
              {/* Remove button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(item.id);
                }}
                className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity flex"
              >
                <X className="w-2.5 h-2.5 text-white" />
              </button>
              {/* Layer indicator for top */}
              {type === 'top' && index > 0 && (
                <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-[#FE8F39] rounded-full flex items-center justify-center">
                  <span className="text-[8px] text-white font-bold">{index + 1}</span>
                </div>
              )}
            </motion.div>
          ))}
          {clothes.length === 0 && (
            <div className="text-center p-2" onClick={onClick}>
              <PlusCircle className="w-5 h-5 text-slate-300 mx-auto" />
              <span className="text-[10px] text-slate-400 mt-1 block">点击添加</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Draggable Accessory Component
interface AccessoryItemProps {
  item: AccessoryItem;
  onPositionChange: (id: string, position: { x: number; y: number }) => void;
  onRemove: (id: string) => void;
}

const AccessoryItemComponent = ({ item, onPositionChange, onRemove }: AccessoryItemProps) => {
  const itemRef = useRef<HTMLDivElement>(null);

  return (
    <div
      className="absolute"
      style={{ left: item.position.x, top: item.position.y }}
    >
      <motion.div
        ref={itemRef}
        drag
        dragMomentum={false}
        onDragEnd={(_, info) => {
          const containerRect = itemRef.current?.parentElement?.getBoundingClientRect();
          if (containerRect) {
            const x = item.position.x + info.offset.x;
            const y = item.position.y + info.offset.y;
            onPositionChange(item.id, {
              x: Math.max(0, Math.min(x, containerRect.width - 56)),
              y: Math.max(0, Math.min(y, containerRect.height - 56)),
            });
          }
        }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="relative cursor-grab active:cursor-grabbing"
      >
        <div className="w-14 h-14 rounded-xl overflow-hidden border-2 border-white shadow-lg bg-white">
          <img
            src={item.clothing.imageUrl}
            alt={item.clothing.name}
            className="w-full h-full object-cover"
            draggable={false}
          />
        </div>
        {/* Remove button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(item.id);
          }}
          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full items-center justify-center opacity-0 hover:opacity-100 transition-opacity flex"
        >
          <X className="w-2.5 h-2.5 text-white" />
        </button>
      </motion.div>
    </div>
  );
};

// Clothing Card Component ( selectable)
interface ClothingCardProps {
  clothing: SlotClothing;
  selected: boolean;
  onToggleSelect: () => void;
}

const ClothingCard = ({ clothing, selected, onToggleSelect }: ClothingCardProps) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onToggleSelect}
      className={`
        relative cursor-pointer rounded-xl p-2 shadow-sm border-2 transition-all
        ${selected
          ? 'border-[#FE8F39] bg-[#FE8F39]/5'
          : 'border-slate-100 bg-white hover:border-slate-200'
        }
      `}
    >
      {/* Checkbox */}
      <div
        className={`
          absolute top-1.5 right-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all
          ${selected
            ? 'bg-[#FE8F39] border-[#FE8F39]'
            : 'border-slate-300 bg-white'
          }
        `}
      >
        {selected && <Check className="w-3 h-3 text-white" />}
      </div>

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
          <span className="text-[9px] text-slate-400">{slotLabels[clothing.category]}</span>
        </div>
      </div>
    </motion.div>
  );
};

// Top Slot Editor Drawer Component
interface TopSlotEditorProps {
  isOpen: boolean;
  onClose: () => void;
  clothes: SlotClothing[];
  onReorder: (newOrder: SlotClothing[]) => void;
  onRemove: (id: string) => void;
}

const TopSlotEditor = ({ isOpen, onClose, clothes, onReorder, onRemove }: TopSlotEditorProps) => {
  const [items, setItems] = useState(clothes);

  // Update local items when clothes prop changes
  useState(() => {
    setItems(clothes);
  });

  const handleDragEnd = (newItems: SlotClothing[]) => {
    setItems(newItems);
    onReorder(newItems);
  };

  return (
    <>
      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Drawer - slides from left */}
      <motion.div
        initial={{ x: '-100%' }}
        animate={{ x: isOpen ? 0 : '-100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed left-0 top-0 bottom-0 w-[260px] bg-white shadow-2xl z-50 flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">编辑上身</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
            >
              <X className="w-4 h-4 text-slate-600" />
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">从上到下表示从内到外</p>
        </div>

        {/* Reorderable List */}
        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <div className="text-center py-8">
              <Shirt className="w-12 h-12 text-slate-200 mx-auto mb-2" />
              <p className="text-sm text-slate-400">暂无衣物</p>
            </div>
          ) : (
            <Reorder.Group
              axis="y"
              values={items}
              onReorder={handleDragEnd}
              className="flex flex-col gap-2"
            >
              {items.map((item, index) => (
                <Reorder.Item
                  key={item.id}
                  value={item}
                  className="relative"
                >
                  {/* Dashed line connector */}
                  {index < items.length - 1 && (
                    <div className="absolute left-1/2 -translate-x-1/2 top-full w-0.5 h-4 border-l-2 border-dashed border-slate-300 z-10" />
                  )}

                  <div className="flex items-center gap-3 bg-slate-50 rounded-xl p-2 border border-slate-100">
                    {/* Drag handle */}
                    <div className="cursor-grab active:cursor-grabbing">
                      <GripVertical className="w-5 h-5 text-slate-400" />
                    </div>

                    {/* Thumbnail */}
                    <div className="w-14 h-14 rounded-lg overflow-hidden bg-white border border-slate-100">
                      <img
                        src={item.imageUrl}
                        alt={item.name}
                        className="w-full h-full object-cover"
                        draggable={false}
                      />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-700 truncate">{item.name}</p>
                      <p className="text-[10px] text-slate-400">
                        {index === 0 ? '最内层' : index === items.length - 1 ? '最外层' : `第 ${index + 1} 层`}
                      </p>
                    </div>

                    {/* Delete button */}
                    <button
                      onClick={() => onRemove(item.id)}
                      className="w-7 h-7 rounded-full bg-red-50 flex items-center justify-center hover:bg-red-100 transition-colors"
                    >
                      <Trash className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </Reorder.Item>
              ))}
            </Reorder.Group>
          )}
        </div>
      </motion.div>
    </>
  );
};

// Wardrobe Drawer Component
interface WardrobeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  clothes: SlotClothing[];
  selectedCategory: string;
  selectedIds: string[];
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
      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Drawer */}
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: isOpen ? 0 : '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed right-0 top-0 bottom-0 w-[280px] bg-white shadow-2xl z-50 flex flex-col"
      >
        {/* Header */}
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

          {/* Category Tabs */}
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

        {/* Clothes Grid */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className="grid grid-cols-2 gap-2">
            {filteredClothes.map((clothing) => (
              <ClothingCard
                key={clothing.id}
                clothing={clothing}
                selected={selectedIds.includes(clothing.id)}
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

        {/* Add Button */}
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
  slots: { top: SlotClothing[]; bottom: SlotClothing | null; shoes: SlotClothing | null };
  accessories: AccessoryItem[];
}

const OutfitSummary = ({ slots, accessories }: OutfitSummaryProps) => {
  const totalItems =
    slots.top.length +
    (slots.bottom ? 1 : 0) +
    (slots.shoes ? 1 : 0) +
    accessories.length;

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-slate-900">当前搭配</h3>
        <span className="text-[10px] text-slate-400">
          共 {totalItems} 件
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {/* Top items */}
        {slots.top.map((item) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-2 py-1 bg-rose-50 rounded-full"
          >
            <img
              src={item.imageUrl}
              alt={item.name}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="text-[10px] text-rose-700 font-medium">{item.name}</span>
          </motion.div>
        ))}

        {/* Bottom */}
        {slots.bottom && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-2 py-1 bg-blue-50 rounded-full"
          >
            <img
              src={slots.bottom.imageUrl}
              alt={slots.bottom.name}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="text-[10px] text-blue-700 font-medium">{slots.bottom.name}</span>
          </motion.div>
        )}

        {/* Shoes */}
        {slots.shoes && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-2 py-1 bg-amber-50 rounded-full"
          >
            <img
              src={slots.shoes.imageUrl}
              alt={slots.shoes.name}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="text-[10px] text-amber-700 font-medium">{slots.shoes.name}</span>
          </motion.div>
        )}

        {/* Accessories */}
        {accessories.map((item) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-2 py-1 bg-emerald-50 rounded-full"
          >
            <img
              src={item.clothing.imageUrl}
              alt={item.clothing.name}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="text-[10px] text-emerald-700 font-medium">{item.clothing.name}</span>
          </motion.div>
        ))}

        {totalItems === 0 && (
          <p className="text-sm text-slate-400 w-full text-center py-2">
            点击点位区域添加衣物
          </p>
        )}
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
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [topEditorOpen, setTopEditorOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [slots, setSlots] = useState<{
    top: SlotClothing[];
    bottom: SlotClothing | null;
    shoes: SlotClothing | null;
  }>({
    top: [],
    bottom: null,
    shoes: null,
  });
  const [accessories, setAccessories] = useState<AccessoryItem[]>([]);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Toggle clothing selection
  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );
  }, []);

  // Add selected clothes to canvas
  const handleAddToCanvas = useCallback(() => {
    const selectedClothes = mockWardrobeClothes.filter((c) => selectedIds.includes(c.id));

    // Separate accessories from clothes
    const accessoryClothes = selectedClothes.filter((c) => c.category === 'accessory');
    const topClothes = selectedClothes.filter((c) => c.category === 'top');
    const bottomClothes = selectedClothes.filter((c) => c.category === 'bottom');
    const shoesClothes = selectedClothes.filter((c) => c.category === 'shoes');

    // Add to slots
    setSlots((prev) => ({
      top: [...prev.top, ...topClothes],
      bottom: bottomClothes[0] || prev.bottom, // Only take first bottom
      shoes: shoesClothes[0] || prev.shoes, // Only take first shoes
    }));

    // Add accessories to top-left corner
    const newAccessories = accessoryClothes.map((c, index) => ({
      id: `acc-${Date.now()}-${index}`,
      clothing: c,
      position: { x: 20 + index * 60, y: 20 }, // Offset each accessory
    }));
    setAccessories((prev) => [...prev, ...newAccessories]);

    // Clear selection and close drawer
    setSelectedIds([]);
    setDrawerOpen(false);
  }, [selectedIds]);

  // Remove clothing from slot
  const handleRemoveFromSlot = useCallback((id: string) => {
    setSlots((prev) => ({
      ...prev,
      top: prev.top.filter((c) => c.id !== id),
      bottom: prev.bottom?.id === id ? null : prev.bottom,
      shoes: prev.shoes?.id === id ? null : prev.shoes,
    }));
  }, []);

  // Handle top slot reorder
  const handleTopReorder = useCallback((newOrder: SlotClothing[]) => {
    setSlots((prev) => ({
      ...prev,
      top: newOrder,
    }));
  }, []);

  // Handle slot click - open drawer with category filter
  const handleSlotClick = useCallback((type: 'top' | 'bottom' | 'shoes') => {
    setSelectedCategory(type);
    setDrawerOpen(true);
  }, []);

  // Remove accessory
  const handleRemoveAccessory = useCallback((id: string) => {
    setAccessories((prev) => prev.filter((a) => a.id !== id));
  }, []);

  // Update accessory position
  const handleAccessoryPositionChange = useCallback(
    (id: string, position: { x: number; y: number }) => {
      setAccessories((prev) =>
        prev.map((a) => (a.id === id ? { ...a, position } : a))
      );
    },
    []
  );

  // Generate outfit image
  const handleGenerate = useCallback(() => {
    setIsGenerating(true);
    setShowModal(true);

    // Simulate AI generation
    setTimeout(() => {
      setGeneratedImage('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=800&fit=crop');
      setIsGenerating(false);
    }, 3000);
  }, []);

  // Save outfit
  const handleSave = useCallback(() => {
    // In real implementation, save to backend
    console.log('Saving outfit:', { slots, accessories });
    setShowModal(false);
    setGeneratedImage(null);
  }, [slots, accessories]);

  // Check if can generate
  const canGenerate =
    slots.top.length > 0 || slots.bottom || slots.shoes || accessories.length > 0;

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
              onClick={() => setDrawerOpen(true)}
              className="w-9 h-9 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center hover:bg-slate-50 transition-colors"
            >
              <Shirt className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="px-4">
        <div
          ref={canvasRef}
          className="relative bg-white rounded-3xl shadow-lg overflow-hidden border border-slate-100"
          style={{ height: 520 }}
        >
          {/* Background gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-50 to-slate-100/50" />

          {/* Decorative elements */}
          <div className="absolute top-4 left-4 w-20 h-20 bg-[#FE8F39]/5 rounded-full blur-2xl" />
          <div className="absolute bottom-4 right-4 w-32 h-32 bg-[#FE8F39]/10 rounded-full blur-3xl" />

          {/* Mannequin with Slot Zones */}
          <div className="relative w-full h-full flex items-center justify-center">
            {/* Mannequin Image */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <MannequinImage />
            </div>

            {/* Slot Zones */}
            <SlotZone
              type="top"
              clothes={slots.top}
              onRemove={handleRemoveFromSlot}
              onClick={() => handleSlotClick('top')}
              onEdit={() => setTopEditorOpen(true)}
            />
            <SlotZone
              type="bottom"
              clothes={slots.bottom ? [slots.bottom] : []}
              onRemove={handleRemoveFromSlot}
              onClick={() => handleSlotClick('bottom')}
            />
            <SlotZone
              type="shoes"
              clothes={slots.shoes ? [slots.shoes] : []}
              onRemove={handleRemoveFromSlot}
              onClick={() => handleSlotClick('shoes')}
            />

            {/* Accessories Layer */}
            {accessories.map((item) => (
              <AccessoryItemComponent
                key={item.id}
                item={item}
                onPositionChange={handleAccessoryPositionChange}
                onRemove={handleRemoveAccessory}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Outfit Summary */}
      <div className="px-4 mt-4">
        <OutfitSummary slots={slots} accessories={accessories} />
      </div>

      {/* Prompt Input */}
      <div className="px-4 mt-4">
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-[#FE8F39]" />
            <span className="text-sm font-medium text-slate-900">补充描述</span>
            <span className="text-[10px] text-slate-400">(可选)</span>
          </div>
          <input
            type="text"
            placeholder="例如：适合春日出行，休闲风格..."
            className="w-full px-3 py-2 bg-slate-50 rounded-xl text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#FE8F39]/30"
          />
        </div>
      </div>

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

      {/* Top Slot Editor Drawer */}
      <TopSlotEditor
        isOpen={topEditorOpen}
        onClose={() => setTopEditorOpen(false)}
        clothes={slots.top}
        onReorder={handleTopReorder}
        onRemove={handleRemoveFromSlot}
      />

      {/* Wardrobe Drawer */}
      <WardrobeDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        clothes={mockWardrobeClothes}
        selectedCategory={selectedCategory}
        selectedIds={selectedIds}
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
