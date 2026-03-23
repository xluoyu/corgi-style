"use client";

import React, { useState, useEffect } from "react";
import { Sun, MapPin, Cloud, Sparkles, CloudRain, CloudSnow, CloudFog, Wind, CloudLightning, Thermometer, HelpCircle, RefreshCw } from "lucide-react";
import { motion } from "motion/react";
import { BookOpen, Palette, Wand2, Camera, LayoutGrid, Loader2, AlertCircle } from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { useWeather, getWeatherIconName } from "@/hooks/useWeather";
import { generateTodayOutfit, refreshOutfit } from "@/lib/api";
import type { GenerateOutfitResponse } from "@/types/api";

/**
 * HomePage - 首页组件
 * 展示天气信息、穿衣指南、功能入口和今日推荐
 */
export default function HomePage() {
  const heroImage =
    "https://images.unsplash.com/photo-1700557478776-952a33fda578?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWxlJTIwc3RyZWV0JTIwc3R5bGUlMjBvdXRmaXR8ZW58MXx8fHwxNzcyncsdlNTE3MDJ8MA&ixlib=rb-4-1.0&q=80&w=1080";
  const todayHighlightRef = React.useRef<{ refresh: () => void }>(null);

  const handleRefreshOutfit = () => {
    todayHighlightRef.current?.refresh();
  };

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-blue-100/30 to-transparent pointer-events-none z-0" />

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="px-5 pt-4 pb-4 flex flex-col gap-4">
          <WeatherHeader />
          <ClothingGuide />
        </div>

        <div className="flex-1 bg-white rounded-t-[40px] shadow-[0_-12px_48px_rgba(15,23,42,0.08)] px-5 pt-8 flex flex-col gap-6 overflow-hidden">
          <section>
            <FeatureGrid />
          </section>

          <section className="flex-1 flex flex-col min-h-0 mb-6">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                今日主打推荐
              </h2>
              <button
                onClick={handleRefreshOutfit}
                className="text-[10px] font-bold text-[#FE8F39] hover:bg-orange-50 px-2.5 py-1 rounded-full transition-colors border border-orange-100"
              >
                换一批
              </button>
            </div>
            <TodayHighlight imageUrl={heroImage} ref={todayHighlightRef} />
          </section>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}

/**
 * getWeatherIconComponent - 根据图标名称获取对应的 Lucide 图标组件
 * @param iconName - 图标名称
 * @returns Lucide 图标组件
 */
function getWeatherIconComponent(iconName: string) {
  const icons: Record<string, React.ReactNode> = {
    Sun: <Sun size={24} className="text-[#FE8F39]" />,
    Cloud: <Cloud size={24} className="text-slate-400" />,
    CloudRain: <CloudRain size={24} className="text-blue-400" />,
    CloudSnow: <CloudSnow size={24} className="text-blue-300" />,
    CloudFog: <CloudFog size={24} className="text-slate-400" />,
    CloudLightning: <CloudLightning size={24} className="text-yellow-500" />,
    Wind: <Wind size={24} className="text-slate-500" />,
    Thermometer: <Thermometer size={24} className="text-red-400" />,
    HelpCircle: <HelpCircle size={24} className="text-slate-400" />,
  };
  return icons[iconName] || icons.Sun;
}

/**
 * getWeatherDescription - 根据温度和天气状况生成穿衣建议
 * @param temp - 温度
 * @param weatherText - 天气状况描述
 * @returns 穿衣建议文本
 */
