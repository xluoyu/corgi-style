import React from 'react';
import { Sparkles, Info } from 'lucide-react';
import { motion } from 'motion/react';

export const ClothingGuide: React.FC = () => {
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
