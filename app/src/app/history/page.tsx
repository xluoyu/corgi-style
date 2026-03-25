"use client";

import React, { useState, useEffect } from "react";
import { Calendar, Filter, RefreshCw, MapPin, Cloud, Sun, CloudRain, Snowflake, Thermometer } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { BottomNav } from "@/components/BottomNav";
import { generateTodayOutfit } from "@/lib/api";
import type { GenerateOutfitResponse } from "@/types/api";

/**
 * 穿搭记录接口
 */
interface OutfitHistoryItem {
  id: string;
  date: string;
  temperature: number;
  city: string;
  weather: string;
  scene: string;
  clothes: {
    id: string;
    image_url: string;
    category: string;
    color: string;
  }[];
  description: string;
  match_score?: number;
  feedback?: "like" | "dislike" | "neutral";
}

/**
 * Mock 穿搭历史数据
 */
const mockOutfitHistory: OutfitHistoryItem[] = [
  {
    id: "1",
    date: "2024-03-22",
    temperature: 18,
    city: "上海",
    weather: "晴朗",
    scene: "daily",
    clothes: [
      {
        id: "1",
        image_url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=300&h=300&fit=crop",
        category: "top",
        color: "白色"
      },
      {
        id: "2",
        image_url: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=300&h=300&fit=crop",
        category: "bottom",
        color: "黑色"
      }
    ],
    description: "简约休闲风格，白色T恤搭配黑色牛仔裤，适合日常穿着",
    match_score: 92
  },
  {
    id: "2",
    date: "2024-03-21",
    temperature: 15,
    city: "上海",
    weather: "多云",
    scene: "work",
    clothes: [
      {
        id: "3",
        image_url: "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=300&h=300&fit=crop",
        category: "outerwear",
        color: "灰色"
      },
      {
        id: "4",
        image_url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=300&h=300&fit=crop",
        category: "top",
        color: "蓝色"
      },
      {
        id: "5",
        image_url: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=300&h=300&fit=crop",
        category: "bottom",
        color: "卡其色"
      }
    ],
    description: "职场正装，灰色西装外套搭配蓝色衬衫和卡其色西裤",
    match_score: 88,
    feedback: "like"
  },
  {
    id: "3",
    date: "2024-03-20",
    temperature: 22,
    city: "上海",
    weather: "晴朗",
    scene: "date",
    clothes: [
      {
        id: "6",
        image_url: "https://images.unsplash.com/photo-1598554747436-c9293d6a588f?w=300&h=300&fit=crop",
        category: "top",
        color: "粉色"
      },
      {
        id: "7",
        image_url: "https://images.unsplash.com/photo-1584370848010-d7cc6374d6aa?w=300&h=300&fit=crop",
        category: "bottom",
        color: "白色"
      }
    ],
    description: "约会甜美风，粉色连衣裙搭配白色小包",
    match_score: 95,
    feedback: "like"
  },
  {
    id: "4",
    date: "2024-03-19",
    temperature: 12,
    city: "上海",
    weather: "小雨",
    scene: "daily",
    clothes: [
      {
        id: "8",
        image_url: "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=300&h=300&fit=crop",
        category: "outerwear",
        color: "深蓝色"
      },
      {
        id: "9",
        image_url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=300&h=300&fit=crop",
        category: "top",
        color: "白色"
      },
      {
        id: "10",
        image_url: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=300&h=300&fit=crop",
        category: "bottom",
        color: "黑色"
      }
    ],
    description: "雨天穿搭，深蓝色风衣保暖防风",
    match_score: 85,
    feedback: "neutral"
  },
  {
    id: "5",
    date: "2024-03-18",
    temperature: 20,
    city: "上海",
    weather: "多云",
    scene: "sport",
    clothes: [
      {
        id: "11",
        image_url: "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=300&h=300&fit=crop",
        category: "top",
        color: "红色"
      },
      {
        id: "12",
        image_url: "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=300&h=300&fit=crop",
        category: "bottom",
        color: "黑色"
      }
    ],
    description: "运动健身风格，红色运动衫搭配黑色运动裤",
    match_score: 90
  }
];

/**
 * WeatherIcon - 天气图标组件
 */
function WeatherIcon({ weather }: { weather: string }) {
  const icons: Record<string, React.ReactNode> = {
    "晴朗": <Sun size={20} className="text-[#FE8F39]" />,
    "多云": <Cloud size={20} className="text-slate-400" />,
    "小雨": <CloudRain size={20} className="text-blue-400" />,
    "大雪": <Snowflake size={20} className="text-blue-300" />
  };
  return icons[weather] || <Cloud size={20} className="text-slate-400" />;
}

/**
 * HistoryPage - 穿搭历史页面
 */
