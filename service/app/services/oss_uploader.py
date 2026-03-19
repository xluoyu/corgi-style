import os
import uuid
from datetime import datetime
from typing import Optional
import oss2
from langchain.tools import BaseTool


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
    
    def _get_url(self, path: str) -> str:
        cdn_domain = os.getenv("OSS_CDN_DOMAIN")
        if cdn_domain:
            return f"https://{cdn_domain}/{path}"
        
        bucket_name = os.getenv("OSS_BUCKET_NAME")
        endpoint = os.getenv("OSS_ENDPOINT")
        return f"https://{bucket_name}.{endpoint}/{path}"
    
    def upload(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        file_ext = '.png'
        path = f"{sub_dir}/{user_id}/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4()}{file_ext}"
        
        self.bucket.put_object(path, image_data)
        
        return self._get_url(path)
    
    def upload_with_path(self, image_data: bytes, path: str) -> str:
        self.bucket.put_object(path, image_data)
        
        return self._get_url(path)


oss_uploader = OSSUploader()


class OSSUploadTool(BaseTool):
    name: str = "oss_upload"
    description: str = "上传图片到阿里云OSS，返回图片URL"
    
    def _run(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        return oss_uploader.upload(image_data, user_id, sub_dir)
    
    async def _arun(self, image_data: bytes, user_id: str, sub_dir: str = "clothes") -> str:
        return self._run(image_data, user_id, sub_dir)