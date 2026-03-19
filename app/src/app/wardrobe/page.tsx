"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { Shirt, Wind, Crown, Sparkles, Watch } from "lucide-react";
import { BottomNav } from "@/components/BottomNav";

type CategoryType = "all" | "top" | "bottom" | "outer" | "inner" | "accessory";

interface ClothingItem {
  id: number;
  name: string;
  category: CategoryType;
  color: string;
  imageUrl: string;
}

const mockClothingData: ClothingItem[] = [
  {
    id: 1,
    name: "白色棉质T恤",
    category: "top",
    color: "白色",
    imageUrl: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=500&fit=crop",
  },
  {
    id: 2,
    name: "深蓝色牛仔裤",
    category: "bottom",
    color: "深蓝色",
    imageUrl: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop",
  },
  {
    id: 3,
    name: "灰色休闲西装",
    category: "outer",
    color: "灰色",
    imageUrl: "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop",
  },
  {
    id: 4,
    name: "粉色针织衫",
    category: "inner",
    color: "粉色",
    imageUrl: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=500&fit=crop",
  },
  {
    id: 5,
    name: "黑色皮质手表",
    category: "accessory",
    color: "黑色",
    imageUrl: "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=500&fit=crop",
  },
  {
    id: 6,
    name: "条纹衬衫",
    category: "top",
    color: "蓝白条纹",
    imageUrl: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop",
  },
  {
    id: 7,
    name: "卡其色工装裤",
    category: "bottom",
    color: "卡其色",
    imageUrl: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&h=500&fit=crop",
  },
  {
    id: 8,
    name: "黑色风衣",
    category: "outer",
    color: "黑色",
    imageUrl: "https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=400&h=500&fit=crop",
  },
  {
    id: 9,
    name: "白色打底衫",
    category: "inner",
    color: "白色",
    imageUrl: "https://images.unsplash.com/photo-1485218126466-34e6392ec754?w=400&h=500&fit=crop",
  },
  {
    id: 10,
    name: "银色项链",
    category: "accessory",
    color: "银色",
    imageUrl: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=500&fit=crop",
  },
  {
    id: 11,
    name: "藏青色Polo衫",
    category: "top",
    color: "藏青色",
    imageUrl: "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&h=500&fit=crop",
  },
  {
    id: 12,
    name: "棕色皮带",
    category: "accessory",
    color: "棕色",
    imageUrl: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=500&fit=crop",
  },
];

const categoryLabels: Record<CategoryType, string> = {
  all: "全部",
  top: "上衣",
  bottom: "裤子",
  outer: "外套",
  inner: "内搭",
  accessory: "配饰",
};

const categoryIcons: Record<CategoryType, React.ReactNode> = {
  all: <Shirt size={16} />,
  top: <Shirt size={16} />,
  bottom: <Wind size={16} />,
  outer: <Crown size={16} />,
  inner: <Sparkles size={16} />,
  accessory: <Watch size={16} />,
};

/**
 * WardrobePage - 衣柜页面组件
 * 展示用户的衣物列表，支持分类筛选
 */
export default function WardrobePage() {
  const [activeCategory, setActiveCategory] = useState<CategoryType>("all");

  const filteredClothes =
    activeCategory === "all"
      ? mockClothingData
      : mockClothingData.filter((item) => item.category === activeCategory);

  const categories: CategoryType[] = ["all", "top", "bottom", "outer", "inner", "accessory"];

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-blue-100/30 to-transparent pointer-events-none z-0" />

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="flex flex-col h-full">
          <div className="px-5 pt-4 pb-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center">
                <Shirt size={18} className="text-[#FE8F39]" />
              </div>
              <h1 className="text-lg font-bold text-slate-900">我的衣柜</h1>
              <span className="ml-auto text-xs font-medium text-slate-400">
                {filteredClothes.length} 件衣物
              </span>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {categories.map((cat) => (
                <motion.button
                  key={cat}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setActiveCategory(cat)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    activeCategory === cat
                      ? "bg-[#FE8F39] text-white shadow-lg shadow-[#FE8F39]/20"
                      : "bg-white text-slate-600 border border-slate-100"
                  }`}
                >
                  {categoryIcons[cat]}
                  {categoryLabels[cat]}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-5 pb-6">
            <div className="grid grid-cols-2 gap-3">
              {filteredClothes.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100"
                >
                  <div className="aspect-[3/4] relative overflow-hidden">
                    <img src={item.imageUrl} alt={item.name} className="w-full h-full object-cover" />
                    <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-lg">
                      <span className="text-[10px] font-bold text-slate-700">{item.color}</span>
                    </div>
                  </div>
                  <div className="p-3">
                    <h3 className="text-sm font-bold text-slate-800 truncate">{item.name}</h3>
                    <p className="text-[10px] text-slate-400 mt-0.5">{categoryLabels[item.category]}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