function getWeatherDescription(temp: number, weatherText: string): string {
  if (temp >= 30) {
    return `今日${weatherText}，气温炎热。建议选择<span className="text-[#FE8F39] font-bold">轻薄透气</span>的棉麻或真丝材质，以<span className="text-[#FE8F39] font-bold">浅色系</span>为主，注意防晒降温。`;
  } else if (temp >= 25) {
    return `今日${weatherText}，气温温暖。建议选择<span className="text-[#FE8F39] font-bold">清爽透气</span>的短袖或薄衬衫，可外搭薄款防晒衫，颜色以<span className="text-[#FE8F39] font-bold">清爽色系</span>为佳。`;
  } else if (temp >= 20) {
    return `今日${weatherText}，气温舒适宜人。建议采用<span className="text-[#FE8F39] font-bold">层次穿搭</span>，内搭薄针织或衬衫，外搭轻薄外套，方便随时增减。`;
  } else if (temp >= 15) {
    return `今日${weatherText}，气温温和。建议<span className="text-[#FE8F39] font-bold">长袖+薄外套</span>的组合，早晚温差较大时可加一件开衫或风衣。`;
  } else if (temp >= 10) {
    return `今日${weatherText}，气温偏凉。建议选择<span className="text-[#FE8F39] font-bold">毛衣或卫衣</span>搭配外套，注意<span className="text-[#FE8F39] font-bold">保暖防风</span>。`;
  } else if (temp >= 0) {
    return `今日${weatherText}，气温较低。建议选择<span className="text-[#FE8F39] font-bold">厚实羽绒服或棉服</span>，内搭保暖衣物，做好防寒措施。`;
  } else {
    return `今日${weatherText}，气温严寒。建议选择<span className="text-[#FE8F39] font-bold">加厚羽绒服</span>，内搭保暖内衣，佩戴<span className="text-[#FE8F39] font-bold">帽子围巾手套</span>，全方位御寒。`;
  }
}

/**
 * WeatherHeader - 天气头部组件
 */
function WeatherHeader() {
  const { weather, location, loading, error, refetch } = useWeather();

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center py-4 px-1"
      >
        <div className="flex items-center gap-3">
          <div className="bg-[#FE8F39]/10 p-2 rounded-2xl animate-pulse">
            <Sun size={24} className="text-[#FE8F39]/50" />
          </div>
          <div>
            <div className="flex items-center gap-1 text-slate-400 text-[10px] font-medium uppercase tracking-wider">
              <MapPin size={10} />
              <span className="animate-pulse">获取位置中...</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-300 leading-none animate-pulse">--°</span>
              <span className="text-xs font-semibold text-slate-400">加载中</span>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  if (error || !weather) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center py-4 px-1"
      >
        <div className="flex items-center gap-3">
          <div className="bg-slate-100 p-2 rounded-2xl">
            <HelpCircle size={24} className="text-slate-400" />
          </div>
          <div>
            <div className="flex items-center gap-1 text-slate-400 text-[10px] font-medium uppercase tracking-wider">
              <MapPin size={10} />
              <span>未知位置</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-medium text-slate-500">{error || "无法获取天气"}</span>
            </div>
          </div>
        </div>
        <button
          onClick={refetch}
          className="flex items-center gap-1 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100 hover:bg-slate-100 transition-colors"
        >
          <RefreshCw size={12} className="text-slate-500" />
          <span className="text-[10px] font-bold text-slate-600">重试</span>
        </button>
      </motion.div>
    );
  }

  const temp = parseInt(weather.temp, 10);
  const iconName = getWeatherIconName(weather.icon);
  const WeatherIcon = getWeatherIconComponent(iconName);
  const locationText = location ? `${location.city} · ${weather.text}` : weather.text;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-between items-center py-4 px-1"
    >
      <div className="flex items-center gap-3">
        <div className="bg-[#FE8F39]/10 p-2 rounded-2xl">
          {WeatherIcon}
        </div>
        <div>
          <div className="flex items-center gap-1 text-slate-400 text-[10px] font-medium uppercase tracking-wider">
            <MapPin size={10} />
            <span>{locationText}</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-slate-900 leading-none">{weather.temp}°</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
        <Cloud size={14} className="text-blue-400" />
        <span className="text-[10px] font-bold text-slate-600">湿度 {weather.humidity}%</span>
      </div>
    </motion.div>
  );
}

/**
 * ClothingGuide - 穿衣指南组件
 */
