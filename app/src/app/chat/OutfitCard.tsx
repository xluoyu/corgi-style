"use client";

import React from "react";
import { motion } from "framer-motion";
import { Shirt, Wind, Sparkles, MapPin, Thermometer } from "lucide-react";
import type { OutfitPlan, ClothesItem } from "@/types/chat";

interface OutfitCardProps {
  plan: OutfitPlan;
  clothes: Record<string, ClothesItem>;
  matchScore: number;
  scene?: string;
  temperature?: number;
  city?: string;
  onClothesClick?: (clothes: ClothesItem) => void;
}

const slotNames: Record<string, string> = {
  top: "上装",
  pants: "裤装",
  outer: "外套",
  inner: "内搭",
  accessory: "配饰",
};

const sceneNames: Record<string, string> = {
  daily: "日常",
  work: "职场",
  formal: "正式",
  sport: "运动",
  date: "约会",
  party: "派对",
};

/**
 * OutfitCard - 穿搭卡片组件
 */
export function OutfitCard({
  plan,
  clothes,
  matchScore,
  scene,
  temperature,
  city,
  onClothesClick,
}: OutfitCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white border border-slate-100 rounded-3xl overflow-hidden shadow-sm"
    >
      {/* 头部信息 */}
      <div className="px-4 py-3 bg-gradient-to-r from-slate-50 to-white border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-[#FE8F39]/10 rounded-lg flex items-center justify-center">
              <Sparkles size={14} className="text-[#FE8F39]" />
            </div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              AI 推荐
            </span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-slate-500">
            {city && (
              <div className="flex items-center gap-1">
                <MapPin size={10} />
                <span>{city}</span>
              </div>
            )}
            {temperature !== undefined && (
              <div className="flex items-center gap-1">
                <Thermometer size={10} />
                <span>{temperature}°C</span>
              </div>
            )}
          </div>
        </div>

        {/* 场景标签 */}
        {scene && (
          <div className="inline-flex items-center px-2 py-0.5 bg-amber-50 text-amber-600 text-[10px] font-bold rounded-full">
            {sceneNames[scene] || scene}
          </div>
        )}
      </div>

      {/* 方案描述 */}
      <div className="px-4 py-3">
        <p className="text-[13px] text-slate-700 leading-relaxed">
          {plan.description}
        </p>
      </div>

      {/* 搭配单品 */}
      <div className="px-4 pb-3">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
          搭配单品
        </div>
        <div className="grid grid-cols-1 gap-2">
          {Object.entries(clothes).map(([slot, item]) => {
            if (!item) return null;
            return (
              <button
                key={slot}
                onClick={() => onClothesClick?.(item)}
                className="flex items-center gap-3 p-2.5 bg-slate-50 hover:bg-slate-100 rounded-xl transition-colors text-left"
              >
                <div className="w-10 h-10 bg-white rounded-lg border border-slate-200 flex items-center justify-center overflow-hidden">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.description || item.color}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Shirt size={18} className="text-slate-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold text-[#FE8F39] uppercase">
                      {slotNames[slot] || slot}
                    </span>
                    <span className="text-[10px] text-slate-400">·</span>
                    <span className="text-[11px] font-semibold text-slate-700 truncate">
                      {item.color || "未知"}
                    </span>
                  </div>
                  {item.description && (
                    <p className="text-[10px] text-slate-500 truncate mt-0.5">
                      {item.description}
                    </p>
                  )}
                </div>
                <div className="text-[10px] text-slate-400">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9,18 15,12 9,6" />
                  </svg>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 匹配度 */}
      <div className="px-4 py-3 bg-slate-50 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            匹配度
          </span>
          <div className="flex items-center gap-2">
            <div className="w-20 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${matchScore}%` }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className={`h-full rounded-full ${
                  matchScore >= 80
                    ? "bg-emerald-500"
                    : matchScore >= 60
                    ? "bg-amber-500"
                    : "bg-rose-500"
                }`}
              />
            </div>
            <span
              className={`text-[12px] font-bold ${
                matchScore >= 80
                  ? "text-emerald-600"
                  : matchScore >= 60
                  ? "text-amber-600"
                  : "text-rose-600"
              }`}
            >
              {matchScore}%
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
