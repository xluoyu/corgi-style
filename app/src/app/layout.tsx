import type { Metadata } from "next";
import "@/styles/globals.css";
import { UserProvider } from "@/components/UserProvider";

export const metadata: Metadata = {
  title: "Corgi Style - 智能穿搭助手",
  description: "AI驱动的个性化穿搭推荐应用",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <UserProvider>
          {children}
        </UserProvider>
      </body>
    </html>
  );
}