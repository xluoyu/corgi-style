'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Globe, Upload, Loader2, CheckCircle } from 'lucide-react';
import type { OutfitCollectionItem } from '@/types/collection';
import { addCollectionByUrl, addCollectionByUpload } from '@/lib/api/collection';

interface AddCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (item: OutfitCollectionItem) => void;
}

type AddMode = 'select' | 'url' | 'upload';

export function AddCollectionModal({ isOpen, onClose, onSuccess }: AddCollectionModalProps) {
  const [mode, setMode] = useState<AddMode>('select');
  const [urlInput, setUrlInput] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClose = () => {
    setMode('select');
    setUrlInput('');
    setPreviewUrl(null);
    setSelectedFile(null);
    setError(null);
    onClose();
  };

  const handleUrlInputChange = (value: string) => {
    setUrlInput(value);
    setError(null);
    // 简单的 URL 验证
    if (value && (value.startsWith('http://') || value.startsWith('https://'))) {
      setPreviewUrl(value);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim()) {
      setError('请输入图片 URL');
      return;
    }
    if (!urlInput.startsWith('http')) {
      setError('请输入有效的 URL（以 http:// 或 https:// 开头）');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const newItem = await addCollectionByUrl(urlInput.trim());
      onSuccess(newItem);
      handleClose();
    } catch (err) {
      setError('添加失败，请重试');
      console.error('添加穿搭失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        setError('请选择图片文件');
        return;
      }
      // 验证文件大小（最大 10MB）
      if (file.size > 10 * 1024 * 1024) {
        setError('图片大小不能超过 10MB');
        return;
      }
      setSelectedFile(file);
      setError(null);
      // 生成预览
      const reader = new FileReader();
      reader.onload = (e) => setPreviewUrl(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) {
      setError('请选择图片');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const newItem = await addCollectionByUpload(selectedFile);
      onSuccess(newItem);
      handleClose();
    } catch (err) {
      setError('上传失败，请重试');
      console.error('上传穿搭失败:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="bg-white rounded-3xl w-full max-w-md shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">添加穿搭</h3>
              <button
                onClick={handleClose}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4">
              {mode === 'select' && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500 text-center mb-6">
                    选择添加方式
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={() => setMode('url')}
                      className="flex flex-col items-center gap-3 p-6 bg-blue-50 border border-blue-100 rounded-2xl hover:bg-blue-100 transition-colors"
                    >
                      <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
                        <Globe className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-slate-900">URL 链接</p>
                        <p className="text-xs text-slate-500 mt-1">粘贴图片地址</p>
                      </div>
                    </button>
                    <button
                      onClick={() => setMode('upload')}
                      className="flex flex-col items-center gap-3 p-6 bg-emerald-50 border border-emerald-100 rounded-2xl hover:bg-emerald-100 transition-colors"
                    >
                      <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center">
                        <Upload className="w-6 h-6 text-white" />
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-slate-900">本地上传</p>
                        <p className="text-xs text-slate-500 mt-1">选择相册图片</p>
                      </div>
                    </button>
                  </div>
                </div>
              )}

              {mode === 'url' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      图片 URL
                    </label>
                    <input
                      type="text"
                      value={urlInput}
                      onChange={(e) => handleUrlInputChange(e.target.value)}
                      placeholder="https://example.com/image.jpg"
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FE8F39] focus:border-transparent"
                    />
                  </div>

                  {/* 预览 */}
                  {previewUrl && (
                    <div className="relative aspect-[3/4] bg-slate-100 rounded-xl overflow-hidden">
                      <img
                        src={previewUrl}
                        alt="预览"
                        className="w-full h-full object-cover"
                        onError={() => setPreviewUrl(null)}
                      />
                    </div>
                  )}

                  {error && (
                    <p className="text-sm text-red-500">{error}</p>
                  )}

                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setMode('select');
                        setError(null);
                      }}
                      className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-medium text-sm hover:bg-slate-50 transition-colors"
                    >
                      返回
                    </button>
                    <button
                      onClick={handleUrlSubmit}
                      disabled={loading || !previewUrl}
                      className="flex-1 py-3 rounded-xl bg-[#FE8F39] text-white font-medium text-sm hover:bg-[#e07d2a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                      确认添加
                    </button>
                  </div>
                </div>
              )}

              {mode === 'upload' && (
                <div className="space-y-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {!selectedFile ? (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full aspect-[3/4] bg-slate-50 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center gap-3 hover:bg-slate-100 transition-colors"
                    >
                      <div className="w-12 h-12 bg-slate-200 rounded-xl flex items-center justify-center">
                        <Upload className="w-6 h-6 text-slate-400" />
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-slate-600">点击选择图片</p>
                        <p className="text-xs text-slate-400 mt-1">支持 JPG、PNG，最大 10MB</p>
                      </div>
                    </button>
                  ) : (
                    <div className="relative aspect-[3/4] bg-slate-100 rounded-xl overflow-hidden">
                      <img
                        src={previewUrl || ''}
                        alt="预览"
                        className="w-full h-full object-cover"
                      />
                      <button
                        onClick={() => {
                          setSelectedFile(null);
                          setPreviewUrl(null);
                          if (fileInputRef.current) fileInputRef.current.value = '';
                        }}
                        className="absolute top-2 right-2 w-8 h-8 bg-black/50 rounded-full flex items-center justify-center hover:bg-black/70 transition-colors"
                      >
                        <X className="w-4 h-4 text-white" />
                      </button>
                    </div>
                  )}

                  {error && (
                    <p className="text-sm text-red-500">{error}</p>
                  )}

                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setMode('select');
                        setError(null);
                      }}
                      className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-medium text-sm hover:bg-slate-50 transition-colors"
                    >
                      返回
                    </button>
                    <button
                      onClick={handleUploadSubmit}
                      disabled={loading || !selectedFile}
                      className="flex-1 py-3 rounded-xl bg-[#FE8F39] text-white font-medium text-sm hover:bg-[#e07d2a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                      上传添加
                    </button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
