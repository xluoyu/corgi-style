"use client";

import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Shirt, Wind, Crown, Sparkles, Watch, Plus, X, Upload, Loader2 } from "lucide-react";
import { BottomNav } from "@/components/BottomNav";
import { uploadClothesImage, getClothesList, pollClothesStatus } from "@/lib/api";
import type { UploadClothesResponse, ClothingItem as ApiClothingItem } from "@/types/api";

type CategoryType = "all" | "top" | "bottom" | "outer" | "inner" | "accessory";

interface ClothingItem {
  id: number;
  name: string;
  category: CategoryType;
  color: string;
  imageUrl: string;
}

interface AddClothesForm {
  description: string;
  color?: string;
  material?: string;
  scene?: string;
}

const mockClothingData: ClothingItem[] = [
  {
    id: 1,
    name: "白色棉质T恤",
    category: "top",
    color: "白色",
    imageUrl: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=500&fit=crop",
  },
  {
    id: 2,
    name: "深蓝色牛仔裤",
    category: "bottom",
    color: "深蓝色",
    imageUrl: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop",
  },
  {
    id: 3,
    name: "灰色休闲西装",
    category: "outer",
    color: "灰色",
    imageUrl: "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop",
  },
  {
    id: 4,
    name: "粉色针织衫",
    category: "inner",
    color: "粉色",
    imageUrl: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=500&fit=crop",
  },
  {
    id: 5,
    name: "黑色皮质手表",
    category: "accessory",
    color: "黑色",
    imageUrl: "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=500&fit=crop",
  },
  {
    id: 6,
    name: "条纹衬衫",
    category: "top",
    color: "蓝白条纹",
    imageUrl: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop",
  },
  {
    id: 7,
    name: "卡其色工装裤",
    category: "bottom",
    color: "卡其色",
    imageUrl: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&h=500&fit=crop",
  },
  {
    id: 8,
    name: "黑色风衣",
    category: "outer",
    color: "黑色",
    imageUrl: "https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=400&h=500&fit=crop",
  },
  {
    id: 9,
    name: "白色打底衫",
    category: "inner",
    color: "白色",
    imageUrl: "https://images.unsplash.com/photo-1485218126466-34e6392ec754?w=400&h=500&fit=crop",
  },
  {
    id: 10,
    name: "银色项链",
    category: "accessory",
    color: "银色",
    imageUrl: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=500&fit=crop",
  },
  {
    id: 11,
    name: "藏青色Polo衫",
    category: "top",
    color: "藏青色",
    imageUrl: "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&h=500&fit=crop",
  },
  {
    id: 12,
    name: "棕色皮带",
    category: "accessory",
    color: "棕色",
    imageUrl: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=500&fit=crop",
  },
];

const categoryLabels: Record<CategoryType, string> = {
  all: "全部",
  top: "上衣",
  bottom: "裤子",
  outer: "外套",
  inner: "内搭",
  accessory: "配饰",
};

const categoryIcons: Record<CategoryType, React.ReactNode> = {
  all: <Shirt size={16} />,
  top: <Shirt size={16} />,
  bottom: <Wind size={16} />,
  outer: <Crown size={16} />,
  inner: <Sparkles size={16} />,
  accessory: <Watch size={16} />,
};

/**
 * WardrobePage - 衣柜页面组件
 * 展示用户的衣物列表，支持分类筛选
 */
