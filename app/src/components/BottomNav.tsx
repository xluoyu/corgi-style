"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  Palette,
  User,
  Plus,
  Camera,
  Link as LinkIcon,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

/**
 * BottomNav - 底部导航栏组件
 * 包含首页、衣柜、我的三个导航项和一个添加按钮
 */
export function BottomNav() {
  const pathname = usePathname();
  const [showAddMenu, setShowAddMenu] = useState(false);
  const addButtonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (addButtonRef.current && !addButtonRef.current.contains(event.target as Node)) {
        setShowAddMenu(false);
      }
    };
    if (showAddMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showAddMenu]);

  const handleAddClick = () => {
    setShowAddMenu(!showAddMenu);
  };

  const handleMenuItemClick = (action: string) => {
    setShowAddMenu(false);
    console.log("Action:", action);
  };

  const isActive = (path: string) => {
    if (path === "/" && pathname === "/") return true;
    if (path !== "/" && pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 px-5 pb-6 pt-2 z-30">
      <div className="flex items-center justify-center gap-3 h-16">
        <nav className="flex-1 h-full bg-white/70 backdrop-blur-xl rounded-[28px] border border-white/40 shadow-[0_10px_30px_rgba(0,0,0,0.04)] flex items-center justify-around px-3">
          <NavItem
            icon={<LayoutGrid size={22} />}
            active={isActive("/")}
            href="/"
            label="首页"
          />
          <NavItem
            icon={<Palette size={22} />}
            active={isActive("/wardrobe")}
            href="/wardrobe"
            label="衣柜"
          />
          <NavItem
            icon={<User size={22} />}
            active={isActive("/profile")}
            href="/profile"
            label="我的"
          />
        </nav>

        <div className="relative" ref={addButtonRef}>
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleAddClick}
            className="h-14 w-14 bg-[#FE8F39] rounded-[28px] flex items-center justify-center text-white shadow-xl shadow-[#FE8F39]/25 border border-[#FE8F39]/20"
          >
            <Plus size={26} strokeWidth={2.5} className={showAddMenu ? "rotate-45" : ""} />
          </motion.button>

          <AnimatePresence>
            {showAddMenu && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, x: -10 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.8, x: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute bottom-full right-0 mb-3 mr-7 w-44 bg-white/95 backdrop-blur-xl rounded-2xl border border-white/40 shadow-2xl shadow-slate-900/10 overflow-hidden"
              >
                <div className="absolute -bottom-2 right-6 w-4 h-4 bg-white/95 border-r border-b border-slate-100 transform rotate-45" />
                <div className="relative z-10 py-2">
                  <button
                    onClick={() => handleMenuItemClick("camera")}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
                  >
                    <div className="w-8 h-8 bg-rose-50 rounded-xl flex items-center justify-center">
                      <Camera size={16} className="text-rose-500" />
                    </div>
                    <span className="text-sm font-bold text-slate-700">拍照上传</span>
                  </button>
                  <button
                    onClick={() => handleMenuItemClick("link")}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-50 rounded-xl flex items-center justify-center">
                      <LinkIcon size={16} className="text-blue-500" />
                    </div>
                    <span className="text-sm font-bold text-slate-700">复制链接</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/**
 * NavItem - 导航项组件
 */
function NavItem({
  icon,
  active,
  href,
  label,
}: {
  icon: React.ReactNode;
  active?: boolean;
  href: string;
  label: string;
}) {
  return (
    <Link
      href={href}
      className={`flex flex-col items-center justify-center gap-1 flex-1 transition-all ${active ? "text-[#FE8F39]" : "text-slate-400"}`}
    >
      <div className={`${active ? "scale-110" : "scale-100"} transition-transform relative`}>
        {icon}
      </div>
      <span className="text-[10px] font-bold tracking-tight">{label}</span>
    </Link>
  );
}
