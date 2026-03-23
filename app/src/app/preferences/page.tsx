"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowLeft,
  Palette,
  Sparkles,
  Sun,
  Check,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
} from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { updateUserInfo, getUserPreference } from "@/lib/api";
import type { UserProfile } from "@/types/api";
import { useRouter } from "next/navigation";

// 风格选项
const STYLE_OPTIONS = [
  { id: "minimalist", label: "简约", icon: "✨", color: "bg-slate-50 border-slate-200 text-slate-700" },
  { id: "casual", label: "休闲", icon: "🎯", color: "bg-blue-50 border-blue-200 text-blue-700" },
  { id: "business", label: "商务", icon: "💼", color: "bg-indigo-50 border-indigo-200 text-indigo-700" },
  { id: "sport", label: "运动", icon: "🏃", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  { id: "street", label: "街头", icon: "🎧", color: "bg-purple-50 border-purple-200 text-purple-700" },
  { id: "vintage", label: "复古", icon: "🎻", color: "bg-amber-50 border-amber-200 text-amber-700" },
];

// 场景选项
const SCENE_OPTIONS = [
  { id: "daily", label: "日常通勤", icon: "🚶", color: "bg-slate-50 border-slate-200 text-slate-700" },
  { id: "date", label: "周末约会", icon: "💕", color: "bg-rose-50 border-rose-200 text-rose-700" },
  { id: "sport", label: "运动健身", icon: "💪", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  { id: "work", label: "职场工作", icon: "💼", color: "bg-indigo-50 border-indigo-200 text-indigo-700" },
  { id: "party", label: "聚会派对", icon: "🎉", color: "bg-purple-50 border-purple-200 text-purple-700" },
  { id: "formal", label: "正式场合", icon: "🎩", color: "bg-slate-50 border-slate-200 text-slate-700" },
];

// 季节选项
const SEASON_OPTIONS = [
  { id: "spring", label: "春", icon: "🌸", color: "bg-pink-50 border-pink-200 text-pink-700" },
  { id: "summer", label: "夏", icon: "☀️", color: "bg-yellow-50 border-yellow-200 text-yellow-700" },
  { id: "autumn", label: "秋", icon: "🍂", color: "bg-orange-50 border-orange-200 text-orange-700" },
  { id: "winter", label: "冬", icon: "❄️", color: "bg-blue-50 border-blue-200 text-blue-700" },
];

/**
 * 标签选择组件
 */
function TagSelector({
  options,
  selected,
  onChange,
  multiSelect = true,
}: {
  options: Array<{ id: string; label: string; icon: string; color: string }>;
  selected: string[];
  onChange: (selected: string[]) => void;
  multiSelect?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const isSelected = selected.includes(option.id);
        return (
          <motion.button
            key={option.id}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              if (multiSelect) {
                onChange(
                  isSelected
                    ? selected.filter((id) => id !== option.id)
                    : [...selected, option.id]
                );
              } else {
                onChange(isSelected ? [] : [option.id]);
              }
            }}
            className={`
              relative px-3.5 py-2 rounded-2xl border-2 flex items-center gap-2
              transition-all duration-200
              ${isSelected ? option.color + " border-current shadow-sm" : "bg-white border-slate-200 text-slate-400"}
            `}
          >
            <span className="text-sm">{option.icon}</span>
            <span className="text-xs font-bold">{option.label}</span>
            {isSelected && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-4 h-4 bg-[#FE8F39] rounded-full flex items-center justify-center"
              >
                <Check size={10} className="text-white" strokeWidth={3} />
              </motion.div>
            )}
          </motion.button>
        );
      })}
    </div>
  );
}

/**
 * 通知组件
 */
