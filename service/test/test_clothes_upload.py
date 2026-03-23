"""
/clothes/upload 接口测试用例

测试优先：先定义测试 → 验证失败（功能未实现）→ 实现功能 → 回归测试
"""
import pytest
from unittest.mock import patch, MagicMock
from app.routers.clothes import run_clothes_agent_async

# 导入 conftest 中的 fixtures（pytest 自动发现）
# client, mock_oss_uploader, mock_async_task, valid_image_bytes 等


import uuid

class TestClothesUpload:
    """/clothes/upload 接口测试"""

    # ========== 正常流程测试 ==========

    def test_upload_success(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes):
        """
        测试：有效图片上传成功
        验证：返回 200，clothes_id、image_url、message 正确，OSS 被调用，DB 记录被创建
        """
        mock_thread, mock_instance = mock_async_task
        test_user_id = str(uuid.uuid4())

        response = client.post(
            "/clothes/upload",
            data={"user_id": test_user_id},
            files={"file": ("test.png", valid_image_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "clothes_id" in data
        assert data["message"] == "上传成功"
        assert "image_url" in data
        assert data["image_url"] == mock_oss_uploader.get_signed_url.return_value

        # 验证 OSS 上传被调用
        mock_oss_uploader.upload.assert_called_once()
        call_args = mock_oss_uploader.upload.call_args
        assert call_args[0][1] == test_user_id  # user_id
        assert call_args[1]["sub_dir"] == "clothes"

        # 验证异步线程被触发
        mock_thread.assert_called_once()
        mock_instance.start.assert_called_once()

    def test_upload_creates_db_record(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes, test_db):
        """
        测试：上传成功后数据库记录正确创建
        验证：category=top, color=识别中..., analysis_completed=0
        """
        mock_async_task  # 忽略返回值
        test_user_id = str(uuid.uuid4())

        response = client.post(
            "/clothes/upload",
            data={"user_id": test_user_id},
            files={"file": ("test.png", valid_image_bytes, "image/png")},
        )

        assert response.status_code == 200
        clothes_id = response.json()["clothes_id"]

        # 验证数据库记录
        from app.models.clothes import UserClothes
        record = test_db.query(UserClothes).filter(
            UserClothes.id == clothes_id
        ).first()

        assert record is not None
        assert str(record.user_id) == "test-user-123"
        assert record.original_image_url == mock_oss_uploader.upload.return_value
        assert record.category == "top"
        assert record.color == "识别中..."
        assert record.material == "识别中..."
        assert record.temperature_range == "all_season"
        assert record.analysis_completed == 0
        assert record.generated_completed == 0

    # ========== 文件大小验证 ==========

    def test_upload_file_too_large(self, client, mock_oss_uploader, mock_async_task, large_image_bytes):
        """
        测试：图片超过 10MB 时返回 400 错误
        验证：返回 400，detail 包含 "10MB"，OSS 未被调用
        """
        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("large.png", large_image_bytes, "image/png")},
        )

        assert response.status_code == 400
        assert "10MB" in response.json()["detail"]
        mock_oss_uploader.upload.assert_not_called()

    # ========== 文件类型验证 ==========

    def test_upload_invalid_content_type(self, client, mock_oss_uploader, mock_async_task, text_file_bytes):
        """
        测试：上传非图片文件时返回 400 错误
        验证：返回 400，detail 包含 "图片"，OSS 未被调用
        """
        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("test.txt", text_file_bytes, "text/plain")},
        )

        assert response.status_code == 400
        assert "图片" in response.json()["detail"]
        mock_oss_uploader.upload.assert_not_called()

    def test_upload_no_content_type(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes):
        """
        测试：上传时 content-type 为空字符串也视为无效
        验证：返回 400
        """
        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("test.png", valid_image_bytes, "")},
        )

        assert response.status_code == 400

    # ========== 参数缺失验证 ==========

    def test_upload_missing_user_id(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes):
        """
        测试：user_id 缺失时返回 422（FastAPI 表单验证错误）
        验证：返回 422，detail 包含 user_id
        """
        response = client.post(
            "/clothes/upload",
            data={},  # 缺少 user_id
            files={"file": ("test.png", valid_image_bytes, "image/png")},
        )

        assert response.status_code == 422
        assert "user_id" in str(response.json()["detail"])

    def test_upload_missing_file(self, client, mock_oss_uploader, mock_async_task):
        """
        测试：未上传文件时返回 422
        验证：返回 422
        """
        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={},  # 缺少 file
        )

        assert response.status_code == 422

    # ========== 边界条件测试 ==========

    def test_upload_empty_image(self, client, mock_oss_uploader, mock_async_task):
        """
        测试：上传空文件（0 字节）
        验证：空文件应该被接受（OSS 上传成功），DB 记录被创建
              因为代码只验证大小 > 10MB，不限制最小大小
        """
        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("empty.png", b"", "image/png")},
        )

        # 空文件不触发大小限制，应该成功
        assert response.status_code == 200
        data = response.json()
        assert "clothes_id" in data

    def test_upload_jpeg_content_type(self, client, mock_oss_uploader, mock_async_task):
        """
        测试：上传 JPEG 格式图片（不同 content-type）
        验证：image/jpeg 有效，成功上传
        """
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 100

        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("test.jpg", jpeg_data, "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "上传成功"

    # ========== 异常场景测试 ==========

    def test_upload_oss_failure(self, client, mock_async_task, valid_image_bytes):
        """
        测试：OSS 上传失败时返回 500
        验证：oss_uploader.upload 抛出异常时，接口返回 500
        """
        with patch("app.routers.clothes.oss_uploader") as mock_oss:
            mock_oss.upload.side_effect = Exception("OSS 连接失败")

            response = client.post(
                "/clothes/upload",
                data={"user_id": str(uuid.uuid4())},
                files={"file": ("test.png", valid_image_bytes, "image/png")},
            )

            # 当前实现未捕获此异常，返回 500
            assert response.status_code == 500

    def test_upload_db_session_error(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes):
        """
        测试：数据库会话异常时返回 500
        验证：db.add / db.commit 失败时接口返回 500
        """
        with patch("app.routers.clothes.UserClothes") as mock_model:
            # 模拟 db.commit 时抛出异常
            from app.database import get_db
            original_override = dict(client.app.dependency_overrides)

            def bad_db():
                bad_session = MagicMock()
                bad_session.add.side_effect = Exception("DB 连接断开")
                yield bad_session

            client.app.dependency_overrides[get_db] = bad_db

            response = client.post(
                "/clothes/upload",
                data={"user_id": str(uuid.uuid4())},
                files={"file": ("test.png", valid_image_bytes, "image/png")},
            )

            assert response.status_code == 500
            # 恢复原始 override
            client.app.dependency_overrides = original_override

    # ========== 异步任务测试 ==========

    def test_async_task_receives_correct_params(self, client, mock_oss_uploader, mock_async_task, valid_image_bytes):
        """
        测试：异步任务被触发时传入正确的参数
        验证：threading.Thread 被调用，target 为 run_clothes_agent_async
        """
        mock_thread, mock_instance = mock_async_task

        response = client.post(
            "/clothes/upload",
            data={"user_id": str(uuid.uuid4())},
            files={"file": ("test.png", valid_image_bytes, "image/png")},
        )

        assert response.status_code == 200

        # 验证线程被正确配置
        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs["target"] == run_clothes_agent_async
        mock_instance.start.assert_called_once()
