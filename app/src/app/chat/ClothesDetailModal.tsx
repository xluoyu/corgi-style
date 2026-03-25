"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Shirt, Calendar, Tag, Layers, MapPin } from "lucide-react";
import type { ClothesItem } from "@/types/chat";

interface WardrobeClothesItem {
  id: string;
  name: string;
  categoryLabel: string;
  color: string;
  colorLabel: string;
  imageUrl: string;
  material?: string;
  temperatureRange?: string;
  temperatureRangeLabel?: string;
  wearMethod?: string;
  wearMethodLabel?: string;
  scene?: string;
  sceneLabel?: string;
  analysisCompleted: boolean;
  generatedCompleted: boolean;
  wearCount: number;
  createdAt: string;
  raw: Record<string, unknown>;
}

type ClothesDetailData = WardrobeClothesItem | ClothesItem;

interface ClothesDetailModalProps {
  clothes: ClothesDetailData | null;
  isOpen: boolean;
  onClose: () => void;
}

function InfoRow({ label, value, icon }: { label: string; value?: string; icon?: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-slate-400">{icon}</span>}
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-sm font-medium text-slate-700">{value}</span>
    </div>
  );
}

/**
 * ClothesDetailModal - 衣物详情弹窗（衣橱版）
 */
export function ClothesDetailModal({ clothes, isOpen, onClose }: ClothesDetailModalProps) {
  if (!clothes) return null;

  const isWardrobeItem = 'categoryLabel' in clothes;
  const name = isWardrobeItem ? (clothes as WardrobeClothesItem).name : (clothes as ClothesItem).description || "未知衣物";
  const categoryLabel = isWardrobeItem ? (clothes as WardrobeClothesItem).categoryLabel : (clothes as ClothesItem).category || "-";
  const colorLabel = isWardrobeItem ? (clothes as WardrobeClothesItem).colorLabel : (clothes as ClothesItem).color || "-";
  const imageUrl = isWardrobeItem ? (clothes as WardrobeClothesItem).imageUrl : (clothes as ClothesItem).image_url;
  const wearCount = isWardrobeItem ? (clothes as WardrobeClothesItem).wearCount : (clothes as ClothesItem).wear_count || 0;
  const generatedCompleted = isWardrobeItem ? (clothes as WardrobeClothesItem).generatedCompleted : false;
  const createdAt = isWardrobeItem ? (clothes as WardrobeClothesItem).createdAt : "-";
  const analysisCompleted = isWardrobeItem ? (clothes as WardrobeClothesItem).analysisCompleted : false;

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
            initial={{ opacity: 0, scale: 0.9, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 40 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
            className="fixed inset-x-4 bottom-0 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[22rem] bg-white rounded-3xl shadow-xl z-50 overflow-hidden"
          >
            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 w-8 h-8 bg-black/10 hover:bg-black/20 rounded-full flex items-center justify-center transition-colors z-10"
            >
              <X size={16} className="text-slate-600" />
            </button>

            {/* 图片区 */}
            <div className="relative h-56 bg-slate-100">
              {imageUrl ? (
                <img
                  src={imageUrl}
                  alt={name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Shirt size={56} className="text-slate-300" />
                </div>
              )}
              {/* 品类标签 */}
              <div className="absolute top-3 left-3">
                <span className="px-2.5 py-1 bg-white/90 backdrop-blur-sm text-[11px] font-bold text-slate-700 rounded-full shadow-sm">
                  {categoryLabel}
                </span>
              </div>
              {/* 商品图标识 */}
              {generatedCompleted && (
                <div className="absolute bottom-3 left-3">
                  <span className="px-2 py-0.5 bg-[#FE8F39]/90 text-white text-[10px] font-bold rounded-full">
                    商品图
                  </span>
                </div>
              )}
            </div>

            {/* 信息区 */}
            <div className="p-4">
              {/* 衣物名称 */}
              <h2 className="text-base font-bold text-slate-800 mb-4">{name}</h2>

              {/* 基础属性列表 */}
              <div className="space-y-0">
                <InfoRow label="颜色" value={colorLabel} />
                <InfoRow
                  label="适合季节"
                  value={isWardrobeItem ? (clothes as WardrobeClothesItem).temperatureRangeLabel : undefined}
                  icon={<Calendar size={12} />}
                />
                <InfoRow
                  label="穿着方式"
                  value={isWardrobeItem ? (clothes as WardrobeClothesItem).wearMethodLabel : undefined}
                  icon={<Layers size={12} />}
                />
                <InfoRow
                  label="适用场合"
                  value={isWardrobeItem ? (clothes as WardrobeClothesItem).sceneLabel : undefined}
                  icon={<MapPin size={12} />}
                />
                <InfoRow label="穿着次数" value={`${wearCount} 次`} />
              </div>

              {/* 底部信息栏 */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Calendar size={12} />
                  <span>添加于 {createdAt}</span>
                </div>
                {analysisCompleted ? (
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 text-[10px] font-bold rounded-full">
                    已识别
                  </span>
                ) : (
                  <span className="px-2 py-0.5 bg-amber-50 text-amber-600 text-[10px] font-bold rounded-full">
                    识别中
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
