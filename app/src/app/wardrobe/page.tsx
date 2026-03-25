"use client";

import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Shirt, Wind, Crown, Sparkles, Watch, Thermometer } from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { getClothesList } from "@/lib/api";
import { ClothesDetailModal } from "@/app/chat/ClothesDetailModal";

type CategoryType = "all" | "top" | "pants" | "outer" | "inner" | "accessory";

// 后端返回的原始衣物数据
interface ApiClothingItem {
  id: string;
  user_id: string;
  image_url: string;
  name?: string;
  category: string;
  color: string;
  material?: string;
  temperature_range?: string;
  wear_method?: string;
  scene?: string;
  generated_image_url?: string;
  analysis_completed: number;
  generated_completed: number;
  wear_count?: number;
  created_at: string;
}

// 页面内部使用的衣物数据
interface ClothingItem {
  id: string;
  name: string;
  category: CategoryType;
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
  raw: ApiClothingItem;
}

const categoryLabels: Record<CategoryType, string> = {
  all: "全部",
  top: "上衣",
  pants: "裤子",
  outer: "外套",
  inner: "内搭",
  accessory: "配饰",
};

const categoryIcons: Record<CategoryType, React.ReactNode> = {
  all: <Shirt size={16} />,
  top: <Shirt size={16} />,
  pants: <Wind size={16} />,
  outer: <Crown size={16} />,
  inner: <Sparkles size={16} />,
  accessory: <Watch size={16} />,
};

const temperatureLabels: Record<string, string> = {
  summer: "夏季",
  spring_autumn: "春秋",
  winter: "冬季",
  all_season: "四季",
};

const colorLabels: Record<string, string> = {
  black: "黑色",
  white: "白色",
  red: "红色",
  blue: "蓝色",
  gray: "灰色",
  beige: "米色",
  brown: "棕色",
  green: "绿色",
  purple: "紫色",
  navy: "藏青色",
  other: "其他",
};

const sceneLabels: Record<string, string> = {
  daily: "日常",
  work: "工作",
  sport: "运动",
  date: "约会",
  party: "聚会",
};

const wearMethodLabels: Record<string, string> = {
  inner_wear: "内穿",
  outer_wear: "外穿",
  single_wear: "单穿",
  layering: "叠穿",
};

function mapCategory(category: string): CategoryType {
  const map: Record<string, CategoryType> = {
    top: "top",
    pants: "pants",
    bottom: "pants",
    outer: "outer",
    outerwear: "outer",
    inner: "inner",
    accessory: "accessory",
  };
  return map[category] || "top";
}

function formatDate(isoString: string): string {
  try {
    const d = new Date(isoString);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  } catch {
    return isoString;
  }
}

export default function WardrobePage() {
  const [activeCategory, setActiveCategory] = useState<CategoryType>("all");
  const [clothingData, setClothingData] = useState<ClothingItem[]>([]);
  const [selectedClothes, setSelectedClothes] = useState<ClothingItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchClothingList = async () => {
    try {
      const response = await getClothesList();
      if (response.clothes && (response.clothes as ApiClothingItem[]).length > 0) {
        const formatted: ClothingItem[] = (response.clothes as ApiClothingItem[]).map((item) => ({
          id: item.id,
          name: item.name || "未命名衣物",
          category: mapCategory(item.category),
          categoryLabel: categoryLabels[mapCategory(item.category)],
          color: item.color || "unknown",
          colorLabel: colorLabels[item.color] || item.color || "未知",
          imageUrl: item.generated_image_url || item.image_url || "",
          material: item.material,
          temperatureRange: item.temperature_range,
          temperatureRangeLabel: item.temperature_range ? temperatureLabels[item.temperature_range] || item.temperature_range || "" : "",
          wearMethod: item.wear_method,
          wearMethodLabel: item.wear_method ? wearMethodLabels[item.wear_method] || item.wear_method || "" : "",
          scene: item.scene,
          sceneLabel: item.scene ? sceneLabels[item.scene] || item.scene || "" : "",
          analysisCompleted: item.analysis_completed === 1,
          generatedCompleted: item.generated_completed === 1,
          wearCount: item.wear_count || 0,
          createdAt: formatDate(item.created_at),
          raw: item,
        }));
        setClothingData(formatted);
      } else {
        setClothingData([]);
      }
    } catch (error) {
      console.error("获取衣物列表失败:", error);
    }
  };

  useEffect(() => {
    fetchClothingList();
  }, []);

  const filteredClothes =
    activeCategory === "all"
      ? clothingData
      : clothingData.filter((item) => item.category === activeCategory);

  // 根据真实数据动态生成分类标签
  const presentCategories: CategoryType[] = ["all", ...new Set(clothingData.map((c) => c.category))];

  const handleCardClick = (item: ClothingItem) => {
    setSelectedClothes(item);
    setModalOpen(true);
  };

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
              {presentCategories.map((cat) => (
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
                    className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100 cursor-pointer"
                    onClick={() => handleCardClick(item)}
                  >
                    <div className="aspect-[3/4] relative overflow-hidden">
                      {item.imageUrl ? (
                        <img src={item.imageUrl} alt={item.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-slate-100">
                          <Shirt size={40} className="text-slate-300" />
                        </div>
                      )}
                      {item.temperatureRangeLabel && (
                        <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-lg flex items-center gap-1">
                          <Thermometer size={10} className="text-[#FE8F39]" />
                          <span className="text-[10px] font-bold text-slate-700">{item.temperatureRangeLabel}</span>
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h3 className="text-sm font-bold text-slate-800 truncate">{item.name}</h3>
                      <div className="flex items-center justify-between mt-0.5">
                        <p className="text-[10px] text-slate-400">{item.categoryLabel}</p>
                        {item.colorLabel && item.colorLabel !== "未知" && (
                          <span className="text-[10px] text-slate-400">{item.colorLabel}</span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      <BottomNav />

      {selectedClothes && (
        <ClothesDetailModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          clothes={selectedClothes}
        />
      )}
    </div>
  );
}
