#!/usr/bin/env python3
"""
数据库重建脚本 - ClosetAI / 衣橱管家
功能：删除所有表并重新创建（基于 schema.sql）
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseRebuilder:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '6543'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'dbname': os.getenv('DB_NAME', 'postgres'),
        }
        logger.info("数据库配置已加载")

    def _connect(self, dbname=None):
        config = self.db_config.copy()
        if dbname:
            config['dbname'] = dbname
        return psycopg2.connect(**config)

    def drop_all_tables(self, conn):
        """删除所有表"""
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()

        for (table,) in tables:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            logger.info(f"  已删除: {table}")

        conn.commit()
        cursor.close()

    def drop_all_functions(self, conn):
        """删除所有自定义函数"""
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 'DROP FUNCTION IF EXISTS ' || routine_name || ' CASCADE'
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
        """)
        functions = cursor.fetchall()

        for (query,) in functions:
            cursor.execute(query)

        conn.commit()
        cursor.close()
        logger.info("已删除所有自定义函数")

    def drop_all_views(self, conn):
        """删除所有视图"""
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 'DROP VIEW IF EXISTS ' || viewname || ' CASCADE'
            FROM pg_views
            WHERE schemaname = 'public'
        """)
        views = cursor.fetchall()

        for (query,) in views:
            cursor.execute(query)

        conn.commit()
        cursor.close()
        logger.info("已删除所有视图")

    def execute_sql_file(self, conn, file_path):
        """执行 SQL 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        cursor = conn.cursor()

        statements = []
        current_statement = []
        in_block = False

        for line in sql_content.split('\n'):
            stripped = line.strip()

            if stripped.startswith('--'):
                continue

            if '$$' in line or "$'" in line:
                in_block = not in_block

            if not in_block and stripped.endswith(';'):
                current_statement.append(line)
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
                current_statement = []
            else:
                current_statement.append(line)

        for i, stmt in enumerate(statements):
            try:
                cursor.execute(stmt)
                conn.commit()
            except Exception as e:
                logger.error(f"SQL 执行失败: {str(e)[:100]}")
                logger.error(f"语句: {stmt[:100]}...")
                conn.rollback()

        cursor.close()

    def verify_tables(self, conn):
        """验证表创建"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        cursor.close()

        logger.info("=" * 50)
        logger.info("当前数据库表:")
        for (table,) in tables:
            logger.info(f"  - {table}")
        logger.info("=" * 50)

        return [t[0] for t in tables]

    def run(self):
        """执行重建"""
        logger.info("=" * 50)
        logger.info("ClosetAI 数据库重建开始")
        logger.info("=" * 50)

        try:
            conn = self._connect()

            logger.info("\n[步骤1] 删除所有视图...")
            self.drop_all_views(conn)

            logger.info("\n[步骤2] 删除所有自定义函数...")
            self.drop_all_functions(conn)

            logger.info("\n[步骤3] 删除所有表...")
            self.drop_all_tables(conn)

            logger.info("\n[步骤4] 执行 schema.sql 重建表结构...")
            schema_file = Path(__file__).parent / 'schema.sql'
            if not schema_file.exists():
                logger.error(f"schema.sql 文件不存在: {schema_file}")
                return False

            self.execute_sql_file(conn, schema_file)
            logger.info("schema.sql 执行完成")

            logger.info("\n[步骤5] 验证表结构...")
            tables = self.verify_tables(conn)

            expected_tables = [
                'users', 'user_profiles', 'clothing_items',
                'outfit_histories', 'outfit_feedback', 'outfit_cache'
            ]

            logger.info("\n验证结果:")
            for table in expected_tables:
                if table in tables:
                    logger.info(f"  ✅ {table}")
                else:
                    logger.error(f"  ❌ {table} 缺失!")

            conn.close()

            logger.info("\n" + "=" * 50)
            logger.info("数据库重建完成!")
            logger.info("=" * 50)
            return True

        except Exception as e:
            logger.error(f"重建失败: {e}")
            return False


def main():
    rebuilder = DatabaseRebuilder()
    success = rebuilder.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
