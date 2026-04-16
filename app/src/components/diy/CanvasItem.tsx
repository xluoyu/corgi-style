'use client';

import { useRef } from 'react';
import { motion } from 'framer-motion';
import { ChevronUp, ChevronDown, X } from 'lucide-react';
import type { SlotClothing } from '@/types/diy';

interface CanvasItemProps {
  id: string;
  clothing: SlotClothing;
  position: { x: number; y: number };
  zIndex: number;
  isSelected: boolean;
  onSelect: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
  onDragEnd: (position: { x: number; y: number }) => void;
}

export function CanvasItem({
  id,
  clothing,
  position,
  zIndex,
  isSelected,
  onSelect,
  onMoveUp,
  onMoveDown,
  onDelete,
  onDragEnd,
}: CanvasItemProps) {
  const itemRef = useRef<HTMLDivElement>(null);

  return (
    <motion.div
      ref={itemRef}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      drag
      dragMomentum={false}
      dragListener={false}
      onDragEnd={(_, info) => {
        // Calculate new position based on drag delta
        const newX = position.x + info.offset.x;
        const newY = position.y + info.offset.y;
        onDragEnd({ x: newX, y: newY });
      }}
      className={`
        absolute cursor-grab active:cursor-grabbing
        rounded-xl overflow-hidden shadow-md
        transition-all duration-200
        ${isSelected
          ? 'ring-2 ring-[#FE8F39] shadow-lg'
          : 'ring-1 ring-white/50 hover:ring-2 hover:ring-[#FE8F39]/50'
        }
      `}
      style={{
        left: position.x,
        top: position.y,
        zIndex,
        width: 90,
        height: 110,
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
    >
      {/* Image */}
      <div className="w-full h-full bg-slate-100">
        <img
          src={clothing.imageUrl}
          alt={clothing.name}
          className="w-full h-full object-cover pointer-events-none"
          draggable={false}
        />
      </div>

      {/* Selected controls */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="absolute -top-10 left-1/2 -translate-x-1/2 flex items-center gap-0.5 bg-white rounded-full shadow-lg px-1.5 py-1"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMoveUp();
            }}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 transition-colors"
            title="上移一层"
          >
            <ChevronUp className="w-4 h-4 text-slate-600" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMoveDown();
            }}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 transition-colors"
            title="下移一层"
          >
            <ChevronDown className="w-4 h-4 text-slate-600" />
          </button>
          <div className="w-px h-4 bg-slate-200 mx-0.5" />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-red-50 transition-colors"
            title="删除"
          >
            <X className="w-4 h-4 text-red-500" />
          </button>
        </motion.div>
      )}

      {/* Layer indicator */}
      {!isSelected && (
        <div className="absolute bottom-1 right-1 w-4 h-4 bg-black/50 rounded-full flex items-center justify-center">
          <span className="text-[8px] text-white font-bold">{zIndex}</span>
        </div>
      )}
    </motion.div>
  );
}
