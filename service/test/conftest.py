"""
pytest 配置和共享 fixtures

设计原则：
- 不导入 app.main，避免加载 OutfitCache（JSONB 类型不支持 SQLite）
- 创建独立的测试 Base，仅注册 clothes/upload 需要的模型
- 使用 dependency_overrides 注入测试数据库
"""
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio

# 异步测试配置
pytest_plugins = ("pytest_asyncio",)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, DateTime, Integer, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.pool import StaticPool
from datetime import datetime
import uuid

# 设置测试环境变量（在导入 app 模块之前）
os.environ["OSS_ENDPOINT"] = "https://oss-cn-hangzhou.aliyuncs.com"
os.environ["OSS_ACCESS_KEY_ID"] = "test_key"
os.environ["OSS_ACCESS_KEY_SECRET"] = "test_secret"
os.environ["OSS_BUCKET_NAME"] = "test-bucket"


# =============================================================================
# 独立的测试数据库 Base（仅注册 clothes/upload 需要的模型）
# =============================================================================

TestBase = declarative_base()


class TestUser(TestBase):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_fingerprint = Column(String(255), unique=True, nullable=False)
    last_active_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    clothes = relationship("TestUserClothes", back_populates="user", cascade="all, delete-orphan")


class TestUserClothes(TestBase):
    __tablename__ = "clothing_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(100), nullable=True)
    original_image_url = Column(String(500), nullable=False)
    cartoon_image_url = Column(String(500), nullable=True)
    color = Column(String(32), nullable=True)
    material = Column(String(64), nullable=True)
    temperature_range = Column(String(50), nullable=True)
    wear_method = Column(String(50), nullable=True)
    scene = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    wear_count = Column(Integer, default=0)
    last_worn_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    analysis_completed = Column(Integer, default=0)
    generated_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("TestUser", back_populates="clothes")


# =============================================================================
# 测试数据库 engine & session
# =============================================================================

def create_test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(bind=engine)
    return engine


# =============================================================================
# 测试用 FastAPI app（直接注册 clothes_router，不触发 OutfitCache 加载）
# =============================================================================

def create_test_app():
    """创建仅包含 clothes_router 的测试 FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    from app.routers.clothes import router as clothes_router

    test_app = FastAPI(title="Test App")
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    test_app.include_router(clothes_router)
    return test_app


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """创建 SQLite 内存数据库引擎（每个测试函数独立）"""
    engine = create_test_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    # 预先创建测试用户，避免外键约束失败
    test_user = TestUser(
        id="test-user-123",
        device_fingerprint="test_fingerprint_for_tests"
    )
    db.add(test_user)
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_engine, test_db):
    """创建带测试数据库的 FastAPI TestClient"""
    from app.database import get_db

    test_app = create_test_app()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as c:
        yield c

    test_app.dependency_overrides.clear()


# =============================================================================
# Mock fixtures
# =============================================================================

@pytest.fixture
def mock_oss_uploader():
    """Mock OSS 上传，避免真实 OSS 调用"""
    with patch("app.routers.clothes.oss_uploader") as mock:
        mock.upload.return_value = "clothes/test-user-123/20240101/fake-uuid.png"
        mock.get_signed_url.return_value = "https://signed-url.example.com/clothes/test-user-123/20240101/fake-uuid.png?Signature=xxx"
        yield mock


@pytest.fixture
def mock_async_task():
    """Mock 后台异步任务，避免启动真实线程"""
    with patch("app.routers.clothes.threading.Thread") as mock_thread:
        mock_instance = MagicMock()
        mock_thread.return_value = mock_instance
        yield mock_thread, mock_instance


# =============================================================================
# 测试数据 fixtures
# =============================================================================

@pytest.fixture
def valid_image_bytes():
    """生成最小合法 PNG 图片字节"""
    png_data = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01"
        b"\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00"
        b"\x90\x77\x53\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return png_data


@pytest.fixture
def large_image_bytes(valid_image_bytes):
    """生成超过 10MB 的图片数据"""
    target_size = 11 * 1024 * 1024 + 1
    repeats = (target_size // len(valid_image_bytes)) + 1
    return valid_image_bytes * repeats


@pytest.fixture
def text_file_bytes():
    """返回非图片文件字节"""
    return b"This is not an image file, just plain text content."
