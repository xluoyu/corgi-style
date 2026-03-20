-- ClosetAI / 衣橱管家 - PostgreSQL 数据库 Schema
-- 版本: V1.1
-- 日期: 2026-03-20

-- =============================================================================
-- 第一部分：扩展与基础设置
-- =============================================================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 创建认证相关 schema
CREATE SCHEMA IF NOT EXISTS auth;

-- =============================================================================
-- 第二部分：创建表
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 用户表 (users)
-- 存储用户基本信息，通过浏览器指纹识别
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    last_active_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE users IS '用户表，通过浏览器指纹识别';
COMMENT ON COLUMN users.device_fingerprint IS '浏览器指纹';
COMMENT ON COLUMN users.last_active_at IS '最后活跃时间';

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_fingerprint ON users(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active_at);

-- -----------------------------------------------------------------------------
-- 用户画像表 (user_profiles)
-- 存储用户的个性化偏好数据
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gender VARCHAR(20),
    style_preferences JSONB DEFAULT '[]',
    season_preference JSONB DEFAULT '[]',
    default_occasion VARCHAR(50) DEFAULT 'casual',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_profile UNIQUE (user_id)
);

COMMENT ON TABLE user_profiles IS '用户画像表，存储个性化偏好';
COMMENT ON COLUMN user_profiles.style_preferences IS '风格偏好列表，如 ["minimalist", "business"]';
COMMENT ON COLUMN user_profiles.season_preference IS '季节偏好列表，如 ["spring", "autumn"]';
COMMENT ON COLUMN user_profiles.default_occasion IS '默认场合，如 casual/work/formal';

-- 用户画像表索引
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON user_profiles(user_id);

-- -----------------------------------------------------------------------------
-- 衣物表 (clothing_items)
-- 核心资产表，存储用户衣橱中的每件衣物
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clothing_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100),
    original_image_url VARCHAR(500) NOT NULL,
    cartoon_image_url VARCHAR(500) NOT NULL,
    tags JSONB NOT NULL DEFAULT '{}',
    wear_count INTEGER DEFAULT 0,
    last_worn_at DATE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE clothing_items IS '衣物表，核心资产';
COMMENT ON COLUMN clothing_items.category IS '一级分类：top/bottom/outerwear/dress/shoes/accessory';
COMMENT ON COLUMN clothing_items.sub_category IS '二级分类：如 t-shirt/shirt/jeans/sneakers';
COMMENT ON COLUMN clothing_items.original_image_url IS '原始图片URL';
COMMENT ON COLUMN clothing_items.cartoon_image_url IS '卡通图片URL';
COMMENT ON COLUMN clothing_items.tags IS '属性标签JSON，包含 colors/materials/styles/occasions/seasons/thickness';
COMMENT ON COLUMN clothing_items.is_deleted IS '软删除标记';
COMMENT ON COLUMN clothing_items.deleted_at IS '删除时间，用于3天后彻底清理';

