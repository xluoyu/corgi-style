-- ClosetAI / 衣橱管家 - PostgreSQL 数据库 Schema
-- 版本: V2.0
-- 日期: 2026-03-23
-- 优化: 基于 Supabase Postgres Best Practices

-- =============================================================================
-- 第一部分：扩展与基础设置
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS auth;

-- =============================================================================
-- 第二部分：创建表
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 用户表 (users)
-- 存储用户基本信息，通过浏览器指纹识别
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_fingerprint TEXT UNIQUE NOT NULL,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_fingerprint ON users(device_fingerprint);
CREATE INDEX idx_users_last_active ON users(last_active_at);

COMMENT ON TABLE users IS '用户表，通过浏览器指纹识别';
COMMENT ON COLUMN users.device_fingerprint IS '浏览器指纹';
COMMENT ON COLUMN users.last_active_at IS '最后活跃时间';

-- -----------------------------------------------------------------------------
-- 用户画像表 (user_profiles)
-- 存储用户的个性化偏好数据
-- -----------------------------------------------------------------------------
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gender TEXT,
    style_preferences JSONB DEFAULT '[]',
    season_preference JSONB DEFAULT '[]',
    default_occasion TEXT DEFAULT 'casual',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_profile UNIQUE (user_id)
);

CREATE INDEX idx_profiles_user_id ON user_profiles(user_id);

COMMENT ON TABLE user_profiles IS '用户画像表，存储个性化偏好';
COMMENT ON COLUMN user_profiles.gender IS '性别：male/female/other';
COMMENT ON COLUMN user_profiles.style_preferences IS '风格偏好列表，如 ["minimalist", "business"]';
COMMENT ON COLUMN user_profiles.season_preference IS '季节偏好列表，如 ["spring", "autumn"]';
COMMENT ON COLUMN user_profiles.default_occasion IS '默认场合，如 casual/work/formal';

-- -----------------------------------------------------------------------------
-- 衣物表 (clothing_items)
-- 核心资产表，存储用户衣橱中的每件衣物
-- -----------------------------------------------------------------------------
CREATE TABLE clothing_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    sub_category TEXT,
    original_image_url TEXT NOT NULL,
    cartoon_image_url TEXT,
    color TEXT,
    material TEXT,
    temperature_range TEXT,
    tags JSONB NOT NULL DEFAULT '{}',
    wear_count INTEGER DEFAULT 0,
    last_worn_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    analysis_completed INTEGER DEFAULT 0,
    generated_completed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_category CHECK (category IN ('top', 'pants', 'outer', 'inner', 'accessory')),
    CONSTRAINT chk_temperature_range CHECK (temperature_range IS NULL OR temperature_range IN ('summer', 'spring_autumn', 'winter', 'all_season'))
);

CREATE INDEX idx_clothing_user_id ON clothing_items(user_id);
CREATE INDEX idx_clothing_category ON clothing_items(category);
CREATE INDEX idx_clothing_deleted ON clothing_items(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_clothing_tags ON clothing_items USING GIN(tags);

COMMENT ON TABLE clothing_items IS '衣物表，核心资产';
COMMENT ON COLUMN clothing_items.category IS '一级分类：top/pants/outer/inner/accessory';
COMMENT ON COLUMN clothing_items.sub_category IS '二级分类：如 t-shirt/shirt/jeans/sneakers';
COMMENT ON COLUMN clothing_items.original_image_url IS '原始图片URL';
COMMENT ON COLUMN clothing_items.cartoon_image_url IS '卡通图片URL';
COMMENT ON COLUMN clothing_items.tags IS '属性标签JSON，包含 colors/materials/styles/occasions/seasons/thickness';
COMMENT ON COLUMN clothing_items.is_deleted IS '软删除标记';
COMMENT ON COLUMN clothing_items.deleted_at IS '删除时间，用于3天后彻底清理';

-- -----------------------------------------------------------------------------
-- 穿搭历史表 (outfit_histories)
-- 记录用户采纳的穿搭方案快照
-- -----------------------------------------------------------------------------
CREATE TABLE outfit_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    occasion TEXT NOT NULL,
    outfit_name TEXT,
    outfit_snapshot JSONB NOT NULL DEFAULT '{}',
    weather_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_occasion CHECK (occasion IN ('casual', 'work', 'formal', 'sport', 'date', 'party'))
);

