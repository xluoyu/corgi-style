import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from sqlalchemy import text
from app.database import engine

def fix_missing_columns():
    with engine.connect() as conn:
        columns_to_add = [
            ("material", "VARCHAR(64)"),
            ("scene", "VARCHAR(32)"),
            ("wear_method", "VARCHAR(32)"),
            ("brand", "VARCHAR(128)"),
            ("generated_image_url", "VARCHAR(512)"),
            ("analysis_completed", "INTEGER DEFAULT 0"),
            ("generated_completed", "INTEGER DEFAULT 0"),
        ]

        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f'ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS {column_name} {column_type};'))
                conn.commit()
                print(f"✅ 列 {column_name} 已添加或已存在")
            except Exception as e:
                print(f"❌ 添加列 {column_name} 失败: {e}")

        print("\n数据库结构修复完成!")

if __name__ == "__main__":
    fix_missing_columns()