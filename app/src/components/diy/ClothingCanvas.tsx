'use client';

import { useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CanvasItem } from './CanvasItem';
import type { SlotClothing } from '@/types/diy';

export interface CanvasItemData {
  id: string;
  clothing: SlotClothing;
  position: { x: number; y: number };
  zIndex: number;
}

interface ClothingCanvasProps {
  items: CanvasItemData[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  onDelete: (id: string) => void;
  onPositionChange: (id: string, position: { x: number; y: number }) => void;
  onDrop?: (position: { x: number; y: number }) => void;
}

export function ClothingCanvas({
  items,
  selectedId,
  onSelect,
  onMoveUp,
  onMoveDown,
  onDelete,
  onPositionChange,
  onDrop,
}: ClothingCanvasProps) {
  const handleCanvasClick = useCallback(() => {
    onSelect(null);
  }, [onSelect]);

  const handleDragEndFromChild = useCallback(
    (id: string, position: { x: number; y: number }) => {
      onPositionChange(id, position);
    },
    [onPositionChange]
  );

  return (
    <div
      className="relative w-full h-full overflow-hidden rounded-3xl"
      onClick={handleCanvasClick}
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-slate-100" />

      {/* Decorative elements */}
      <div className="absolute top-8 left-8 w-24 h-24 bg-[#FE8F39]/5 rounded-full blur-3xl" />
      <div className="absolute bottom-12 right-12 w-40 h-40 bg-[#FE8F39]/10 rounded-full blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-50/30 rounded-full blur-3xl" />

      {/* Grid pattern (subtle) */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #94a3b8 1px, transparent 1px),
            linear-gradient(to bottom, #94a3b8 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
        }}
      />

      {/* Drop zone hint when dragging */}
      {onDrop && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-sm text-slate-400 bg-white/80 px-4 py-2 rounded-full">
            拖拽衣物到此处
          </p>
        </div>
      )}

      {/* Canvas items */}
      <AnimatePresence>
        {items.map((item) => (
          <CanvasItem
            key={item.id}
            id={item.id}
            clothing={item.clothing}
            position={item.position}
            zIndex={item.zIndex}
            isSelected={selectedId === item.id}
            onSelect={() => onSelect(item.id)}
            onMoveUp={() => onMoveUp(item.id)}
            onMoveDown={() => onMoveDown(item.id)}
            onDelete={() => onDelete(item.id)}
            onDragEnd={(pos) => handleDragEndFromChild(item.id, pos)}
          />
        ))}
      </AnimatePresence>

      {/* Empty state */}
      {items.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 flex flex-col items-center justify-center"
        >
          <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <svg
              className="w-10 h-10 text-slate-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
          </div>
          <p className="text-sm text-slate-400">从右侧衣柜添加衣物</p>
        </motion.div>
      )}
    </div>
  );
}