function ClothingGuide() {
  const { weather, loading } = useWeather();

  const temp = weather ? parseInt(weather.temp, 10) : 22;
  const weatherText = weather?.text || "晴朗";

  const description = loading
    ? "正在获取天气数据，为您生成穿衣建议..."
    : getWeatherDescription(temp, weatherText);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white/60 backdrop-blur-sm border border-white p-4 rounded-3xl relative overflow-hidden shadow-sm"
    >
      <div className="absolute -right-4 -top-4 opacity-5">
        <Sparkles size={80} className="text-[#FE8F39]" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-5 h-5 bg-[#FE8F39]/10 rounded-lg flex items-center justify-center">
            <Sparkles size={12} className="text-[#FE8F39]" />
          </div>
          <span className="text-xs font-bold text-slate-800 tracking-tight">今日穿衣指南</span>
        </div>
        <p
          className="text-[13px] text-slate-600 leading-snug font-medium"
          dangerouslySetInnerHTML={{ __html: description }}
        />
      </div>
    </motion.div>
  );
}

/**
 * FeatureItem - 功能入口项组件
 */
interface FeatureItemProps {
  title: string;
  icon: React.ReactNode;
  color: string;
  span?: string;
}

function FeatureItem({ title, icon, color, span = "col-span-1" }: FeatureItemProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`relative rounded-2xl p-3 flex flex-col justify-center items-center gap-2 shadow-sm transition-all border ${color} ${span} cursor-pointer`}
    >
      <div className="p-2 rounded-xl bg-white/40 border border-white/20">{icon}</div>
      <h3 className="text-xs font-bold text-slate-800">{title}</h3>
    </motion.div>
  );
}

/**
 * FeatureGrid - 功能入口网格组件
 */
