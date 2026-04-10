-- 风格知识库表
CREATE TABLE IF NOT EXISTS style_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    tags TEXT NOT NULL DEFAULT '[]',  -- JSON array
    rules TEXT NOT NULL DEFAULT '{}',  -- JSON object
    colors TEXT NOT NULL DEFAULT '[]',  -- JSON array
    occasion VARCHAR(50),  -- 适用场合
    season VARCHAR(50),  -- 适用季节
    temperature_range VARCHAR(50),
    is_builtin BOOLEAN DEFAULT false,
    user_id UUID REFERENCES users(id),  -- NULL 表示内置风格
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户偏好表
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    disliked_colors TEXT DEFAULT '[]',  -- JSON array
    disliked_styles TEXT DEFAULT '[]',  -- JSON array
    body_conditions TEXT DEFAULT '{}',  -- JSON object: {"cold_sensitive": true, ...}
    shopping_budget VARCHAR(50),  -- 购物预算：low/medium/high
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预设内置风格数据
INSERT INTO style_knowledge (name, description, tags, rules, colors, occasion, season, is_builtin) VALUES
(
    '美式复古',
    '20世纪50-70年代美国风格，代表元素：牛仔、工装、丹宁',
    '["牛仔", "工装", "复古", "丹宁", "皮带", "靴子"]',
    '{"base_items": ["牛仔外套", "工装裤", "白色T恤", "皮靴"], "color_palette": ["深蓝", "浅蓝", "白色", "卡其", "棕色"], "patterns": ["条纹", "格子", "丹宁"], "accessories": ["皮带", "棒球帽", "工装靴"]}',
    '["深蓝", "浅蓝", "白色", "卡其", "棕色"]',
    'daily',
    'spring_autumn',
    true
),
(
    '日系简约',
    '日本街头简约风格，强调基础款、棉麻、素色',
    '["基础款", "棉麻", "素色", "宽松", "文艺"]',
    '{"base_items": ["衬衫", "针织衫", "休闲裤", "帆布鞋"], "color_palette": ["白色", "米色", "灰色", "藏蓝", "军绿"], "patterns": ["纯色", "细条纹"], "accessories": ["帆布包", "渔夫帽"]}',
    '["白色", "米色", "灰色", "藏蓝", "军绿"]',
    'daily',
    'all_season',
    true
),
(
    '韩系通勤',
    '韩国时尚通勤风格，精致但不夸张',
    '["通勤", "精致", "西装裤", "衬衫", "高跟鞋"]',
    '{"base_items": ["衬衫", "西装裤", "针织开衫", "乐福鞋"], "color_palette": ["白色", "黑色", "灰色", "浅粉", "浅蓝"], "patterns": ["纯色", "微条纹"], "accessories": ["手表", "简约包包"]}',
    '["白色", "黑色", "灰色", "浅粉", "浅蓝"]',
    'work',
    'all_season',
    true
),
(
    '街头潮流',
    '年轻街头风格，宽松、个性、有态度',
    '["宽松", "印花", "卫衣", "运动裤", "球鞋"]',
    '{"base_items": ["卫衣", "运动裤", "棒球帽", "球鞋"], "color_palette": ["黑色", "白色", "红色", "荧光绿", "灰色"], "patterns": ["大印花", "logo", "拼接"], "accessories": ["棒球帽", "双肩包", "耳机"]}',
    '["黑色", "白色", "红色", "荧光绿", "灰色"]',
    'daily',
    'all_season',
    true
),
(
    '文艺清新',
    '文艺气质风格，碎花、蕾丝、自然',
    '["碎花", "蕾丝", "连衣裙", "草编", "自然"]',
    '{"base_items": ["碎花裙", "蕾丝上衣", "草编帽", "帆布鞋"], "color_palette": ["白色", "浅黄", "浅绿", "粉色", "淡蓝"], "patterns": ["碎花", "波点", "格纹"], "accessories": ["草编帽", "帆布包", "细项链"]}',
    '["白色", "浅黄", "浅绿", "粉色", "淡蓝"]',
    'date',
    'summer',
    true
),
(
    '商务正装',
    '正式商务场合着装',
    '["西装", "衬衫", "领带", "皮鞋", "正式"]',
    '{"base_items": ["西装", "衬衫", "西裤", "皮鞋"], "color_palette": ["黑色", "深灰", "深蓝", "白色"], "patterns": ["纯色", "细条纹"], "accessories": ["领带", "领夹", "皮带"]}',
    '["黑色", "深灰", "深蓝", "白色"]',
    'work',
    'all_season',
    true
) ON CONFLICT (name) DO NOTHING;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_style_knowledge_user_id ON style_knowledge(user_id);
CREATE INDEX IF NOT EXISTS idx_style_knowledge_is_builtin ON style_knowledge(is_builtin);
