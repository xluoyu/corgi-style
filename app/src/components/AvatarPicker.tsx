"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Check } from "lucide-react";
import avatarsData from "../data/avataaars.json";

interface AvatarPickerProps {
  currentAvatarUrl?: string;
  onSelect: (avatarUrl: string) => void;
  onClose: () => void;
}

type Gender = "boys" | "girls";

export function AvatarPicker({
  currentAvatarUrl,
  onSelect,
  onClose,
}: AvatarPickerProps) {
  const [gender, setGender] = useState<Gender>("boys");
  const [selected, setSelected] = useState<string>(
    currentAvatarUrl || (avatarsData.boys[0] as string)
  );

  const avatars = avatarsData[gender] as string[];

  const handleConfirm = () => {
    onSelect(selected);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className="bg-white rounded-3xl w-full max-w-sm p-5 shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900">选择头像</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
          >
            <X size={16} className="text-slate-500" />
          </button>
        </div>

        {/* Gender Tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => {
              setGender("boys");
              setSelected(avatarsData.boys[0] as string);
            }}
            className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all ${
              gender === "boys"
                ? "bg-[#FE8F39] text-white shadow-sm"
                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
            }`}
          >
            男
          </button>
          <button
            onClick={() => {
              setGender("girls");
              setSelected(avatarsData.girls[0] as string);
            }}
            className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all ${
              gender === "girls"
                ? "bg-[#FE8F39] text-white shadow-sm"
                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
            }`}
          >
            女
          </button>
        </div>

        {/* Avatar Grid */}
        <div className="grid grid-cols-4 gap-2 mb-4 max-h-64 overflow-y-auto pr-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={gender}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="contents"
            >
              {avatars.map((url) => (
                <button
                  key={url}
                  onClick={() => setSelected(url)}
                  className={`relative w-full aspect-square rounded-xl overflow-hidden border-2 transition-all ${
                    selected === url
                      ? "border-[#FE8F39] ring-2 ring-[#FE8F39]/20"
                      : "border-slate-100 hover:border-slate-300"
                  }`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={url}
                    alt="avatar"
                    className="w-full h-full object-cover"
                  />
                  {selected === url && (
                    <div className="absolute inset-0 bg-[#FE8F39]/20 flex items-center justify-center">
                      <div className="w-5 h-5 bg-[#FE8F39] rounded-full flex items-center justify-center">
                        <Check size={12} className="text-white" />
                      </div>
                    </div>
                  )}
                </button>
              ))}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Confirm Button */}
        <button
          onClick={handleConfirm}
          className="w-full py-3 bg-[#FE8F39] text-white text-sm font-bold rounded-xl hover:bg-[#e07d2a] active:scale-[0.98] transition-all"
        >
          确认选择
        </button>
      </motion.div>
    </motion.div>
  );
}