-- 衣物表索引
CREATE INDEX IF NOT EXISTS idx_clothing_user_id ON clothing_items(user_id);
CREATE INDEX IF NOT EXISTS idx_clothing_category ON clothing_items(category);
CREATE INDEX IF NOT EXISTS idx_clothing_deleted ON clothing_items(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_clothing_tags ON clothing_items USING GIN(tags);

-- -----------------------------------------------------------------------------
-- 穿搭历史表 (outfit_histories)
-- 记录用户采纳的穿搭方案快照
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outfit_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    occasion VARCHAR(50) NOT NULL,
    outfit_snapshot JSONB NOT NULL,
    weather_snapshot JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE outfit_histories IS '穿搭历史表，记录用户采纳的穿搭';
COMMENT ON COLUMN outfit_histories.occasion IS '场合：casual/work/formal/sport/date/party';
COMMENT ON COLUMN outfit_histories.outfit_snapshot IS '穿搭衣物快照，JSON格式包含各品类衣物信息';
COMMENT ON COLUMN outfit_histories.weather_snapshot IS '当天天气快照';

-- 穿搭历史表索引
CREATE INDEX IF NOT EXISTS idx_outfit_user_id ON outfit_histories(user_id);
CREATE INDEX IF NOT EXISTS idx_outfit_created_at ON outfit_histories(created_at);
CREATE INDEX IF NOT EXISTS idx_outfit_occasion ON outfit_histories(occasion);

-- =============================================================================
-- 第三部分：触发器
-- =============================================================================

-- 自动更新 updated_at 字段的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有表创建更新触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_clothing_updated_at ON clothing_items;
CREATE TRIGGER update_clothing_updated_at
    BEFORE UPDATE ON clothing_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 第四部分：RLS 辅助函数
-- =============================================================================

-- 设置当前用户上下文（供后端调用）
CREATE OR REPLACE FUNCTION set_user_id(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_user_id', user_uuid::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 获取当前用户 ID（用于 RLS 策略）
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
  RETURN NULLIF(current_setting('app.current_user_id', true), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- 第五部分：Row Level Security 策略
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 用户画像表 RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_profiles_user_policy ON user_profiles;
CREATE POLICY user_profiles_user_policy ON user_profiles
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

-- 衣物表 RLS
ALTER TABLE clothing_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE clothing_items FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clothing_items_user_policy ON clothing_items;
CREATE POLICY clothing_items_user_policy ON clothing_items
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

-- 穿搭历史表 RLS
ALTER TABLE outfit_histories ENABLE ROW LEVEL SECURITY;
ALTER TABLE outfit_histories FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS outfit_histories_user_policy ON outfit_histories;
CREATE POLICY outfit_histories_user_policy ON outfit_histories
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

-- -----------------------------------------------------------------------------
-- 衣物表 RLS
-- -----------------------------------------------------------------------------
ALTER TABLE clothing_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE clothing_items FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clothing_items_user_policy ON clothing_items;
CREATE POLICY clothing_items_user_policy ON clothing_items
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

-- -----------------------------------------------------------------------------
-- 穿搭历史表 RLS
-- -----------------------------------------------------------------------------
ALTER TABLE outfit_histories ENABLE ROW LEVEL SECURITY;
ALTER TABLE outfit_histories FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS outfit_histories_user_policy ON outfit_histories;
CREATE POLICY outfit_histories_user_policy ON outfit_histories
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

-- =============================================================================
-- 第六部分：辅助函数与视图
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 获取用户衣物统计
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_wardrobe_stats(user_uuid UUID)
RETURNS TABLE (
    category VARCHAR(50),
    total_count BIGINT,
    avg_wear_count NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.category,
        COUNT(*)::BIGINT as total_count,
        AVG(ci.wear_count)::NUMERIC(10, 2) as avg_wear_count
    FROM clothing_items ci
    WHERE ci.user_id = user_uuid
      AND ci.is_deleted = FALSE
    GROUP BY ci.category;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 获取用户穿搭历史（最近30天）
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW recent_outfits AS
SELECT
    oh.id,
    oh.user_id,
    oh.occasion,
    oh.created_at,
    oh.weather_snapshot,
    jsonb_build_object(
        'top', oh.outfit_snapshot->>'top',
        'bottom', oh.outfit_snapshot->>'bottom',
        'shoes', oh.outfit_snapshot->>'shoes'
    ) as outfit_summary
FROM outfit_histories oh
WHERE oh.created_at >= NOW() - INTERVAL '30 days';

-- -----------------------------------------------------------------------------
-- 获取未被充分利用的衣物（穿着次数 < 3 且 30天未穿）
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_underused_clothes(user_uuid UUID)
RETURNS TABLE (
    id UUID,
    category VARCHAR(50),
    sub_category VARCHAR(100),
    wear_count INTEGER,
    last_worn_at DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.id,
        ci.category,
        ci.sub_category,
        ci.wear_count,
        ci.last_worn_at
    FROM clothing_items ci
    WHERE ci.user_id = user_uuid
      AND ci.is_deleted = FALSE
      AND ci.wear_count < 3
      AND (ci.last_worn_at IS NULL OR ci.last_worn_at < NOW() - INTERVAL '30 days')
    ORDER BY ci.last_worn_at NULLS FIRST;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- 第七部分：定时清理任务（示例）
-- =============================================================================

-- 清理超过3天的已删除衣物
-- 建议使用 pg_cron 或外部调度器执行：
--
-- SELECT cron.schedule(
--     'cleanup_deleted_clothes',
--     '0 3 * * *',
--     $$DELETE FROM clothing_items WHERE is_deleted = TRUE AND deleted_at < NOW() - INTERVAL '3 days'$$
-- );
--
-- 或创建手动清理函数供外部调用：
CREATE OR REPLACE FUNCTION cleanup_deleted_clothes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM clothing_items
        WHERE is_deleted = TRUE
          AND deleted_at < NOW() - INTERVAL '3 days'
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- 完成
-- =============================================================================