export default function WardrobePage() {
  const [activeCategory, setActiveCategory] = useState<CategoryType>("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [clothingData, setClothingData] = useState<ClothingItem[]>(mockClothingData);
  const [form, setForm] = useState<AddClothesForm>({ description: "" });

  // 获取衣物列表
  const fetchClothingList = async () => {
    try {
      const response = await getClothesList();
      if (response.clothes && response.clothes.length > 0) {
        const formattedClothes: ClothingItem[] = response.clothes.map((item) => ({
          id: parseInt(item.id),
          name: item.sub_category || item.tags.colors?.[0] || "未命名",
          category: item.category as CategoryType,
          color: item.tags.colors?.join(", ") || "未知",
          imageUrl: item.cartoon_image_url || item.original_image_url,
        }));
        setClothingData(formattedClothes);
      }
    } catch (error) {
      console.error("获取衣物列表失败:", error);
      // 保持使用模拟数据
    }
  };

  // 组件挂载时获取衣物列表
  useEffect(() => {
    fetchClothingList();
  }, []);

  const filteredClothes =
    activeCategory === "all"
      ? clothingData
      : clothingData.filter((item) => item.category === activeCategory);

  const categories: CategoryType[] = ["all", "top", "bottom", "outer", "inner", "accessory"];

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setUploadError(null);
    }
  };

  // 处理上传
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError("请选择一张图片");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const response = await uploadClothesImage(selectedFile, form.description);

      // 轮询等待处理完成
      await pollClothesStatus(response.clothes_id, 60, 1000);

      // 上传成功，刷新列表
      await fetchClothingList();

      // 关闭模态框并重置表单
      closeModal();
    } catch (error) {
      console.error("上传失败:", error);
      setUploadError(error instanceof Error ? error.message : "上传失败，请重试");
    } finally {
      setIsUploading(false);
    }
  };

  // 关闭模态框
  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedFile(null);
    setPreviewUrl(null);
    setForm({ description: "" });
    setUploadError(null);
  };

  return (
    <div className="h-screen bg-[#F1F4F9] font-sans text-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-blue-100/30 to-transparent pointer-events-none z-0" />

      <main className="h-full overflow-y-auto relative z-10 pb-20">
        <div className="flex flex-col h-full">
          <div className="px-5 pt-4 pb-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#FE8F39]/10 rounded-xl flex items-center justify-center">
                <Shirt size={18} className="text-[#FE8F39]" />
              </div>
              <h1 className="text-lg font-bold text-slate-900">我的衣柜</h1>
              <span className="ml-auto text-xs font-medium text-slate-400">
                {filteredClothes.length} 件衣物
              </span>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {categories.map((cat) => (
                <motion.button
                  key={cat}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setActiveCategory(cat)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    activeCategory === cat
                      ? "bg-[#FE8F39] text-white shadow-lg shadow-[#FE8F39]/20"
                      : "bg-white text-slate-600 border border-slate-100"
                  }`}
                >
                  {categoryIcons[cat]}
                  {categoryLabels[cat]}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-5 pb-6">
            <div className="grid grid-cols-2 gap-3">
              {filteredClothes.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100"
                >
                  <div className="aspect-[3/4] relative overflow-hidden">
                    <img src={item.imageUrl} alt={item.name} className="w-full h-full object-cover" />
                    <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-lg">
                      <span className="text-[10px] font-bold text-slate-700">{item.color}</span>
                    </div>
                  </div>
                  <div className="p-3">
                    <h3 className="text-sm font-bold text-slate-800 truncate">{item.name}</h3>
                    <p className="text-[10px] text-slate-400 mt-0.5">{categoryLabels[item.category]}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <BottomNav />

      {/* 添加衣物按钮 */}
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsModalOpen(true)}
        className="fixed bottom-24 right-5 w-14 h-14 bg-[#FE8F39] rounded-full shadow-lg shadow-[#FE8F39]/30 flex items-center justify-center z-20"
      >
        <Plus size={24} className="text-white" />
      </motion.button>

      {/* 上传衣物模态框 */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-30">
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            className="bg-white w-full max-w-lg rounded-t-3xl p-6 max-h-[90vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-900">添加衣物</h2>
              <button
                onClick={closeModal}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center"
              >
                <X size={18} className="text-slate-600" />
              </button>
            </div>

            {/* 图片选择和预览 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                上传图片
              </label>
              <div
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-colors ${
                  previewUrl ? "border-[#FE8F39] bg-[#FE8F39]/5" : "border-slate-300 hover:border-[#FE8F39]"
                }`}
              >
                {previewUrl ? (
                  <div className="relative">
                    <img
                      src={previewUrl}
                      alt="预览"
                      className="max-h-48 mx-auto rounded-xl"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setPreviewUrl(null);
                      }}
                      className="absolute top-2 right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center"
                    >
                      <X size={14} className="text-white" />
                    </button>
                  </div>
                ) : (
                  <div>
                    <Upload size={32} className="mx-auto text-slate-400 mb-2" />
                    <p className="text-sm text-slate-600">点击或拖拽上传图片</p>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="absolute inset-0" />
              </div>
            </div>

            {/* 衣物信息表单 */}
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  描述
                </label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="例如：白色棉质T恤"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-[#FE8F39] transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  颜色（可选）
                </label>
                <input
                  type="text"
                  value={form.color || ""}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                  placeholder="例如：白色"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-[#FE8F39] transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  材质（可选）
                </label>
                <input
                  type="text"
                  value={form.material || ""}
                  onChange={(e) => setForm({ ...form, material: e.target.value })}
                  placeholder="例如：棉质"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-[#FE8F39] transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  场景（可选）
                </label>
                <select
                  value={form.scene || ""}
                  onChange={(e) => setForm({ ...form, scene: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-[#FE8F39] transition-colors bg-white"
                >
                  <option value="">请选择场景</option>
                  <option value="daily">日常</option>
                  <option value="work">工作</option>
                  <option value="formal">正式</option>
                  <option value="sport">运动</option>
                  <option value="date">约会</option>
                  <option value="party">派对</option>
                </select>
              </div>
            </div>

            {/* 错误提示 */}
            {uploadError && (
              <div className="mb-4 p-3 bg-red-50 rounded-xl">
                <p className="text-sm text-red-600">{uploadError}</p>
              </div>
            )}

            {/* 上传按钮 */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleUpload}
              disabled={isUploading || !selectedFile}
              className={`w-full py-4 rounded-xl font-bold transition-colors ${
                isUploading || !selectedFile
                  ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                  : "bg-[#FE8F39] text-white shadow-lg shadow-[#FE8F39]/20"
              }`}
            >
              {isUploading ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 size={20} className="animate-spin" />
                  <span>上传中...</span>
                </div>
              ) : (
                "添加衣物"
              )}
            </motion.button>
          </motion.div>
        </div>
      )}
    </div>
  );
}
