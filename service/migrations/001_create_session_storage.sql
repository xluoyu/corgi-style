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
