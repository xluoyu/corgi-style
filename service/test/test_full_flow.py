"""
衣物完整流程测试脚本

提供两种模式：
  --mode new   : 新建记录（给定图片路径 + user_id）
  --mode rerun : 重新分析已有记录（给定 clothes_id）

使用示例：
  python -m test.test_full_flow --mode new --image test.jpg --user-id de124fa9-1558-4695-bb0a-d8090dfdb773
  python -m test.test_full_flow --mode rerun --clothes-id 812a1cf0-ad88-4152-9b10-418e819efb66
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from app.database import SessionLocal
from app.agent.clothes_agent import ClothesAgent
from app.services.oss_uploader import oss_uploader


async def _rerun_analysis(image_data: bytes, user_id: str, clothes_id: str, db):
    """复用 agent 分析逻辑更新已有记录"""
    from app.models import UserClothes
    clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()

    agent = ClothesAgent()

    # 分析图片（使用签名 URL）
    print("[分析] 调用视觉模型分析图片...")
    signed_url = oss_uploader.get_signed_url(str(clothes.original_image_url))
    analysis_result = await agent.analyze_clothes(str(clothes.original_image_url), user_id)
    analysis = analysis_result["result"]
    print(f"[分析] 结果: {analysis}")

    # 生成商品图（Qwen-Image-2.0，传入 signed URL）
    print("[生成] 调用图像生成模型...")
    signed_url = oss_uploader.get_signed_url(str(clothes.original_image_url))
    generation_result = await agent.generate_product_image(str(clothes.original_image_url), user_id)
    generated_path = generation_result["result"]
    print(f"[生成] 商品图路径: {generated_path}")

    # 更新数据库
    from app.models import UserClothes, ClothesCategory, TemperatureRange
    clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()
    if not clothes:
        print(f"[错误] 记录不存在: {clothes_id}")
        return

    clothes.analysis_completed = 1
    clothes.name = analysis.get('name')
    clothes.color = analysis.get('color', 'unknown')
    clothes.material = analysis.get('material')

    try:
        clothes.category = ClothesCategory(analysis.get('category', 'top'))
    except (ValueError, TypeError):
        clothes.category = 'top'

    try:
        clothes.temperature_range = TemperatureRange(analysis.get('temperature_range', 'all_season'))
    except (ValueError, TypeError):
        clothes.temperature_range = 'all_season'

    clothes.wear_method = analysis.get('wear_method')
    clothes.scene = analysis.get('scene')

    clothes.cartoon_image_url = generated_path
    clothes.generated_completed = 1
    db.commit()

    print(f"[更新] name={clothes.name}, color={clothes.color}, category={clothes.category}")
    print(f"[更新] material={clothes.material}, wear_method={clothes.wear_method}, scene={clothes.scene}")
    print(f"[更新] 商品图路径已写入数据库")
    print(f"[签名] 商品图签名URL: {oss_uploader.get_signed_url(generated_path)}")


async def run_new_flow(image_path: str, user_id: str):
    """模式A：给定图片和 user_id，新建完整流程"""
    print(f"\n{'='*60}")
    print(f" 模式A：新建完整流程")
    print(f"{'='*60}")

    # 1. 读取图片
    if not os.path.exists(image_path):
        print(f"[错误] 图片不存在: {image_path}")
        return
    with open(image_path, 'rb') as f:
        image_data = f.read()
    print(f"[1/5] 读取图片: {len(image_data)} bytes, path={image_path}")

    # 2. OSS 上传
    oss_path = oss_uploader.upload(image_data, user_id, sub_dir="clothes")
    print(f"[2/5] OSS 上传成功: {oss_path}")

    # 3. 签名 URL
    signed_url = oss_uploader.get_signed_url(oss_path)
    print(f"[3/5] 签名URL: {signed_url}")

    # 4. 创建 DB 记录
    db = SessionLocal()
    try:
        from app.models import UserClothes, ClothesCategory, TemperatureRange
        clothes = UserClothes(
            user_id=user_id,
            original_image_url=oss_path,
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
        clothes_id = str(clothes.id)
        print(f"[4/5] DB 记录创建: clothes_id={clothes_id}")
    except Exception as e:
        print(f"[错误] DB 写入失败: {e}")
        db.rollback()
        return
    finally:
        db.close()

    # 5. 执行分析 + 生成
    await _rerun_analysis(image_data, user_id, clothes_id, SessionLocal())

    print(f"\nOK 完整流程完成！clothes_id={clothes_id}")
    print(f"OK 最终签名URL: {signed_url}")


async def rerun_existing(clothes_id: str):
    """模式B：重新分析已有记录"""
    print(f"\n{'='*60}")
    print(f" 模式B：重新分析已有记录 (clothes_id={clothes_id})")
    print(f"{'='*60}")

    db = SessionLocal()
    try:
        from app.models import UserClothes
        clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()
        if not clothes:
            print(f"[错误] 记录不存在: {clothes_id}")
            return

        print(f"[DB] user_id={clothes.user_id}")
        print(f"[DB] color={clothes.color}, category={clothes.category}, "
              f"material={clothes.material}, temperature_range={clothes.temperature_range}")
        print(f"[DB] analysis_completed={clothes.analysis_completed}, "
              f"generated_completed={clothes.generated_completed}")
        print(f"[DB] original_image_url={clothes.original_image_url}")
        print(f"[DB] cartoon_image_url={clothes.cartoon_image_url}")

        # 验证签名 URL 并下载图片
        orig_signed = oss_uploader.get_signed_url(clothes.original_image_url)
        print(f"\n[签名] original签名URL:\n  {orig_signed}")

        import requests
        resp = requests.get(orig_signed)
        resp.raise_for_status()
        image_data = resp.content
        print(f"[下载] 图片下载成功: {len(image_data)} bytes")

        # 重新分析
        await _rerun_analysis(image_data, str(clothes.user_id), clothes_id, db)

        print(f"\nOK 重新分析完成！请刷新 /clothes/list 或 /clothes/status/{clothes_id} 验证")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="衣物完整流程测试")
    parser.add_argument("--mode", choices=["new", "rerun"], required=True,
                        help="new=新建记录, rerun=重试已有记录")
    parser.add_argument("--image", help="模式A: 图片路径")
    parser.add_argument("--user-id", help="模式A: user_id")
    parser.add_argument("--clothes-id", help="模式B: clothes_id")
    args = parser.parse_args()

    if args.mode == "new":
        if not args.image or not args.user_id:
            print("FAIL 模式A 需要 --image 和 --user-id")
            sys.exit(1)
        asyncio.run(run_new_flow(args.image, args.user_id))
    else:
        if not args.clothes_id:
            print("FAIL 模式B 需要 --clothes-id")
            sys.exit(1)
        asyncio.run(rerun_existing(args.clothes_id))
