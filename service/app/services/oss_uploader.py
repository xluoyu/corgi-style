import os
import uuid
from datetime import datetime
from typing import Optional
import oss2
from langchain_core.tools import BaseTool


class OSSUploader:
    def __init__(self):
        self._bucket = None

    @property
    def bucket(self):
        if self._bucket is None:
            endpoint = os.getenv("OSS_ENDPOINT")
            access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
            access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
            bucket_name = os.getenv("OSS_BUCKET_NAME")

            if not all([endpoint, access_key_id, access_key_secret, bucket_name]):
                raise ValueError("OSS not configured")

            auth = oss2.Auth(access_key_id, access_key_secret)
            self._bucket = oss2.Bucket(auth, endpoint, bucket_name)

        return self._bucket

    def _get_cdn_domain(self) -> Optional[str]:
        return os.getenv("OSS_CDN_DOMAIN")

    def get_signed_url(self, path: str, expires: int = 3600) -> str:
        """生成私有 bucket 的签名访问 URL"""
        signed = self.bucket.sign_url('GET', path, expires)
        cdn = self._get_cdn_domain()
        if cdn:
            signed = f"https://{cdn}/{path}" + signed[signed.index("?"):]
        return signed

    def upload(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        """
        上传图片到 OSS，返回 OSS 路径（不含域名前缀）。
        用于存入数据库，访问时通过 get_signed_url 生成签名 URL。
        """
        file_ext = '.png'
        path = f"{sub_dir}/{user_id}/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4()}{file_ext}"

        self.bucket.put_object(path, image_data)

        return path

    def upload_with_path(self, image_data: bytes, path: str) -> str:
        """上传指定路径，返回 OSS 路径"""
        self.bucket.put_object(path, image_data)
        return path


oss_uploader = OSSUploader()


class OSSUploadTool(BaseTool):
    name: str = "oss_upload"
    description: str = "上传图片到阿里云OSS，返回图片路径"

    def _run(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        return oss_uploader.upload(image_data, user_id, sub_dir)

    async def _arun(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        return self._run(image_data, user_id, sub_dir)