function FeatureGrid() {
  return (
    <div className="grid grid-cols-4 gap-3">
      <FeatureItem
        title="穿搭日记"
        icon={<BookOpen size={20} className="text-rose-500" />}
        color="bg-rose-50 border-rose-100"
      />
      <FeatureItem
        title="DIY穿搭"
        icon={<Palette size={20} className="text-blue-500" />}
        color="bg-blue-50 border-blue-100"
      />
      <FeatureItem
        title="我的衣橱"
        icon={<Camera size={20} className="text-amber-500" />}
        color="bg-amber-50 border-amber-100"
      />
      <FeatureItem
        title="穿搭集"
        icon={<LayoutGrid size={20} className="text-emerald-500" />}
        color="bg-emerald-50 border-emerald-100"
      />
      <motion.div
        whileTap={{ scale: 0.98 }}
        className="col-span-4 bg-slate-900 rounded-[24px] p-4 flex items-center justify-between shadow-xl shadow-slate-200 cursor-pointer relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-[#FE8F39]/10 rounded-full blur-2xl -mr-8 -mt-8" />

        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 bg-[#FE8F39] rounded-xl flex items-center justify-center text-white shadow-lg shadow-[#FE8F39]/20">
            <Wand2 size={20} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white mb-0.5">AI 深度定制推荐</h3>
            <p className="text-[10px] text-slate-400">基于您的风格基因进行匹配</p>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full border border-slate-800 flex items-center justify-center relative z-10">
          <Wand2 size={12} className="text-slate-500" />
        </div>
      </motion.div>
    </div>
  );
}

/**
 * TodayHighlight - 今日推荐组件
 */
interface TodayHighlightProps {
  imageUrl: string;
  onRefresh?: () => void;
}

interface TodayHighlightHandle {
  refresh: () => void;
}

const TodayHighlight = React.forwardRef<TodayHighlightHandle, TodayHighlightProps>(
  ({ imageUrl, onRefresh }, ref) => {
    const { weather, location } = useWeather();
    const [loading, setLoading] = useState(false);
    const [outfit, setOutfit] = useState<GenerateOutfitResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchOutfit = async (forceRefresh = false) => {
      if (!weather || !location || loading) return;

      setLoading(true);
      setError(null);

      try {
        const temp = parseFloat(weather.temp);
        const city = location.city;
        const response = forceRefresh
          ? await refreshOutfit(city, temp)
          : await generateTodayOutfit(city, temp);
        setOutfit(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取推荐失败");
        console.error("获取穿搭推荐失败:", err);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      // 有错误时不重新请求，等待用户手动重试
      if (weather && location && !outfit && !loading && !error) {
        fetchOutfit();
      }
    }, [weather, location, outfit, loading, error]);

    const handleRefresh = () => {
      if (loading) return;
      fetchOutfit(true);
      onRefresh?.();
    };

    React.useImperativeHandle(ref, () => ({
      refresh: handleRefresh,
    }));

    if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 flex items-center justify-center bg-slate-100"
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-[#FE8F39]" size={32} />
          <p className="text-xs font-medium text-slate-500">AI 正在为您生成穿搭...</p>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 flex items-center justify-center bg-red-50"
      >
        <div className="flex flex-col items-center gap-3 p-4 text-center">
          <AlertCircle className="text-red-400" size={32} />
          <p className="text-xs font-medium text-red-600">{error}</p>
          <button
            onClick={handleRefresh}
            className="text-xs font-bold text-[#FE8F39] hover:bg-orange-50 px-3 py-1.5 rounded-full transition-colors border border-orange-100"
          >
            重试
          </button>
        </div>
      </motion.div>
    );
  }

  if (!outfit) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 group cursor-pointer"
      >
        <img src={imageUrl} alt="Today's Recommendation" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

        <div className="absolute bottom-0 left-0 p-4 w-full text-white">
          <div className="flex justify-between items-end">
            <div>
              <div className="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold inline-block mb-1">
                AI 场景：周末约会
              </div>
              <h2 className="text-lg font-bold leading-tight">春日清新学院风</h2>
            </div>
            <button className="w-8 h-8 bg-white text-[#FE8F39] rounded-full flex items-center justify-center shadow-lg">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            </button>
          </div>
        </div>

        <div className="absolute top-3 right-3 bg-white/10 backdrop-blur-xl p-1.5 rounded-xl border border-white/20">
          <Sparkles className="text-yellow-300" size={16} />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 group cursor-pointer"
    >
      {/* AI 生成的模特穿搭图 */}
      <img
        src={outfit.image_url}
        alt="今日穿搭推荐"
        className="w-full h-full object-cover"
      />

      {/* 渐变遮罩 */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

      {/* AI 标签 */}
      <div className="absolute top-3 right-3 bg-white/10 backdrop-blur-xl p-1.5 rounded-xl border border-white/20">
        <Sparkles className="text-yellow-300" size={16} />
      </div>

      {/* 底部信息 */}
      <div className="absolute bottom-0 left-0 p-4 w-full text-white">
        {/* 标签行 */}
        <div className="flex flex-wrap gap-1 mb-2">
          <div className="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold">
            {weather?.temp}°C
          </div>
          <div className="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold">
            {outfit.scene === "daily" ? "日常" : outfit.scene === "work" ? "职场" : outfit.scene === "sport" ? "运动" : outfit.scene === "date" ? "约会" : "派对"}
          </div>
          {outfit.cached && (
            <div className="bg-green-500/30 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold">
              缓存
            </div>
          )}
        </div>

        {/* 描述 */}
        <h2 className="text-sm font-bold leading-tight mb-3">{outfit.description}</h2>

        {/* 搭配单品 */}
        {outfit.outfit_items && outfit.outfit_items.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {outfit.outfit_items.map((item, idx) => (
              <div key={idx} className="bg-white/15 backdrop-blur-sm rounded-lg px-2.5 py-1">
                <span className="text-[10px] text-white/60">{item.slot}</span>
                <span className="text-[10px] font-semibold text-white ml-1.5">{item.color} {item.description}</span>
              </div>
            ))}
          </div>
        )}

        {/* 换一批按钮 */}
        <button
          onClick={handleRefresh}
          className="flex items-center justify-center gap-2 bg-white/20 backdrop-blur-md text-white py-2.5 rounded-full font-bold text-xs border border-white/20 hover:bg-white/30 transition-colors w-full"
        >
          <RefreshCw size={12} />
          换一批
        </button>
      </div>
    </motion.div>
  );
  }
);

TodayHighlight.displayName = "TodayHighlight";