export default function HistoryPage() {
  const [outfitHistory, setOutfitHistory] = useState<OutfitHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [showFilter, setShowFilter] = useState(false);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);

  useEffect(() => {
    // 加载穿搭历史数据
    // TODO: 替换为实际的 API 调用
    // fetchOutfitHistory();
    setOutfitHistory(mockOutfitHistory);
    setLoading(false);
  }, []);

  /**
   * 根据日期筛选穿搭记录
   */
  const filteredHistory = selectedDate
    ? outfitHistory.filter(item => item.date === selectedDate)
    : outfitHistory;

  /**
   * 获取所有可用日期
   */
  const availableDates = Array.from(new Set(outfitHistory.map(item => item.date)));

  /**
   * 重新推荐穿搭
   */
  const handleRegenerate = async (item: OutfitHistoryItem) => {
    setRegeneratingId(item.id);

    try {
      // 使用 API 重新生成穿搭
      const response = await generateTodayOutfit(
        item.city,
        item.temperature,
        item.scene as any
      );

      // 更新历史记录
      const updatedHistory = outfitHistory.map(outfit => {
        if (outfit.id === item.id) {
          return {
            ...outfit,
            clothes: response.outfit_items.map(item => ({
              id: item.slot,
              image_url: "",
              category: item.slot,
              color: item.color
            })),
            description: response.description,
            match_score: 0
          };
        }
        return outfit;
      });

      setOutfitHistory(updatedHistory);
    } catch (error) {
      console.error("重新推荐失败:", error);
    } finally {
      setRegeneratingId(null);
    }
  };

  /**
   * 切换筛选面板
   */
  const toggleFilter = () => {
    setShowFilter(!showFilter);
  };

  /**
   * 格式化日期显示
   */
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateStr === today.toISOString().split('T')[0]) {
      return "今天";
    } else if (dateStr === yesterday.toISOString().split('T')[0]) {
      return "昨天";
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' });
    }
  };

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-1/3 bg-gradient-to-b from-rose-100/20 to-transparent pointer-events-none z-0" />

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="px-5 pt-6 pb-4">
          <header className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">穿搭历史</h1>
              <p className="text-xs text-slate-500 mt-1">查看您的穿搭记录</p>
            </div>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={toggleFilter}
              className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all ${
                showFilter
                  ? "bg-[#FE8F39] text-white border-[#FE8F39]"
                  : "bg-white text-slate-600 border-slate-200"
              }`}
            >
              <Filter size={16} />
              <span className="text-xs font-bold">筛选</span>
            </motion.button>
          </header>

          <AnimatePresence>
            {showFilter && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4"
              >
                <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Calendar size={16} className="text-[#FE8F39]" />
                    <span className="text-sm font-bold text-slate-800">选择日期</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setSelectedDate(null)}
                      className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                        selectedDate === null
                          ? "bg-[#FE8F39] text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      全部
                    </motion.button>
                    {availableDates.map(date => (
                      <motion.button
                        key={date}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setSelectedDate(date)}
                        className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                          selectedDate === date
                            ? "bg-[#FE8F39] text-white"
                            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                        }`}
                      >
                        {formatDate(date)}
                      </motion.button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="px-5 pb-4">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin text-[#FE8F39]">
                <RefreshCw size={32} />
              </div>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="text-center py-20">
              <Calendar size={48} className="text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-500">暂无穿搭记录</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredHistory.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-3xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center">
                        <Calendar size={16} className="text-[#FE8F39]" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900">{formatDate(item.date)}</p>
                        <p className="text-[10px] text-slate-400">{item.date}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 bg-slate-50 px-2 py-1 rounded-full">
                        <WeatherIcon weather={item.weather} />
                        <span className="text-[10px] font-bold text-slate-600">{item.weather}</span>
                      </div>
                      <div className="flex items-center gap-1 bg-slate-50 px-2 py-1 rounded-full">
                        <Thermometer size={12} className="text-slate-500" />
                        <span className="text-[10px] font-bold text-slate-600">{item.temperature}°C</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2 mb-3">
                    <div className="flex items-center gap-1 bg-slate-50 px-2 py-1 rounded-full">
                      <MapPin size={12} className="text-slate-500" />
                      <span className="text-[10px] font-bold text-slate-600">{item.city}</span>
                    </div>
                    <div className="bg-[#FE8F39]/10 px-2 py-1 rounded-full">
                      <span className="text-[10px] font-bold text-[#FE8F39]">
                        {item.scene === "daily" ? "日常" :
                         item.scene === "work" ? "职场" :
                         item.scene === "date" ? "约会" :
                         item.scene === "sport" ? "运动" :
                         item.scene === "formal" ? "正式" :
                         item.scene === "party" ? "派对" : item.scene}
                      </span>
                    </div>
                    {item.match_score && (
                      <div className="bg-emerald-50 px-2 py-1 rounded-full">
                        <span className="text-[10px] font-bold text-emerald-600">
                          匹配度 {item.match_score}%
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    {item.clothes.map(clothes => (
                      <div
                        key={clothes.id}
                        className="relative aspect-square rounded-xl overflow-hidden bg-slate-100"
                      >
                        <img
                          src={clothes.image_url}
                          alt={clothes.category}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-1.5">
                          <p className="text-[9px] font-bold text-white truncate">
                            {clothes.color} {clothes.category}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <p className="text-xs text-slate-600 mb-3 line-clamp-2">
                    {item.description}
                  </p>

                  <div className="flex justify-between items-center pt-3 border-t border-slate-100">
                    <div className="flex gap-2">
                      {item.feedback === "like" && (
                        <div className="flex items-center gap-1 text-emerald-500">
                          <span className="text-[10px] font-bold">喜欢</span>
                        </div>
                      )}
                      {item.feedback === "dislike" && (
                        <div className="flex items-center gap-1 text-red-500">
                          <span className="text-[10px] font-bold">不喜欢</span>
                        </div>
                      )}
                    </div>

                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleRegenerate(item)}
                      disabled={regeneratingId === item.id}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                        regeneratingId === item.id
                          ? "bg-slate-100 text-slate-400"
                          : "bg-[#FE8F39]/10 text-[#FE8F39] hover:bg-[#FE8F39]/20"
                      }`}
                    >
                      {regeneratingId === item.id ? (
                        <>
                          <RefreshCw size={12} className="animate-spin" />
                          <span>生成中...</span>
                        </>
                      ) : (
                        <>
                          <RefreshCw size={12} />
                          <span>重新推荐</span>
                        </>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
