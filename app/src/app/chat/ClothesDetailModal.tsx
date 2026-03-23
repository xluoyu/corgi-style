"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Shirt, Calendar, Tag } from "lucide-react";
import type { ClothesItem } from "@/types/chat";

interface ClothesDetailModalProps {
  clothes: ClothesItem | null;
  isOpen: boolean;
  onClose: () => void;
}

const categoryNames: Record<string, string> = {
  top: "上装",
  pants: "裤装",
  outer: "外套",
  inner: "内搭",
  accessory: "配饰",
};

/**
 * ClothesDetailModal - 衣物详情弹窗
 */
export function ClothesDetailModal({
  clothes,
  isOpen,
  onClose,
}: ClothesDetailModalProps) {
  if (!clothes) return null;

  const tags = clothes.tags || {};

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
          />

          {/* 弹窗 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
            className="fixed inset-x-4 bottom-0 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-96 bg-white rounded-3xl shadow-xl z-50 overflow-hidden"
          >
            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 w-8 h-8 bg-slate-100 hover:bg-slate-200 rounded-full flex items-center justify-center transition-colors z-10"
            >
              <X size={16} className="text-slate-500" />
            </button>

            {/* 图片区 */}
            <div className="relative h-48 bg-slate-100">
              {clothes.image_url ? (
                <img
                  src={clothes.image_url}
                  alt={clothes.description || clothes.color}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Shirt size={48} className="text-slate-300" />
                </div>
              )}

              {/* 品类标签 */}
              <div className="absolute top-3 left-3">
                <span className="px-2.5 py-1 bg-white/90 backdrop-blur-sm text-[11px] font-bold text-slate-700 rounded-full shadow-sm">
                  {categoryNames[clothes.category] || clothes.category}
                </span>
              </div>
            </div>

            {/* 信息区 */}
            <div className="p-4 space-y-4">
              {/* 基础信息 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    颜色
                  </span>
                  <span className="text-[13px] font-semibold text-slate-700">
                    {clothes.color || "未知"}
                  </span>
                </div>

                {clothes.description && (
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      描述
                    </span>
                    <span className="text-[13px] text-slate-600">
                      {clothes.description}
                    </span>
                  </div>
                )}

                {clothes.wear_count !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      穿着次数
                    </span>
                    <span className="text-[13px] text-slate-600">
                      {clothes.wear_count} 次
                    </span>
                  </div>
                )}
              </div>

              {/* 风格标签 */}
              {tags.styles && tags.styles.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    <Tag size={10} />
                    风格
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {tags.styles.map((style, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] rounded-full"
                      >
                        {style}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 适用季节 */}
              {tags.seasons && tags.seasons.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    <Calendar size={10} />
                    适用季节
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {tags.seasons.map((season, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-amber-50 text-amber-600 text-[11px] rounded-full"
                      >
                        {season}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 适用场合 */}
              {tags.occasions && tags.occasions.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    <Calendar size={10} />
                    适用场合
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {tags.occasions.map((occasion, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-blue-50 text-blue-600 text-[11px] rounded-full"
                      >
                        {occasion}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
