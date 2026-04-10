import os
import json
import dashscope
from dashscope import MultiModalConversation
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


# 单件衣物分析 prompt
CLOTHING_ANALYSIS_PROMPT = """请分析这张图片中的衣物，返回 JSON 格式：
{
    "name": "衣物名称",
    "category": "top/pants/outer/inner/accessory",
    "color": "主要颜色",
    "material": "材质（棉/麻/羊毛/牛仔等）",
    "style": "风格描述",
    "temperature_range": "summer/spring_autumn/winter/all_season",
    "scene": "daily/work/sport/date/party",
    "tags": ["标签1", "标签2"]
}"""


# 整套穿搭分析 prompt
OUTFIT_ANALYSIS_PROMPT = """请分析这张图片中的整套穿搭，返回 JSON 格式：
{
    "overall_style": "整体风格描述（如：美式复古、日系简约）",
    "items": [
        {
            "type": "衣物类型（如：牛仔外套、白色T恤）",
            "color": "主要颜色",
            "position": "上装/下装/外套/配饰"
        }
    ],
    "style_tags": ["风格标签1", "风格标签2"],
    "color_palette": ["主色调1", "主色调2", "辅助色"],
    "description": "整体搭配描述"
}"""


@dataclass
class ClothingAttrs:
    """单件衣物分析结果"""
    name: Optional[str] = None
    category: str = "top"
    color: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None
    temperature_range: Optional[str] = None
    scene: Optional[str] = None
    tags: List[str] = None


@dataclass
class OutfitAnalysisResult:
    """整套穿搭分析结果"""
    overall_style: str
    items: List[Dict[str, Any]]
    style_tags: List[str]
    color_palette: List[str]
    description: Optional[str] = None


class ImageAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    def _call_vision_model(
        self,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        prompt: str = ""
    ) -> dict:
        """
        调用视觉模型

        Args:
            image_url: 图片 URL（优先使用）
            image_data: 图片字节数据
            prompt: 提示词

        Returns:
            解析后的 JSON dict
        """
        content = []

        if image_url:
            content.append({"image": image_url})
        elif image_data:
            import base64
            b64 = base64.b64encode(image_data).decode('utf-8')
            content.append({"image": f"data:image/jpeg;base64,{b64}"})
        else:
            raise ValueError("必须提供 image_url 或 image_data")

        content.append({"text": prompt})

        messages = [{"role": "user", "content": content}]

        response = MultiModalConversation.call(
            api_key=self.api_key,
            model="qwen-vl-plus",  # 使用 VL 模型
            messages=messages,
            result_format='message',
            stream=False,
        )

        if response.status_code != 200:
            raise ValueError(f"Qwen VL 调用失败: {response.message}")

        output = response.output.choices[0].message.content
        for item in output:
            if "text" in item:
                text = item["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start >= 0 and end > 0:
                        return json.loads(text[start:end])
                    raise ValueError(f"Failed to parse LLM response: {text}")

        raise ValueError(f"Qwen VL 未返回文本: {response}")

    def analyze(
        self,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        prompt: str = ""
    ) -> dict:
        """
        使用 qwen-vl-plus 分析图片中的衣物属性。

        Args:
            image_url: 参考图 OSS 签名 URL（优先使用）
            image_data: 参考图字节数据（转 base64）
            prompt: 分析提示词（可选）

        Returns:
            解析后的 JSON dict
        """
        if not prompt:
            prompt = CLOTHING_ANALYSIS_PROMPT

        return self._call_vision_model(image_url, image_data, prompt)

    def analyze_clothing(
        self,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None
    ) -> ClothingAttrs:
        """
        分析单件衣物图片

        Args:
            image_url: 图片 URL
            image_data: 图片数据

        Returns:
            ClothingAttrs 对象
        """
        result = self.analyze(image_url, image_data, CLOTHING_ANALYSIS_PROMPT)

        return ClothingAttrs(
            name=result.get("name"),
            category=result.get("category", "top"),
            color=result.get("color"),
            material=result.get("material"),
            style=result.get("style"),
            temperature_range=result.get("temperature_range"),
            scene=result.get("scene"),
            tags=result.get("tags", [])
        )

    def analyze_outfit(
        self,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None
    ) -> OutfitAnalysisResult:
        """
        分析整套穿搭图片

        Args:
            image_url: 图片 URL
            image_data: 图片数据

        Returns:
            OutfitAnalysisResult 对象
        """
        result = self._call_vision_model(image_url, image_data, OUTFIT_ANALYSIS_PROMPT)

        return OutfitAnalysisResult(
            overall_style=result.get("overall_style", ""),
            items=result.get("items", []),
            style_tags=result.get("style_tags", []),
            color_palette=result.get("color_palette", []),
            description=result.get("description")
        )


image_analyzer = ImageAnalyzer()


async def analyze_clothing_image(image_url: str) -> ClothingAttrs:
    """
    分析单件衣物图片（异步便捷函数）

    Args:
        image_url: 图片 URL

    Returns:
        ClothingAttrs 对象
    """
    return image_analyzer.analyze_clothing(image_url=image_url)


async def analyze_outfit_image(image_url: str) -> OutfitAnalysisResult:
    """
    分析整套穿搭图片（异步便捷函数）

    Args:
        image_url: 图片 URL

    Returns:
        OutfitAnalysisResult 对象
    """
    return image_analyzer.analyze_outfit(image_url=image_url)
