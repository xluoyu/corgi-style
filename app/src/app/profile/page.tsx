"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  User,
  MapPin,
  Ruler,
  Scale,
  Sparkles,
  Clock,
  Heart,
  HelpCircle,
  ChevronRight,
  Camera,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { AvatarPicker } from "@/components/AvatarPicker";
import { useUser } from "@/hooks/useUser";
import { useWeather } from "@/hooks/useWeather";
import { updateUserInfo, getUserProfile } from "@/lib/api";
import type { UserProfileResponse } from "@/types/api";
import { useRouter } from "next/navigation";

const menuItems = [
  {
    icon: <Clock size={20} className="text-rose-500" />,
    title: "穿搭历史",
    subtitle: "记录每日穿搭",
    bgColor: "bg-rose-50",
    borderColor: "border-rose-100",
    href: "/history",
  },
  {
    icon: <Heart size={20} className="text-red-500" />,
    title: "我的收藏",
    subtitle: "收藏喜欢的搭配",
    bgColor: "bg-red-50",
    borderColor: "border-red-100",
    href: "/favorites",
  },
  {
    icon: <Sparkles size={20} className="text-amber-500" />,
    title: "偏好设置",
    subtitle: "个性化推荐设置",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-100",
    href: "/preferences",
  },
  {
    icon: <HelpCircle size={20} className="text-blue-500" />,
    title: "关于与帮助",
    subtitle: "使用指南与反馈",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-100",
    href: "/about",
  },
];

// 风格偏好展示标签
const STYLE_LABELS: Record<string, string> = {
  minimalist: "简约",
  casual: "休闲",
  business: "商务",
  sport: "运动",
  street: "街头",
  vintage: "复古",
};

/**
 * 简单输入弹窗
 */
function EditModal({
  title,
  value,
  onSave,
  onClose,
  type = "text",
  min,
  max,
}: {
  title: string;
  value: string | number;
  onSave: (val: string) => void;
  onClose: () => void;
  type?: "text" | "number";
  min?: number;
  max?: number;
}) {
  const [input, setInput] = useState(String(value));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className="bg-white rounded-3xl w-full max-w-xs p-5 shadow-2xl"
      >
        <h2 className="text-base font-bold text-slate-900 mb-4">{title}</h2>
        <input
          type={type}
          value={input}
          min={min}
          max={max}
          onChange={(e) => setInput(e.target.value)}
          autoFocus
          className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#FE8F39]/20 focus:border-[#FE8F39] transition-all mb-4"
        />
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-slate-100 text-slate-500 text-sm font-bold rounded-xl hover:bg-slate-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => onSave(input)}
            className="flex-1 py-3 bg-[#FE8F39] text-white text-sm font-bold rounded-xl hover:bg-[#e07d2a] active:scale-[0.98] transition-all"
          >
            保存
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/**
 * 个人中心页面
 */
