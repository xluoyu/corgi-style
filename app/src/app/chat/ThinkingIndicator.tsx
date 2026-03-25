"use client";

import React, { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import type { ThinkingItem } from "@/types/chat";

interface ThinkingIndicatorProps {
  items: ThinkingItem[];
  isThinking: boolean;
  collapsed: boolean;
  onToggle: () => void;
}

/**
 * ThinkingIndicator - 思考过程显示组件
 * 固定高度，滚动显示AI思考过程
 */
export function ThinkingIndicator({ items, isThinking, collapsed, onToggle }: ThinkingIndicatorProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current && !collapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [items, isThinking, collapsed]);

  const nodeColors: Record<string, string> = {
    intent: "text-blue-500",
    weather: "text-amber-500",
    wardrobe_query: "text-emerald-500",
    outfit_planning: "text-purple-500",
    clothes_retrieval: "text-rose-500",
    outfit_evaluation: "text-cyan-500",
    feedback: "text-orange-500",
    response: "text-slate-500",
    generate_outfit: "text-indigo-500",
  };

  if (items.length === 0 && !isThinking) {
    return null;
  }

  return (
    <div className="bg-white/60 backdrop-blur-sm border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
      {/* 标题栏 */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-50/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            {isThinking && (
              <Loader2 size={14} className="text-[#FE8F39] animate-spin" />
            )}
            <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
              {isThinking ? "AI 思考中" : "思考过程"}
            </span>
          </div>
          <span className="text-[10px] text-slate-400">
            {items.length} 步
          </span>
        </div>
        {collapsed ? (
          <ChevronDown size={16} className="text-slate-400" />
        ) : (
          <ChevronUp size={16} className="text-slate-400" />
        )}
      </button>

      {/* 内容区 */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div
              ref={scrollRef}
              className="max-h-32 overflow-y-auto px-4 pb-3 space-y-1.5"
            >
              {items.map((item, index) => {
                const statusColors = {
                  pending: "text-[#FE8F39]",
                  success: "text-emerald-500",
                  error: "text-red-500",
                };
                const statusIcons = {
                  pending: "⚡",
                  success: "✅",
                  error: "❌",
                };
                const statusPrefix = item.status ? `${statusIcons[item.status]} ` : "";
                const statusColorClass = item.status ? statusColors[item.status] : "";

                return (
                  <motion.div
                    key={`${item.node}-${index}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                    className="flex items-start gap-2 text-[12px]"
                  >
                    <span className={`font-mono font-bold ${nodeColors[item.node] || "text-slate-400"} ${item.status ? (item.status === 'pending' ? 'animate-pulse' : '') : ''}`}>
                      [{item.node_name}]
                    </span>
                    <span className={`text-slate-600 ${statusColorClass}`}>
                      {statusPrefix}{item.text}
                    </span>
                  </motion.div>
                );
              })}

              {/* 正在思考的指示器 */}
              {isThinking && (
                <div className="flex items-center gap-2 text-[12px]">
                  <span className="font-mono font-bold text-[#FE8F39] animate-pulse">
                    [...]
                  </span>
                  <span className="text-slate-400">等待响应...</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
