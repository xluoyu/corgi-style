import { Pool, PoolConfig } from "pg";

/**
 * 数据库配置接口
 */
interface DatabaseConfig {
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
  projectRef: string;
}

/**
 * 获取数据库配置
 * @returns 数据库配置对象
 */
function getDatabaseConfig(): DatabaseConfig {
  return {
    host: process.env.DB_HOST || "localhost",
    port: parseInt(process.env.DB_PORT || "5432", 10),
    user: process.env.DB_USER || "postgres",
    password: process.env.DB_PASSWORD || "",
    database: process.env.DB_NAME || "postgres",
    projectRef: process.env.DB_PROJECT_REF || "",
  };
}

/**
 * 创建数据库连接池配置
 * @returns PoolConfig 对象
 */
function createPoolConfig(): PoolConfig {
  const config = getDatabaseConfig();
  return {
    host: config.host,
    port: config.port,
    user: config.user,
    password: config.password,
    database: config.database,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
    ssl: {
      rejectUnauthorized: false,
    },
  };
}

let pool: Pool | null = null;

/**
 * 获取数据库连接池（单例模式）
 * @returns PostgreSQL 连接池实例
 */
export function getPool(): Pool {
  if (!pool) {
    pool = new Pool(createPoolConfig());
  }
  return pool;
}

/**
 * 执行数据库查询
 * @param text - SQL 查询语句
 * @param params - 查询参数
 * @returns 查询结果
 */
export async function query<T = unknown>(text: string, params?: unknown[]) {
  const pool = getPool();
  const start = Date.now();
  const result = await pool.query<T>(text, params);
  const duration = Date.now() - start;
  console.log("Executed query", { text: text.substring(0, 100), duration, rows: result.rowCount });
  return result;
}

/**
 * 关闭数据库连接池
 */
export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
  }
}

/**
 * 测试数据库连接
 * @returns 连接是否成功
 */
export async function testConnection(): Promise<boolean> {
  try {
    const result = await query("SELECT NOW()");
    console.log("Database connection successful:", result.rows[0]);
    return true;
  } catch (error) {
    console.error("Database connection failed:", error);
    return false;
  }
}
