import React from 'react';
import { Sun, MapPin, Cloud, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { BookOpen, Palette, Wand2, Camera, LayoutGrid } from 'lucide-react';

export const HomePage: React.FC = () => {
  const heroImage =
    'https://images.unsplash.com/photo-1700557478776-952a33fda578?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWxlJTIwc3RyZWV0JTIwc3R5bGUlMjBvdXRmaXR8ZW58MXx8fHwxNzcyncsdlNTE3MDJ8MA&ixlib=rb-4-1.0&q=80&w=1080';

  return (
    <>
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
            <button className="text-[10px] font-bold text-[#FE8F39] hover:bg-orange-50 px-2.5 py-1 rounded-full transition-colors border border-orange-100">
              换一批
            </button>
          </div>
          <TodayHighlight imageUrl={heroImage} />
        </section>
      </div>
    </>
  );
};

const WeatherHeader: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-between items-center py-4 px-1"
    >
      <div className="flex items-center gap-3">
        <div className="bg-[#FE8F39]/10 p-2 rounded-2xl">
          <Sun size={24} className="text-[#FE8F39]" />
        </div>
        <div>
          <div className="flex items-center gap-1 text-slate-400 text-[10px] font-medium uppercase tracking-wider">
            <MapPin size={10} />
            <span>上海 · 晴朗</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-slate-900 leading-none">22°</span>
            <span className="text-xs font-semibold text-slate-500">宜穿搭</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
        <Cloud size={14} className="text-blue-400" />
        <span className="text-[10px] font-bold text-slate-600">AQI 24 优</span>
      </div>
    </motion.div>
  );
};

const ClothingGuide: React.FC = () => {
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
        <p className="text-[13px] text-slate-600 leading-snug font-medium">
          今日阳光充足，气温回升。建议选择<span className="text-[#FE8F39] font-bold">莫兰迪色系</span>的薄针织或衬衫，搭配浅色下装，打造轻盈呼吸感。
        </p>
      </div>
    </motion.div>
  );
};

interface FeatureItemProps {
  title: string;
  icon: React.ReactNode;
  color: string;
  span?: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ title, icon, color, span = 'col-span-1' }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`relative rounded-2xl p-3 flex flex-col justify-center items-center gap-2 shadow-sm transition-all border ${color} ${span} cursor-pointer`}
    >
      <div className="p-2 rounded-xl bg-white/40 border border-white/20">
        {icon}
      </div>
      <h3 className="text-xs font-bold text-slate-800">{title}</h3>
    </motion.div>
  );
};

const FeatureGrid: React.FC = () => {
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
};

interface TodayHighlightProps {
  imageUrl: string;
}

const TodayHighlight: React.FC<TodayHighlightProps> = ({ imageUrl }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 group cursor-pointer"
    >
      <img
        src={imageUrl}
        alt="Today's Recommendation"
        className="w-full h-full object-cover"
      />
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
};