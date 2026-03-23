import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from sqlalchemy import text
from app.database import engine

def migrate():
    """
    数据库迁移脚本
    将旧表迁移到新的 users/user_profiles/clothing_items 表
    """
    with engine.connect() as conn:
        print("开始数据库迁移...")

        print("\n1. 创建新表 users...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
                last_active_at TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✅ users 表创建完成")

        print("\n2. 创建新表 user_profiles...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                gender VARCHAR(20),
                style_preferences TEXT,
                season_preference TEXT,
                default_occasion VARCHAR(50) DEFAULT 'casual',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✅ user_profiles 表创建完成")

        print("\n3. 创建新表 clothing_items...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clothing_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category VARCHAR(50) NOT NULL,
                sub_category VARCHAR(100),
                original_image_url VARCHAR(500) NOT NULL,
                cartoon_image_url VARCHAR(500),
                color VARCHAR(32),
                material VARCHAR(64),
                temperature_range VARCHAR(50),
                tags TEXT,
                wear_count INTEGER DEFAULT 0,
                last_worn_at TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                analysis_completed INTEGER DEFAULT 0,
                generated_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✅ clothing_items 表创建完成")

        print("\n4. 创建新表 outfit_histories...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS outfit_histories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                occasion VARCHAR(50) NOT NULL,
                outfit_snapshot TEXT,
                weather_snapshot TEXT,
                top_clothes_id UUID REFERENCES clothing_items(id),
                pants_clothes_id UUID REFERENCES clothing_items(id),
                outer_clothes_id UUID REFERENCES clothing_items(id),
                inner_clothes_id UUID REFERENCES clothing_items(id),
                accessory_clothes_id UUID REFERENCES clothing_items(id),
                create_time TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✅ outfit_histories 表创建完成")

        print("\n5. 创建新表 outfit_feedback...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS outfit_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                outfit_id UUID NOT NULL REFERENCES outfit_histories(id),
                rating INTEGER NOT NULL,
                feedback_text TEXT,
                create_time TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✅ outfit_feedback 表创建完成")

        print("\n6. 创建索引...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_fingerprint ON users(device_fingerprint)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clothing_user_id ON clothing_items(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clothing_category ON clothing_items(category)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outfit_user_id ON outfit_histories(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON outfit_feedback(user_id)"))
        conn.commit()
        print("   ✅ 索引创建完成")

        print("\n数据库迁移完成！")
        print("\n注意: 旧表如果存在，可以手动删除")

if __name__ == "__main__":
    migrate()