#!/usr/bin/env python3
"""
数据库初始化脚本 - ClosetAI / 衣橱管家
幂等执行，创建不存在的表，不影响已有数据
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional
import logging

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    def __init__(self):
        self.conn: Optional[connection] = None
        self.cursor: Optional[cursor] = None
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

    def _connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            assert self.conn is not None
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            assert self.cursor is not None
            logger.info(f"已连接到数据库: {self.db_config['dbname']}")
        except psycopg2.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def _close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def _get_existing_tables(self) -> List[str]:
        assert self.cursor is not None
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def _get_existing_functions(self) -> List[str]:
        assert self.cursor is not None
        self.cursor.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def _get_existing_policies(self) -> List[Tuple[str, str]]:
        assert self.cursor is not None
        self.cursor.execute("""
            SELECT tablename, policyname 
            FROM pg_policies 
            WHERE schemaname = 'public'
        """)
        return [(row[0], row[1]) for row in self.cursor.fetchall()]

    def _parse_sql_file(self, file_path: Path) -> List[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        statements = []
        current_statement = []
        in_block = False

        for line in content.split('\n'):
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

        return statements

    def _execute_statement(self, statement: str) -> Optional[bool]:
        assert self.cursor is not None
        try:
            self.cursor.execute(statement)
            return True
        except psycopg2.Error as e:
            if 'already exists' in str(e).lower():
                return None
            logger.warning(f"执行失败: {str(e)[:100]}")
            return False

    def _execute_with_retry(self, statement: str, max_retries: int = 3) -> bool:
        assert self.conn is not None
        for attempt in range(max_retries):
            try:
                self._execute_statement(statement)
                self.conn.commit()
                return True
            except psycopg2.Error as e:
                if attempt < max_retries - 1:
                    self.conn.rollback()
                    logger.warning(f"重试 {attempt + 1}/{max_retries}: {str(e)[:80]}")
                else:
                    return False
        return False

    def init_extensions(self):
        logger.info("=" * 50)
        logger.info("初始化扩展...")

        extensions = [
            ("pgcrypto", "UUID生成"),
        ]

        for ext, desc in extensions:
            try:
                stmt = f"CREATE EXTENSION IF NOT EXISTS \"{ext}\""
                self._execute_with_retry(stmt)
                logger.info(f"  [OK] {ext} - {desc}")
            except Exception as e:
                logger.warning(f"  [SKIP] {ext}: {str(e)[:60]}")

    def init_schema(self):
        logger.info("=" * 50)
        logger.info("创建辅助函数（public schema）...")

        existing = self._get_existing_functions()

        functions = [
            ("set_user_id", """
                CREATE OR REPLACE FUNCTION set_user_id(user_uuid UUID)
                RETURNS VOID AS $$
                BEGIN
                  PERFORM set_config('app.current_user_id', user_uuid::TEXT, false);
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
            """),
            ("current_user_id", """
                CREATE OR REPLACE FUNCTION current_user_id()
                RETURNS UUID AS $$
                BEGIN
                  RETURN NULLIF(current_setting('app.current_user_id', true), '')::UUID;
                END;
                $$ LANGUAGE plpgsql STABLE;
            """),
        ]

        for func_name, func_sql in functions:
            if func_name in existing:
                logger.info(f"  [SKIP] {func_name} (已存在)")
                continue
            try:
                self._execute_with_retry(func_sql)
                logger.info(f"  [CREATED] {func_name}")
            except Exception as e:
                logger.warning(f"  [WARN] {func_name}: {str(e)[:60]}")

    def init_tables(self):
        logger.info("=" * 50)
        logger.info("创建表...")

        schema_file = Path(__file__).parent / 'schema.sql'
        if not schema_file.exists():
            logger.error(f"schema.sql 文件不存在: {schema_file}")
            return

        existing_tables = self._get_existing_tables()
        logger.info(f"已存在的表: {existing_tables if existing_tables else '无'}")

        statements = self._parse_sql_file(schema_file)

        created_count = 0
        skipped_count = 0
        error_count = 0

        for stmt in statements:
            if not stmt.strip():
                continue

            stmt_upper = stmt.upper()

            if 'CREATE TABLE' in stmt_upper:
                match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"?(\w+)"?', stmt, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    if table_name in existing_tables:
                        logger.info(f"  [SKIP] {table_name} (已存在)")
                        skipped_count += 1
                        continue

            if self._execute_with_retry(stmt):
                if 'CREATE TABLE' in stmt_upper:
                    match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', stmt_upper)
                    if match:
                        table_name = match.group(1)
                        logger.info(f"  [CREATED] {table_name}")
                        created_count += 1
                elif 'CREATE TRIGGER' in stmt_upper:
                    match = re.search(r'CREATE\s+TRIGGER\s+(\w+)', stmt_upper)
                    if match:
                        logger.info(f"  [CREATED] trigger {match.group(1)}")
            else:
                error_count += 1

        logger.info(f"表创建完成: 新建 {created_count}, 跳过 {skipped_count}, 错误 {error_count}")

    def init_triggers(self):
        logger.info("=" * 50)
        logger.info("创建触发器...")

        schema_file = Path(__file__).parent / 'schema.sql'
        statements = self._parse_sql_file(schema_file)

        for stmt in statements:
            if 'CREATE TRIGGER' in stmt.upper():
                if self._execute_with_retry(stmt):
                    match = re.search(r'CREATE\s+TRIGGER\s+(\w+)', stmt, re.IGNORECASE)
                    if match:
                        logger.info(f"  [OK] trigger {match.group(1)}")

    def init_rls_functions(self):
        logger.info("=" * 50)
        logger.info("检查 RLS 辅助函数...")

        existing = self._get_existing_functions()
        for func_name in ['set_user_id', 'current_user_id']:
            if func_name in existing:
                logger.info(f"  [OK] {func_name} (已存在)")
            else:
                logger.warning(f"  [MISSING] {func_name}")

    def init_rls_policies(self):
        logger.info("=" * 50)
        logger.info("创建 RLS 策略...")

        tables = ['user_profiles', 'clothing_items', 'outfit_histories']
        existing_policies = self._get_existing_policies()

        for table_name in tables:
            policy_name = f"{table_name}_user_policy"

            if (table_name, policy_name) in existing_policies:
                logger.info(f"  [SKIP] {policy_name} (已存在)")
                continue

            try:
                enable_rls = f'ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY'
                force_rls = f'ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY'
                create_policy = f"""
                    CREATE POLICY {policy_name} ON {table_name}
                        FOR ALL
                        USING (user_id = (SELECT current_user_id()))
                        WITH CHECK (user_id = (SELECT current_user_id()));
                """

                self._execute_with_retry(enable_rls)
                self._execute_with_retry(force_rls)
                self._execute_with_retry(create_policy)
                logger.info(f"  [CREATED] {policy_name}")
            except Exception as e:
                logger.warning(f"  [WARN] {policy_name}: {str(e)[:60]}")

    def verify_schema(self):
        logger.info("=" * 50)
        logger.info("验证数据库结构...")

        assert self.cursor is not None
        tables = self._get_existing_tables()
        logger.info(f"表: {tables}")

        for table in ['users', 'user_profiles', 'clothing_items', 'outfit_histories']:
            if table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = self.cursor.fetchone()
                count = result[0] if result else 0
                logger.info(f"  [OK] {table}: {count} 条记录")
            else:
                logger.warning(f"  [MISSING] {table}")

        functions = self._get_existing_functions()
        rls_funcs = ['set_user_id', 'current_user_id']
        for func in rls_funcs:
            status = "[OK]" if func in functions else "[MISSING]"
            logger.info(f"  {status} {func}")

    def run(self) -> bool:
        logger.info("=" * 50)
        logger.info("ClosetAI 数据库初始化开始")
        logger.info("=" * 50)

        try:
            self._connect()

            self.init_extensions()
            self.init_schema()
            self.init_tables()
            self.init_triggers()
            self.init_rls_functions()
            self.init_rls_policies()

            if self.conn:
                self.conn.commit()
            self.verify_schema()

            logger.info("=" * 50)
            logger.info("数据库初始化完成!")
            logger.info("=" * 50)
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            if self.conn:
                self.conn.rollback()
            return False

        finally:
            self._close()


def init_database() -> bool:
    initializer = DatabaseInitializer()
    return initializer.run()


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
