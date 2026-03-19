import { NextResponse } from "next/server";
import { testConnection } from "@/lib/db";

/**
 * GET /api/health
 * 健康检查接口，测试数据库连接
 */
export async function GET() {
  try {
    const dbConnected = await testConnection();
    
    return NextResponse.json({
      status: "ok",
      timestamp: new Date().toISOString(),
      database: dbConnected ? "connected" : "disconnected",
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
