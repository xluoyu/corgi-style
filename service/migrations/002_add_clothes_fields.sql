-- 迁移：为 clothing_items 表添加 name/wear_method/scene 字段
-- 日期: 2026-03-24

ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS wear_method TEXT;
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS scene TEXT;

-- 添加 CHECK 约束（如列已存在但约束不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_wear_method'
    ) THEN
        ALTER TABLE clothing_items ADD CONSTRAINT chk_wear_method
            CHECK (wear_method IS NULL OR wear_method IN ('inner_wear', 'outer_wear', 'single_wear', 'layering'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_scene'
    ) THEN
        ALTER TABLE clothing_items ADD CONSTRAINT chk_scene
            CHECK (scene IS NULL OR scene IN ('daily', 'work', 'sport', 'date', 'party'));
    END IF;
END $$;

COMMENT ON COLUMN clothing_items.name IS 'AI自动生成的衣物名称';
COMMENT ON COLUMN clothing_items.wear_method IS '穿着方式：inner_wear/outer_wear/single_wear/layering';
COMMENT ON COLUMN clothing_items.scene IS '适用场景：daily/work/sport/date/party';
