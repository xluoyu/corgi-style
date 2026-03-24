"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, MessageCircle, Zap } from "lucide-react";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { ClothesDetailModal } from "./ClothesDetailModal";
import { chatMessageStream } from "@/lib/api";
import { getUserId } from "@/lib/api";
import type { ChatMessage, ThinkingItem, OutfitCard, ClothesItem } from "@/types/chat";

/**
 * ChatPage - AI 对话页面
 */
export default function ChatPage() {
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [thinkingItems, setThinkingItems] = useState<ThinkingItem[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingCollapsed, setThinkingCollapsed] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedClothes, setSelectedClothes] = useState<ClothesItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 处理服装点击
  const handleClothesClick = useCallback((clothes: ClothesItem) => {
    setSelectedClothes(clothes);
    setIsModalOpen(true);
  }, []);

  // 关闭弹窗
  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedClothes(null), 200);
  }, []);

  // 处理建议点击
  const handleSuggestionClick = useCallback((action: string) => {
    // 将建议作为新消息发送
    handleSend(action);
  }, []);

  // 发送消息
  const handleSend = useCallback(async (text: string, imageUrl?: string) => {
    if (!text.trim() && !imageUrl) return;

    const userId = getUserId();

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 清空思考过程
    setThinkingItems([]);
    setIsThinking(true);
    setThinkingCollapsed(false);  // 开始时展开
    setError(null);

    // 累积的文本
    let accumulatedText = "";

    try {
      // 调用流式 API
      const stream = chatMessageStream({
        user_id: userId,
        session_id: sessionId || undefined,
        message: text,
        context: imageUrl ? { image_url: imageUrl } : undefined,
      });

      for await (const event of stream) {
        switch (event.event) {
          case "thinking": {
            // 防御：过滤无效数据（node 应为已知节点名，不含 { 或过长）
            const rawNode = event.content?.node;
            const isValidNode = typeof rawNode === "string" && rawNode.length < 50 && !rawNode.includes("{");
            if (isValidNode) {
              setThinkingItems((prev) => [
                ...prev,
                {
                  node: rawNode,
                  node_name: event.content?.node_name ?? rawNode,
                  text: event.content?.text ?? "",
                  timestamp: Date.now(),
                },
              ]);
            }
            break;
          }

          case "text":
            accumulatedText += event.content;
            // 更新最后一条 AI 消息
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === "assistant" && !lastMsg.outfitCard) {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMsg, content: accumulatedText },
                ];
              }
              // 创建新消息
              return [
                ...prev,
                {
                  id: `assistant-${Date.now()}`,
                  role: "assistant",
                  content: accumulatedText,
                  timestamp: new Date().toISOString(),
                },
              ];
            });
            break;

          case "outfit_card":
            // 创建穿搭卡片消息
            const outfitCard: OutfitCard = {
              plan: event.content.plan,
              clothes: event.content.clothes,
              match_score: event.content.match_score,
              scene: event.content.scene,
              temperature: event.content.temperature,
              city: event.content.city,
            };
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === "assistant") {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMsg,
                    outfitCard,
                  },
                ];
              }
              return [
                ...prev,
                {
                  id: `assistant-${Date.now()}`,
                  role: "assistant",
                  content: "",
                  outfitCard,
                  timestamp: new Date().toISOString(),
                },
              ];
            });
            break;

          case "suggestions":
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === "assistant") {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMsg,
                    suggestions: event.content,
                  },
                ];
              }
              return prev;
            });
            break;

          case "done":
            // 保存 session_id
            if (event.content.session_id) {
              setSessionId(event.content.session_id);
            }
            // done 时停止思考并收起面板
            setThinkingCollapsed(true);
            setIsThinking(false);
            break;

          case "error":
            setError(event.content.message || "发生错误");
            break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setIsThinking(false);
    }
  }, [sessionId]);

  return (
    <div className="h-screen bg-[#F1F4F9] flex flex-col relative">
      {/* 顶部导航 */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-100 px-4 py-3 flex items-center gap-3 safe-area-top z-20">
        <button
          onClick={() => router.back()}
          className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors"
        >
          <ArrowLeft size={20} className="text-slate-600" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-lg flex items-center justify-center">
            <MessageCircle size={16} className="text-[#FE8F39]" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-slate-800">AI 穿搭助手</h1>
            <p className="text-[10px] text-slate-400">基于您的衣柜智能推荐</p>
          </div>
        </div>
      </header>

      {/* 思考过程区 */}
      <div className="px-4 pt-3">
        <ThinkingIndicator
          items={thinkingItems}
          isThinking={isThinking}
          collapsed={thinkingCollapsed}
          onToggle={() => setThinkingCollapsed((c) => !c)}
        />
      </div>

      {/* 错误提示 */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-4 mt-3 px-4 py-2.5 bg-red-50 border border-red-100 rounded-xl"
          >
            <p className="text-[12px] text-red-600">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !isThinking && (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-slate-100 rounded-3xl flex items-center justify-center mb-4">
              <MessageCircle size={32} className="text-slate-300" />
            </div>
            <h2 className="text-[15px] font-bold text-slate-700 mb-1">
              开始对话
            </h2>
            <p className="text-[12px] text-slate-400 max-w-[240px]">
              告诉我你的穿搭需求，比如&quot;后天去北京参加晚宴穿什么&quot;
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onSuggestionClick={handleSuggestionClick}
            onClothesClick={handleClothesClick}
          />
        ))}

        {/* 加载指示器 */}
        {isThinking && messages[messages.length - 1]?.role === "user" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="bg-white border border-slate-100 px-4 py-3 rounded-3xl rounded-bl-md shadow-sm">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="text-[12px] text-slate-500">AI 思考中...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 快捷输入 - 仅无消息时显示 */}
      {messages.length === 0 && (
        <div className="px-4 pb-3">
          <button
            onClick={() => handleSend("帮我生成今日穿搭")}
            disabled={isThinking}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 disabled:opacity-50 rounded-full border border-slate-200 shadow-sm transition-colors"
          >
            <Zap size={12} className="text-[#FE8F39]" />
            <span className="text-[12px] font-medium text-slate-600">帮我生成今日穿搭</span>
          </button>
        </div>
      )}

      {/* 输入区 */}
      <ChatInput onSend={handleSend} disabled={isThinking} />

      {/* 衣物详情弹窗 */}
      <ClothesDetailModal
        clothes={selectedClothes}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}