CREATE INDEX idx_outfit_user_id ON outfit_histories(user_id);
CREATE INDEX idx_outfit_created_at ON outfit_histories(created_at);
CREATE INDEX idx_outfit_occasion ON outfit_histories(occasion);

COMMENT ON TABLE outfit_histories IS '穿搭历史表，记录用户采纳的穿搭';
COMMENT ON COLUMN outfit_histories.occasion IS '场合：casual/work/formal/sport/date/party';
COMMENT ON COLUMN outfit_histories.outfit_name IS '穿搭名称/备注，如"周一通勤搭配"';
COMMENT ON COLUMN outfit_histories.outfit_snapshot IS '穿搭衣物快照，JSON格式包含各品类衣物信息';
COMMENT ON COLUMN outfit_histories.weather_snapshot IS '当天天气快照';

-- -----------------------------------------------------------------------------
-- 穿搭反馈表 (outfit_feedback)
-- 存储用户对穿搭的评分和反馈
-- -----------------------------------------------------------------------------
CREATE TABLE outfit_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outfit_id UUID NOT NULL REFERENCES outfit_histories(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5)
);

CREATE INDEX idx_feedback_user_id ON outfit_feedback(user_id);
CREATE INDEX idx_feedback_outfit_id ON outfit_feedback(outfit_id);

COMMENT ON TABLE outfit_feedback IS '穿搭反馈表';
COMMENT ON COLUMN outfit_feedback.rating IS '评分（1-5分）';
COMMENT ON COLUMN outfit_feedback.feedback_text IS '文字反馈';

-- -----------------------------------------------------------------------------
-- 穿搭缓存表 (outfit_cache)
-- 今日主打推荐的图片缓存
-- -----------------------------------------------------------------------------
CREATE TABLE outfit_cache (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    temperature REAL NOT NULL,
    temperature_range TEXT NOT NULL,
    scene TEXT NOT NULL,
    image_url TEXT NOT NULL,
    description TEXT,
    outfit_items JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_temperature_range CHECK (temperature_range IN ('summer', 'spring_autumn', 'winter')),
    CONSTRAINT chk_scene CHECK (scene IN ('daily', 'work', 'sport', 'date', 'party'))
);

CREATE INDEX idx_cache_lookup ON outfit_cache(city, temperature_range, scene);
CREATE INDEX idx_cache_city ON outfit_cache(city);
CREATE INDEX idx_cache_temperature_range ON outfit_cache(temperature_range);
CREATE INDEX idx_cache_scene ON outfit_cache(scene);

COMMENT ON TABLE outfit_cache IS '穿搭缓存表，用于今日推荐图片缓存';
COMMENT ON COLUMN outfit_cache.city IS '城市';
COMMENT ON COLUMN outfit_cache.temperature IS '温度值';
COMMENT ON COLUMN outfit_cache.temperature_range IS '温度范围：summer/spring_autumn/winter';
COMMENT ON COLUMN outfit_cache.scene IS '场景：daily/work/sport/date/party';
COMMENT ON COLUMN outfit_cache.image_url IS '穿搭图片URL';
COMMENT ON COLUMN outfit_cache.outfit_items IS '搭配单品列表';

-- =============================================================================
-- 第三部分：触发器
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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

CREATE OR REPLACE FUNCTION set_user_id(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_user_id', user_uuid::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
  RETURN NULLIF(current_setting('app.current_user_id', true), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- 第五部分：Row Level Security 策略
-- =============================================================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_profiles_user_policy ON user_profiles;
CREATE POLICY user_profiles_user_policy ON user_profiles
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

ALTER TABLE clothing_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE clothing_items FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clothing_items_user_policy ON clothing_items;
CREATE POLICY clothing_items_user_policy ON clothing_items
    FOR ALL
    USING (user_id = (SELECT current_user_id()))
    WITH CHECK (user_id = (SELECT current_user_id()));

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

CREATE OR REPLACE FUNCTION get_wardrobe_stats(user_uuid UUID)
RETURNS TABLE (
    category TEXT,
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

CREATE OR REPLACE FUNCTION get_underused_clothes(user_uuid UUID)
RETURNS TABLE (
    id UUID,
    category TEXT,
    sub_category TEXT,
    wear_count INTEGER,
    last_worn_at TIMESTAMPTZ
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
-- 第七部分：定时清理任务
-- =============================================================================

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
