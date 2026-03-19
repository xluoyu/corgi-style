import asyncio
from typing import Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from app.services.image_analysis import image_analyzer
from app.services.image_generator import image_generator
from app.services.oss_uploader import oss_uploader


ANALYSIS_PROMPT = """分析这张图片中的衣物，提取以下属性：
- color: 颜色（如：黑色、白色、红色、蓝色、灰色、米色等）
- category: 类型（上衣/裤子/外套/内衣/配饰）
- material: 材质（如：棉、羊毛、丝绸、聚酯纤维、牛仔布、针织等）
- temperature_range: 适合温度（夏季/春秋/冬季/四季）
- wear_method: 穿着方式（内穿/外穿/单穿/叠穿）
- scene: 适用场景（日常/工作/运动/约会/聚会，可选）

请以JSON格式返回所有字段。"""

GENERATION_PROMPT = """根据原图中的衣物，生成一张标准化的产品图片，要求：
1. 平铺展示（非穿戴状态）
2. 背景透明或纯白
3. 光线均匀，正面展示
4. 保持原图的：颜色、材质、款式细节
5. 尺寸比例统一，无变形
6. 专业摄影棚风格

生成与原图衣物完全相同的平铺产品图。"""


@dataclass
class ClothesAgentResult:
    clothes_id: Optional[int] = None
    success: bool = False
    message: str = ""
    image_url: Optional[str] = None
    generated_image_url: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    temperature_range: Optional[str] = None
    wear_method: Optional[str] = None
    scene: Optional[str] = None
    completed_tasks: list = field(default_factory=list)


class ClothesAgent:
    def __init__(self):
        self.analysis_prompt = ANALYSIS_PROMPT
        self.generation_prompt = GENERATION_PROMPT
    
    async def analyze_clothes(self, image_data: bytes, user_id: str) -> dict:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            ThreadPoolExecutor(),
            lambda: image_analyzer.analyze(image_data, self.analysis_prompt)
        )
        return {"type": "analysis", "result": result}
    
    async def generate_product_image(self, image_data: bytes, user_id: str) -> dict:
        loop = asyncio.get_event_loop()
        generated_data = await loop.run_in_executor(
            ThreadPoolExecutor(),
            lambda: image_generator.generate(self.generation_prompt, image_data)
        )
        url = oss_uploader.upload(generated_data, user_id, sub_dir="clothes-generated")
        return {"type": "generated_image", "result": url}
    
    async def run(self, image_data: bytes, user_id: str, db_session) -> ClothesAgentResult:
        from app.models import UserClothes, ClothesCategory, TemperatureRange, Scene, WearMethod
        
        result = ClothesAgentResult()
        original_image_url = oss_uploader.upload(image_data, user_id, sub_dir="clothes")
        
        async def run_tasks():
            analysis_task = asyncio.create_task(self.analyze_clothes(image_data, user_id))
            generation_task = asyncio.create_task(self.generate_product_image(image_data, user_id))
            
            completed = {}
            remaining = {"analysis": analysis_task, "generation": generation_task}
            
            while remaining:
                done, pending = await asyncio.wait(
                    remaining.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    task_result = task.result()
                    completed[task_result["type"]] = task_result["result"]
                    del remaining[task_result["type"]]
                
                if len(completed) == 1:
                    first_type = list(completed.keys())[0]
                    first_result = completed[first_type]
                    
                    result.completed_tasks.append(first_type)
                    
                    if first_type == "analysis":
                        analysis = first_result
                        result.color = analysis.get('color', '未知')
                        result.category = analysis.get('category', 'top')
                        result.material = analysis.get('material')
                        result.temperature_range = analysis.get('temperature_range', 'all_season')
                        result.wear_method = analysis.get('wear_method')
                        result.scene = analysis.get('scene')
                        result.success = True
                        result.message = "衣物分析完成"
                    else:
                        result.generated_image_url = first_result
                        result.success = True
                        result.message = "产品图生成完成"
                    
                    result.image_url = original_image_url
                    
                    clothes = self._create_clothes_record(
                        db_session, user_id, original_image_url, result
                    )
                    result.clothes_id = clothes.id
                    
                    for task in pending:
                        task.cancel()
                    break
            
            if "analysis" in completed:
                analysis = completed["analysis"]
                result.color = analysis.get('color', '未知')
                result.category = analysis.get('category', 'top')
                result.material = analysis.get('material')
                result.temperature_range = analysis.get('temperature_range', 'all_season')
                result.wear_method = analysis.get('wear_method')
                result.scene = analysis.get('scene')
            
            if "generated_image" in completed:
                result.generated_image_url = completed["generated_image"]
            
            if result.clothes_id:
                self._update_clothes_record(
                    db_session, result.clothes_id, result
                )
        
        await run_tasks()
        return result
    
    def _create_clothes_record(self, db_session, user_id: str, image_url: str, result: ClothesAgentResult) -> UserClothes:
        from app.models import UserClothes, ClothesCategory, TemperatureRange, Scene, WearMethod
        
        try:
            category = ClothesCategory(result.category or 'top')
        except ValueError:
            category = ClothesCategory.top
        
        try:
            temperature_range = TemperatureRange(result.temperature_range or 'all_season')
        except ValueError:
            temperature_range = TemperatureRange.all_season
        
        scene = None
        if result.scene:
            try:
                scene = Scene(result.scene)
            except ValueError:
                scene = None
        
        wear_method = None
        if result.wear_method:
            try:
                wear_method = WearMethod(result.wear_method)
            except ValueError:
                wear_method = None
        
        clothes = UserClothes(
            user_id=user_id,
            image_url=image_url,
            category=category,
            color=result.color or '未知',
            material=result.material,
            temperature_range=temperature_range,
            scene=scene,
            wear_method=wear_method,
            generated_image_url=result.generated_image_url,
            analysis_completed="analysis" in result.completed_tasks,
            generated_completed="generated_image" in result.completed_tasks
        )
        
        db_session.add(clothes)
        db_session.commit()
        db_session.refresh(clothes)
        
        return clothes
    
    def _update_clothes_record(self, db_session, clothes_id: int, result: ClothesAgentResult):
        from app.models import UserClothes, ClothesCategory, TemperatureRange, Scene, WearMethod
        
        clothes = db_session.query(UserClothes).filter(UserClothes.id == clothes_id).first()
        if not clothes:
            return
        
        if "analysis" in result.completed_tasks:
            clothes.analysis_completed = True
            if result.category:
                try:
                    clothes.category = ClothesCategory(result.category)
                except ValueError:
                    pass
            if result.color:
                clothes.color = result.color
            if result.material:
                clothes.material = result.material
            if result.temperature_range:
                try:
                    clothes.temperature_range = TemperatureRange(result.temperature_range)
                except ValueError:
                    pass
            if result.scene:
                try:
                    clothes.scene = Scene(result.scene)
                except ValueError:
                    pass
            if result.wear_method:
                try:
                    clothes.wear_method = WearMethod(result.wear_method)
                except ValueError:
                    pass
        
        if "generated_image" in result.completed_tasks and result.generated_image_url:
            clothes.generated_completed = True
            clothes.generated_image_url = result.generated_image_url
        
        db_session.commit()


clothes_agent = ClothesAgent()
