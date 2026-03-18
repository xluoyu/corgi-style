import React from "react";
import { WeatherHeader } from "./components/WeatherHeader";
import { ClothingGuide } from "./components/ClothingGuide";
import { TodayHighlight } from "./components/TodayHighlight";
import { FeatureGrid } from "./components/FeatureGrid";
import {
  LayoutGrid,
  Palette,
  BookOpen,
  User,
  Plus,
} from "lucide-react";
import { motion } from "motion/react";

const App: React.FC = () => {
  const heroImage =
    "https://images.unsplash.com/photo-1700557478776-952a33fda578?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWwlMjBzdHJlZXQlMjBzdHlsZSUyMG91dGZpdHxlbnwxfHx8fDE3NzIxMDk2MDZ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral";

  return (
    <div className="h-screen bg-[#F1F4F9] flex flex-col font-sans text-slate-900 overflow-hidden relative">
      {/* Soft gradient overlay for depth */}
      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-blue-100/30 to-transparent pointer-events-none" />

      <main className="flex-1 flex flex-col overflow-hidden relative z-10">
        {/* Top Section: Weather & Guide */}
        <div className="px-5 pt-4 pb-4 flex flex-col gap-4">
          <WeatherHeader />
          <ClothingGuide />
        </div>

        {/* Bottom Section: Smart Control Panel */}
        <div className="flex-1 bg-white rounded-t-[40px] shadow-[0_-12px_48px_rgba(15,23,42,0.08)] px-5 pt-8 flex flex-col gap-6 overflow-hidden">
          {/* Feature Icons Grid */}
          <section>
            <FeatureGrid />
          </section>

          {/* Today's Recommendation Banner */}
          <section className="flex-1 flex flex-col min-h-0 mb-6">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                今日主打推荐
              </h2>
              <button className="text-[10px] font-bold text-[#FE8F39] hover:bg-orange-50 px-2.5 py-1 rounded-full transition-colors border border-orange-100">
                换一批
              </button>
            </div>
            <TodayHighlight imageUrl={heroImage} />
          </section>
        </div>
      </main>

      {/* iOS Style Navigation Bar */}
      <div className="px-5 pb-10 pt-2 relative z-20">
        <div className="flex items-center gap-3 h-[68px]">
          {/* Main Navigation - Glassmorphic Left Block */}
          <nav className="flex-1 h-full bg-white/70 backdrop-blur-xl rounded-[28px] border border-white/40 shadow-[0_10px_30px_rgba(0,0,0,0.04)] flex items-center justify-around px-3">
            <NavItem
              icon={<LayoutGrid size={22} />}
              active
              label="首页"
            />
            <NavItem
              icon={<Palette size={22} />}
              label="衣橱"
            />
            <NavItem
              icon={<BookOpen size={22} />}
              label="方案"
            />
            <NavItem icon={<User size={22} />} label="我的" />
          </nav>

          {/* Independent Add Button - Right Block */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            className="w-[68px] h-full bg-[#FE8F39] rounded-[28px] flex items-center justify-center text-white shadow-xl shadow-[#FE8F39]/25 border border-[#FE8F39]/20"
          >
            <Plus size={30} strokeWidth={2.5} />
          </motion.button>
        </div>
      </div>
    </div>
  );
};

const NavItem: React.FC<{
  icon: React.ReactNode;
  active?: boolean;
  label: string;
}> = ({ icon, active, label }) => (
  <button
    className={`flex flex-col items-center justify-center gap-1 flex-1 transition-all ${active ? "text-[#FE8F39]" : "text-slate-400"}`}
  >
    <div
      className={`${active ? "scale-110" : "scale-100"} transition-transform`}
    >
      {icon}
    </div>
    <span className="text-[10px] font-bold tracking-tight">
      {label}
    </span>
    {active && (
      <motion.div
        layoutId="navIndicator"
        className="w-1 h-1 bg-[#FE8F39] rounded-full absolute bottom-2"
      />
    )}
  </button>
);

export default App;