function Notification({
  type,
  message,
  onClose,
}: {
  type: "success" | "error";
  message: string;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`
          fixed top-20 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl shadow-lg z-50
          flex items-center gap-2
          ${type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}
        `}
      >
        {type === "success" ? (
          <CheckCircle2 size={20} />
        ) : (
          <AlertCircle size={20} />
        )}
        <span className="text-sm font-bold">{message}</span>
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * PreferencesPage - 偏好设置页面组件
 * 用户可以设置风格、场景和季节偏好
 */
export default function PreferencesPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // 用户偏好状态
  const [stylePreferences, setStylePreferences] = useState<string[]>([]);
  const [seasonPreferences, setSeasonPreferences] = useState<string[]>([]);
  const [defaultOccasion, setDefaultOccasion] = useState<string>("");

  // 加载用户偏好
  useEffect(() => {
    loadUserPreferences();
  }, []);

  const loadUserPreferences = async () => {
    try {
      setLoading(true);
      const preference = await getUserPreference();
      setStylePreferences(preference.style_preferences || []);
      setSeasonPreferences(preference.season_preference || []);
      setDefaultOccasion(preference.default_occasion || "");
    } catch (error) {
      console.error("加载用户偏好失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      await updateUserInfo({
        user_id: "",
        style_preferences: stylePreferences,
        season_preference: seasonPreferences,
        default_occasion: defaultOccasion,
      });
      setNotification({
        type: "success",
        message: "偏好设置已保存",
      });
      setTimeout(() => {
        setNotification(null);
        router.push("/profile");
      }, 1500);
    } catch (error) {
      console.error("保存偏好失败:", error);
      setNotification({
        type: "error",
        message: "保存失败，请重试",
      });
      setTimeout(() => setNotification(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const isFormValid =
    stylePreferences.length > 0 &&
    seasonPreferences.length > 0 &&
    defaultOccasion.length > 0;

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      {/* 背景装饰 */}
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-amber-100/20 to-transparent pointer-events-none z-0" />

      {/* 通知 */}
      <AnimatePresence>
        {notification && (
          <Notification
            type={notification.type}
            message={notification.message}
            onClose={() => setNotification(null)}
          />
        )}
      </AnimatePresence>

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="flex flex-col h-full overflow-y-auto">
          {/* 头部 */}
          <div className="px-5 pt-4 pb-6">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 mb-6"
            >
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => router.push("/profile")}
                className="w-8 h-8 bg-white rounded-xl flex items-center justify-center shadow-sm border border-slate-100"
              >
                <ArrowLeft size={18} className="text-slate-600" />
              </motion.button>
              <h1 className="text-lg font-bold text-slate-900">偏好设置</h1>
            </motion.div>

            {/* 说明卡片 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Sparkles size={20} className="text-[#FE8F39]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800 mb-1">
                    个性化推荐
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    根据您的偏好，我们将为您推荐更合适的穿搭方案。您可以随时修改这些设置。
                  </p>
                </div>
              </div>
            </motion.div>

            {/* 风格偏好 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4"
            >
              <div className="flex items-center gap-2 mb-4">
                <Palette size={18} className="text-[#FE8F39]" />
                <h3 className="text-sm font-bold text-slate-800">风格偏好</h3>
              </div>
              <p className="text-xs text-slate-400 mb-3">
                选择您喜欢的穿搭风格（可多选）
              </p>
              <TagSelector
                options={STYLE_OPTIONS}
                selected={stylePreferences}
                onChange={setStylePreferences}
              />
            </motion.div>

            {/* 场景偏好 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4"
            >
              <div className="flex items-center gap-2 mb-4">
                <Sun size={18} className="text-[#FE8F39]" />
                <h3 className="text-sm font-bold text-slate-800">场景偏好</h3>
              </div>
              <p className="text-xs text-slate-400 mb-3">
                选择默认穿搭场景（单选）
              </p>
              <TagSelector
                options={SCENE_OPTIONS}
                selected={defaultOccasion ? [defaultOccasion] : []}
                onChange={(selected) => setDefaultOccasion(selected[0] || "")}
                multiSelect={false}
              />
            </motion.div>

            {/* 季节偏好 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 mb-4"
            >
              <div className="flex items-center gap-2 mb-4">
                <Sun size={18} className="text-[#FE8F39]" />
                <h3 className="text-sm font-bold text-slate-800">季节偏好</h3>
              </div>
              <p className="text-xs text-slate-400 mb-3">
                选择您经常穿搭的季节（可多选）
              </p>
              <TagSelector
                options={SEASON_OPTIONS}
                selected={seasonPreferences}
                onChange={setSeasonPreferences}
              />
            </motion.div>

            {/* 保存按钮 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mt-4"
            >
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={handleSave}
                disabled={loading || !isFormValid}
                className={`
                  w-full py-3.5 rounded-2xl font-bold text-sm flex items-center justify-center gap-2
                  transition-all duration-200
                  ${isFormValid && !loading
                    ? "bg-[#FE8F39] text-white shadow-lg shadow-[#FE8F39]/25"
                    : "bg-slate-200 text-slate-400 cursor-not-allowed"
                  }
                `}
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <span>保存偏好</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </motion.button>

              {!isFormValid && !loading && (
                <p className="text-center text-xs text-slate-400 mt-3">
                  请至少选择一个风格、一个场景和一个季节
                </p>
              )}
            </motion.div>
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
