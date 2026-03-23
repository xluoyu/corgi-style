"use client";

import React, { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Send, Image, X } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string, imageUrl?: string) => void;
  disabled?: boolean;
}

/**
 * ChatInput - 聊天输入区组件
 * 支持文字和图片发送
 */
export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 自动调整高度
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  // 发送消息
  const handleSend = useCallback((text?: string) => {
    const sendText = text || input.trim();
    if (!sendText && !imageFile) return;

    onSend(sendText, imagePreview || undefined);
    setInput("");
    setImagePreview(null);
    setImageFile(null);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, imageFile, imagePreview, onSend]);

  // 键盘发送
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 选择图片
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => {
        setImagePreview(ev.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
    // 重置 input 以允许选择同一文件
    e.target.value = "";
  };

  // 移除图片
  const handleRemoveImage = () => {
    setImagePreview(null);
    setImageFile(null);
  };

  const canSend = (input.trim() || imageFile) && !disabled;

  return (
    <div className="bg-white border-t border-slate-100 px-4 py-3">
      {/* 图片预览 */}
      {imagePreview && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-3 relative inline-block"
        >
          <div className="w-20 h-20 rounded-xl overflow-hidden border border-slate-200">
            <img
              src={imagePreview}
              alt="Preview"
              className="w-full h-full object-cover"
            />
          </div>
          <button
            onClick={handleRemoveImage}
            className="absolute -top-2 -right-2 w-6 h-6 bg-slate-800 text-white rounded-full flex items-center justify-center shadow-lg hover:bg-slate-700 transition-colors"
          >
            <X size={12} />
          </button>
        </motion.div>
      )}

      {/* 输入区 */}
      <div className="flex items-center gap-3">
        {/* 图片按钮 */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageSelect}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="w-11 h-11 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 rounded-xl flex items-center justify-center transition-colors flex-shrink-0"
        >
          <Image size={20} className="text-slate-500" />
        </button>

        {/* 输入框 */}
        <div className="flex-1 min-w-0">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="描述你的穿搭需求..."
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-[14px] text-slate-700 placeholder:text-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-[#FE8F39]/20 focus:border-[#FE8F39] disabled:opacity-50 transition-all"
            style={{ minHeight: "44px", maxHeight: "120px" }}
          />
        </div>

        {/* 发送按钮 */}
        <motion.button
          onClick={() => handleSend()}
          disabled={!canSend}
          whileTap={{ scale: 0.95 }}
          className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all flex-shrink-0 ${
            canSend
              ? "bg-[#FE8F39] shadow-lg shadow-[#FE8F39]/25 text-white"
              : "bg-slate-200 text-slate-400"
          }`}
        >
          <Send size={18} />
        </motion.button>
      </div>

      {/* 提示文字 */}
      <div className="mt-2 text-center">
        <span className="text-[10px] text-slate-400">
          Enter 发送 · Shift+Enter 换行
        </span>
      </div>
    </div>
  );
}
