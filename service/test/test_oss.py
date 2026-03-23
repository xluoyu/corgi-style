import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from app.services.oss_uploader import oss_uploader

image_path = os.path.join(os.path.dirname(__file__), "v2-042e74a64d30b3c0db560644e8aaee64_r.jpg")
with open(image_path, 'rb') as f:
    image_data = f.read()

path = oss_uploader.upload(image_data, user_id="test", sub_dir="user")
print(f"路径: {path}")
print(f"签名URL: {oss_uploader.get_signed_url(path)}")
