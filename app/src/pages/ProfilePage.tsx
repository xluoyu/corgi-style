import React from 'react';
import { motion } from 'motion/react';
import {
  User,
  MapPin,
  Ruler,
  Scale,
  Sparkles,
  Clock,
  Heart,
  Settings,
  HelpCircle,
  ChevronRight,
  Camera,
} from 'lucide-react';

const mockUserData = {
  avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&h=200&fit=crop',
  nickname: '时尚小熊',
  city: '上海',
  height: '175cm',
  weight: '65kg',
  scenes: ['日常通勤', '周末约会', '运动健身'],
  style: '简约休闲',
};

const menuItems = [
  {
    icon: <Clock size={20} className="text-rose-500" />,
    title: '穿搭历史',
    subtitle: '记录每日穿搭',
    bgColor: 'bg-rose-50',
    borderColor: 'border-rose-100',
  },
  {
    icon: <Heart size={20} className="text-red-500" />,
    title: '我的收藏',
    subtitle: '收藏喜欢的搭配',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-100',
  },
  {
    icon: <Sparkles size={20} className="text-amber-500" />,
    title: '偏好设置',
    subtitle: '个性化推荐设置',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-100',
  },
  {
    icon: <HelpCircle size={20} className="text-blue-500" />,
    title: '关于与帮助',
    subtitle: '使用指南与反馈',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-100',
  },
];

export const ProfilePage: React.FC = () => {
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-5 pt-4 pb-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center">
            <User size={18} className="text-[#FE8F39]" />
          </div>
          <h1 className="text-lg font-bold text-slate-900">个人中心</h1>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100"
        >
          <div className="flex items-center gap-4">
            <div className="relative">
              <img
                src={mockUserData.avatar}
                alt={mockUserData.nickname}
                className="w-16 h-16 rounded-full object-cover border-3 border-[#FE8F39]/20"
              />
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-[#FE8F39] rounded-full flex items-center justify-center border-2 border-white">
                <Camera size={12} className="text-white" />
              </div>
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-slate-900">{mockUserData.nickname}</h2>
              <div className="flex items-center gap-1 mt-1 text-slate-400 text-xs">
                <MapPin size={12} />
                <span>{mockUserData.city}</span>
              </div>
            </div>
            <div className="bg-[#FE8F39]/10 px-3 py-1.5 rounded-full">
              <span className="text-[10px] font-bold text-[#FE8F39]">Lv.5 时尚达人</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-3xl p-5 mt-3 shadow-sm border border-slate-100"
        >
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">个人信息</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center border border-blue-100">
                <Ruler size={18} className="text-blue-500" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">身高</p>
                <p className="text-sm font-bold text-slate-800">{mockUserData.height}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center border border-emerald-100">
                <Scale size={18} className="text-emerald-500" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">体重</p>
                <p className="text-sm font-bold text-slate-800">{mockUserData.weight}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium mb-2">常穿场景</p>
            <div className="flex flex-wrap gap-2">
              {mockUserData.scenes.map((scene) => (
                <span
                  key={scene}
                  className="px-2.5 py-1 bg-slate-100 rounded-full text-[10px] font-bold text-slate-600"
                >
                  {scene}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium mb-2">风格偏好</p>
            <div className="flex items-center gap-2">
              <Sparkles size={14} className="text-[#FE8F39]" />
              <span className="text-sm font-bold text-slate-800">{mockUserData.style}</span>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="flex-1 px-5 pb-8">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">功能菜单</h3>
        <div className="flex flex-col gap-3">
          {menuItems.map((item, index) => (
            <motion.button
              key={item.title}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-100 w-full text-left"
            >
              <div className={`w-12 h-12 ${item.bgColor} rounded-xl flex items-center justify-center border ${item.borderColor}`}>
                {item.icon}
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-bold text-slate-800">{item.title}</h4>
                <p className="text-[10px] text-slate-400 mt-0.5">{item.subtitle}</p>
              </div>
              <ChevronRight size={18} className="text-slate-300" />
            </motion.button>
          ))}
        </div>

        <div className="mt-6 text-center">
          <p className="text-[10px] text-slate-300">Corgi Style v1.0.0</p>
        </div>
      </div>
    </div>
  );
};