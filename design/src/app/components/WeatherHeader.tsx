import React from 'react';
import { Sun, MapPin, Cloud } from 'lucide-react';
import { motion } from 'motion/react';

export const WeatherHeader: React.FC = () => {
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
