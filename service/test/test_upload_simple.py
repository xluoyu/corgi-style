import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from app.database import SessionLocal, init_db
from app.services.oss_uploader import oss_uploader
from app.models import UserClothes, ClothesCategory, TemperatureRange, User

def get_or_create_test_user():
    db = SessionLocal()
    try:
        test_device_fingerprint = "test_fingerprint_123"
        user = db.query(User).filter(User.device_fingerprint == test_device_fingerprint).first()
        if not user:
            user = User(device_fingerprint=test_device_fingerprint)
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ 创建测试用户: {user.id}")
        else:
            print(f"✅ 已存在测试用户: {user.id}")
        return user.id
    finally:
        db.close()

def test_full_flow():
    print("\n" + "=" * 50)
    print("完整流程测试: upload")
    print("=" * 50)

    init_db()
    user_id = get_or_create_test_user()

    image_path = os.path.join(os.path.dirname(__file__), "test.jpg")
    with open(image_path, 'rb') as f:
        image_data = f.read()

    print(f"1. 读取图片: {len(image_data)} bytes")

    print("2. 上传到 OSS...")
    try:
        image_path = oss_uploader.upload(image_data, str(user_id), sub_dir="clothes")
        print(f"   OSS 上传成功，路径: {image_path}")
        print(f"   签名URL: {oss_uploader.get_signed_url(image_path)}")
    except Exception as e:
        print(f"   OSS 上传失败: {type(e).__name__}: {e}")
        print("\n请检查环境变量是否正确设置:")
        print(f"  OSS_ENDPOINT={os.getenv('OSS_ENDPOINT')}")
        print(f"  OSS_ACCESS_KEY_ID={os.getenv('OSS_ACCESS_KEY_ID')}")
        print(f"  OSS_ACCESS_KEY_SECRET={'已设置' if os.getenv('OSS_ACCESS_KEY_SECRET') else '未设置'}")
        print(f"  OSS_BUCKET_NAME={os.getenv('OSS_BUCKET_NAME')}")
        print(f"  OSS_CDN_DOMAIN={os.getenv('OSS_CDN_DOMAIN')}")
        return

    print("3. 保存到数据库...")
    db = SessionLocal()
    try:
        clothes = UserClothes(
            user_id=user_id,
            original_image_url=image_path,
            category="top",
            color="识别中...",
            material="识别中...",
            temperature_range="all_season",
            tags="{}",
            analysis_completed=0,
            generated_completed=0
        )
        db.add(clothes)
        db.commit()
        db.refresh(clothes)
        print(f"   数据库保存成功: clothes_id={clothes.id}")
        print(f"\n✅ 全部测试通过!")
    except Exception as e:
        print(f"   数据库保存失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_full_flow()