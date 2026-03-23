"use client";

import React from "react";
import { motion } from "framer-motion";
import { OutfitCard } from "./OutfitCard";
import type { ChatMessage, Suggestion, ClothesItem } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
  onSuggestionClick?: (action: string) => void;
  onClothesClick?: (clothes: ClothesItem) => void;
}

/**
 * MessageBubble - 消息气泡组件
 */
export function MessageBubble({
  message,
  onSuggestionClick,
  onClothesClick,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] ${
          isUser ? "order-2" : "order-1"
        }`}
      >
        {/* 用户消息气泡 */}
        {isUser && (
          <div className="bg-[#FE8F39] text-white px-4 py-3 rounded-3xl rounded-br-md shadow-sm">
            <p className="text-[14px] leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
        )}

        {/* AI 消息 */}
        {!isUser && (
          <div className="space-y-3">
            {/* 文本内容 */}
            {message.content && (
              <div className="bg-white border border-slate-100 px-4 py-3 rounded-3xl rounded-bl-md shadow-sm">
                <p className="text-[14px] leading-relaxed text-slate-700 whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
            )}

            {/* 穿搭卡片 */}
            {message.outfitCard && (
              <div className="order-first">
                <OutfitCard
                  plan={message.outfitCard.plan}
                  clothes={message.outfitCard.clothes}
                  matchScore={message.outfitCard.match_score}
                  scene={message.outfitCard.scene}
                  temperature={message.outfitCard.temperature}
                  city={message.outfitCard.city}
                  onClothesClick={onClothesClick}
                />
              </div>
            )}

            {/* 建议按钮 */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {message.suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => suggestion.action && onSuggestionClick?.(suggestion.action)}
                    className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-600 text-[12px] font-medium rounded-full border border-slate-200 transition-colors"
                  >
                    {suggestion.text}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
