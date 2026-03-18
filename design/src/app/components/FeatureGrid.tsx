import React from 'react';
import { motion } from 'motion/react';
import { BookOpen, Palette, LayoutGrid, Wand2, Camera } from 'lucide-react';

interface FeatureItemProps {
  title: string;
  icon: React.ReactNode;
  color: string;
  span?: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ title, icon, color, span = "col-span-1" }) => {
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

export const FeatureGrid: React.FC = () => {
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
