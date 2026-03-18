import React from 'react';
import { motion } from 'motion/react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Sparkles, Play } from 'lucide-react';

interface TodayHighlightProps {
  imageUrl: string;
}

export const TodayHighlight: React.FC<TodayHighlightProps> = ({ imageUrl }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative rounded-3xl overflow-hidden shadow-lg flex-1 min-h-0 group cursor-pointer"
    >
      <ImageWithFallback 
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
            <Play size={14} fill="currentColor" />
          </button>
        </div>
      </div>
      
      <div className="absolute top-3 right-3 bg-white/10 backdrop-blur-xl p-1.5 rounded-xl border border-white/20">
        <Sparkles className="text-yellow-300" size={16} />
      </div>
    </motion.div>
  );
};
