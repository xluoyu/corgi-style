"use client";

import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Shirt, Wind, Crown, Sparkles, Watch } from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { getClothesList } from "@/lib/api";

type CategoryType = "all" | "top" | "bottom" | "outer" | "inner" | "accessory";

interface ClothingItem {
  id: number;
  name: string;
  category: CategoryType;
  color: string;
  imageUrl: string;
  analysisCompleted: boolean;
  generatedCompleted: boolean;
}

interface ApiClothingItem {
  id: number;
  user_id: string;
  image_url: string;
  category: string;
  color: string;
  material?: string;
  temperature_range: string;
  scene?: string;
  wear_method?: string;
  brand?: string;
  description?: string;
  generated_image_url?: string;
  analysis_completed: number;
  generated_completed: number;
  create_time: string;
}

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
  const [clothingData, setClothingData] = useState<ClothingItem[]>([]);

  // 获取衣物列表
  const fetchClothingList = async () => {
    try {
      const response = await getClothesList();
      if (response.clothes && response.clothes.length > 0) {
        const formattedClothes: ClothingItem[] = (response.clothes as ApiClothingItem[]).map((item) => ({
          id: item.id,
          name: item.description || "未命名",
          category: mapCategory(item.category),
          color: item.color,
          imageUrl: item.generated_image_url || item.image_url,
          analysisCompleted: item.analysis_completed === 1,
          generatedCompleted: item.generated_completed === 1,
        }));
        setClothingData(formattedClothes);
      }
    } catch (error) {
      console.error("获取衣物列表失败:", error);
    }
  };

  // 组件挂载时获取衣物列表
  useEffect(() => {
    fetchClothingList();
  }, []);

  const filteredClothes =
    activeCategory === "all"
      ? clothingData
      : clothingData.filter((item) => item.category === activeCategory);

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
            {filteredClothes.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <Shirt size={48} className="mb-4 opacity-50" />
                <p className="text-sm">暂无衣物</p>
                <p className="text-xs mt-1">点击底部 + 按钮上传衣物</p>
              </div>
            ) : (
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
                      {!item.analysisCompleted && (
                        <div className="absolute top-2 right-2">
                          <span className="bg-[#FE8F39] text-white px-2 py-1 rounded-full text-[10px] font-bold shadow-lg">
                            识别中...
                          </span>
                        </div>
                      )}
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
            )}
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}

/**
 * 映射后端类别到前端类别
 */
function mapCategory(category: string): CategoryType {
  const categoryMap: Record<string, CategoryType> = {
    top: "top",
    pants: "bottom",
    bottom: "bottom",
    outer: "outer",
    outerwear: "outer",
    inner: "inner",
    accessory: "accessory",
  };
  return categoryMap[category] || "top";
}
