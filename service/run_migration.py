"""执行数据库迁移"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.database import engine, SessionLocal

MIGRATION_SQL = """
-- 对话式 Session 存储表
-- TTL: 3 天

CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_data JSONB NOT NULL DEFAULT '{}',
    messages JSONB NOT NULL DEFAULT '[]',
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '3 days')
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON conversation_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON conversation_sessions(last_active_at);

-- 注释
COMMENT ON TABLE conversation_sessions IS '对话 Session 存储表，TTL 3 天';
COMMENT ON COLUMN conversation_sessions.session_data IS '完整 Session 序列化数据';
COMMENT ON COLUMN conversation_sessions.messages IS '对话历史消息列表';
COMMENT ON COLUMN conversation_sessions.context IS '跨轮次上下文（目标城市/场景/当前穿搭）';
COMMENT ON COLUMN conversation_sessions.expires_at IS '过期时间，3 天后自动过期';
"""


def run_migration():
    with engine.connect() as conn:
        # 迁移 1：对话 Session 存储表
        for statement in MIGRATION_SQL.strip().split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                    print(f"[OK] {statement[:50]}...")
                except Exception as e:
                    print(f"[WARN] {e}")

        # 迁移 2：添加 name/wear_method/scene 字段
        migrations_002 = """
        ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS name TEXT;
        ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS wear_method TEXT;
        ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS scene TEXT;
        """
        for statement in migrations_002.strip().split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                    print(f"[OK] {statement[:50]}...")
                except Exception as e:
                    print(f"[WARN] {e}")

        conn.commit()

    # 验证表创建
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'conversation_sessions'"
        ))
        if result.fetchone():
            print("\n[M OK] Migration completed successfully!")
            print("Table 'conversation_sessions' created.")
        else:
            print("\n[FAIL] Migration may have failed - table not found")


if __name__ == "__main__":
    run_migration()