export default function ProfilePage() {
  const router = useRouter();
  const { user, loading: userLoading } = useUser();
  const { location } = useWeather();

  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // 弹窗状态
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);
  const [showNicknameEditor, setShowNicknameEditor] = useState(false);
  const [showHeightEditor, setShowHeightEditor] = useState(false);
  const [showWeightEditor, setShowWeightEditor] = useState(false);
  const [saving, setSaving] = useState(false);

  // 编辑中的值
  const [editingNickname, setEditingNickname] = useState("");
  const [editingHeight, setEditingHeight] = useState(0);
  const [editingWeight, setEditingWeight] = useState(0);

  // 获取完整用户资料
  const fetchProfile = useCallback(async () => {
    if (!user) return;
    setProfileLoading(true);
    try {
      const data = await getUserProfile();
      setProfile(data);
    } catch (err) {
      console.error("获取用户资料失败:", err);
    } finally {
      setProfileLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user, fetchProfile]);

  // 保存用户信息（乐观更新）
  const saveUserInfo = async (updates: Record<string, unknown>) => {
    if (!profile) return;
    // 立即更新本地状态
    setProfile({ ...profile, ...updates } as UserProfileResponse);
    setSaving(true);
    try {
      await updateUserInfo(updates);
    } catch (err) {
      // 失败时回滚
      setProfile(profile);
      console.error("保存失败:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleNicknameSave = (val: string) => {
    setShowNicknameEditor(false);
    saveUserInfo({ nickname: val.trim() || "时尚路人甲" });
  };

  const handleAvatarSelect = (avatarUrl: string) => {
    setShowAvatarPicker(false);
    saveUserInfo({ avatar_url: avatarUrl });
  };

  const handleHeightSave = (val: string) => {
    const h = parseInt(val, 10);
    setShowHeightEditor(false);
    if (h > 0 && h < 300) {
      saveUserInfo({ height: h });
    }
  };

  const handleWeightSave = (val: string) => {
    const w = parseInt(val, 10);
    setShowWeightEditor(false);
    if (w > 0 && w < 500) {
      saveUserInfo({ weight: w });
    }
  };

  const handleMenuClick = (href: string) => {
    router.push(href);
  };

  // 计算显示用数据
  const nickname = profile?.nickname || user?.nickname || "时尚路人甲";
  const avatarUrl = profile?.avatar_url || user?.avatar_url || "";
  const city = location?.city || "未知城市";
  const height = profile?.height;
  const weight = profile?.weight;
  const stylePrefs = profile?.style_preferences
    ? (typeof profile.style_preferences === "string"
      ? JSON.parse(profile.style_preferences)
      : profile.style_preferences)
    : [];

  const isLoading = userLoading || profileLoading;

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-blue-100/30 to-transparent pointer-events-none z-0" />

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="flex flex-col h-full overflow-y-auto">
          <div className="px-5 pt-4 pb-6">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center">
                <User size={18} className="text-[#FE8F39]" />
              </div>
              <h1 className="text-lg font-bold text-slate-900">个人中心</h1>
            </div>

            {/* Loading 骨架 */}
            {isLoading ? (
              <div className="space-y-3">
                <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 animate-pulse">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-slate-200" />
                    <div className="flex-1 space-y-2">
                      <div className="h-5 bg-slate-200 rounded w-24" />
                      <div className="h-3 bg-slate-100 rounded w-16" />
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 animate-pulse">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="h-14 bg-slate-100 rounded-xl" />
                    <div className="h-14 bg-slate-100 rounded-xl" />
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* 用户卡片 */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100"
                >
                  <div className="flex items-center gap-4">
                    {/* 头像 */}
                    <div
                      className="relative cursor-pointer group"
                      onClick={() => setShowAvatarPicker(true)}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={avatarUrl}
                        alt={nickname}
                        className="w-16 h-16 rounded-full object-cover border-3 border-[#FE8F39]/20"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src =
                            "https://avataaars.io/?avatarStyle=Circle&topType=ShortHairShortCurly&accessoriesType=Blank&hairColor=Black&facialHairType=Blank&clotheType=Hoodie&clotheColor=Black&eyeType=Happy&eyebrowType=DefaultNatural&mouthType=Smile&skinColor=Yellow";
                        }}
                      />
                      <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-[#FE8F39] rounded-full flex items-center justify-center border-2 border-white group-hover:bg-[#e07d2a] transition-colors">
                        <Camera size={12} className="text-white" />
                      </div>
                    </div>

                    {/* 昵称 + 城市 */}
                    <div className="flex-1">
                      <button
                        onClick={() => {
                          setEditingNickname(nickname);
                          setShowNicknameEditor(true);
                        }}
                        className="text-lg font-bold text-slate-900 hover:text-[#FE8F39] transition-colors text-left"
                      >
                        {nickname}
                        {saving && (
                          <Loader2 size={14} className="inline ml-1 animate-spin text-slate-400" />
                        )}
                      </button>
                      <div className="flex items-center gap-1 mt-1 text-slate-400 text-xs">
                        <MapPin size={12} />
                        <span>{city}</span>
                      </div>
                    </div>

                    {/* 统计徽章 */}
                    <div className="bg-[#FE8F39]/10 px-3 py-1.5 rounded-full">
                      <span className="text-[10px] font-bold text-[#FE8F39]">
                        {profile?.clothes_count || 0} 件衣物
                      </span>
                    </div>
                  </div>
                </motion.div>

                {/* 个人信息卡片 */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-3xl p-5 mt-3 shadow-sm border border-slate-100"
                >
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                    个人信息
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {/* 身高 */}
                    <button
                      onClick={() => {
                        setEditingHeight(height || 170);
                        setShowHeightEditor(true);
                      }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-blue-50/50 border border-blue-100 hover:bg-blue-50 transition-colors w-full text-left"
                    >
                      <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center border border-blue-100">
                        <Ruler size={18} className="text-blue-500" />
                      </div>
                      <div>
                        <p className="text-[10px] text-slate-400 font-medium">身高</p>
                        <p className="text-sm font-bold text-slate-800">
                          {height ? `${height}cm` : "未设置"}
                        </p>
                      </div>
                    </button>

                    {/* 体重 */}
                    <button
                      onClick={() => {
                        setEditingWeight(weight || 60);
                        setShowWeightEditor(true);
                      }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-emerald-50/50 border border-emerald-100 hover:bg-emerald-50 transition-colors w-full text-left"
                    >
                      <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center border border-emerald-100">
                        <Scale size={18} className="text-emerald-500" />
                      </div>
                      <div>
                        <p className="text-[10px] text-slate-400 font-medium">体重</p>
                        <p className="text-sm font-bold text-slate-800">
                          {weight ? `${weight}kg` : "未设置"}
                        </p>
                      </div>
                    </button>
                  </div>

                  {/* 风格偏好 */}
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <p className="text-[10px] text-slate-400 font-medium mb-2">风格偏好</p>
                    <div className="flex flex-wrap gap-2">
                      {stylePrefs.length > 0 ? (
                        stylePrefs.map((pref: string) => (
                          <span
                            key={pref}
                            className="px-2.5 py-1 bg-[#FE8F39]/10 rounded-full text-[10px] font-bold text-[#FE8F39]"
                          >
                            {STYLE_LABELS[pref] || pref}
                          </span>
                        ))
                      ) : (
                        <button
                          onClick={() => router.push("/preferences")}
                          className="px-2.5 py-1 bg-slate-100 rounded-full text-[10px] font-bold text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          + 添加偏好
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </div>

          {/* 功能菜单 */}
          <div className="flex-1 px-5 pb-8">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              功能菜单
            </h3>
            <div className="flex flex-col gap-3">
              {menuItems.map((item, index) => (
                <motion.button
                  key={item.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleMenuClick(item.href)}
                  className="flex items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-100 w-full text-left"
                >
                  <div
                    className={`w-12 h-12 ${item.bgColor} rounded-xl flex items-center justify-center border ${item.borderColor}`}
                  >
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
      </main>

      {/* 弹窗 */}
      <AnimatePresence>
        {showAvatarPicker && (
          <AvatarPicker
            currentAvatarUrl={avatarUrl}
            onSelect={handleAvatarSelect}
            onClose={() => setShowAvatarPicker(false)}
          />
        )}
        {showNicknameEditor && (
          <EditModal
            title="修改昵称"
            value={editingNickname}
            onSave={handleNicknameSave}
            onClose={() => setShowNicknameEditor(false)}
            type="text"
          />
        )}
        {showHeightEditor && (
          <EditModal
            title="设置身高"
            value={editingHeight}
            onSave={handleHeightSave}
            onClose={() => setShowHeightEditor(false)}
            type="number"
            min={100}
            max={250}
          />
        )}
        {showWeightEditor && (
          <EditModal
            title="设置体重"
            value={editingWeight}
            onSave={handleWeightSave}
            onClose={() => setShowWeightEditor(false)}
            type="number"
            min={30}
            max={200}
          />
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
}
