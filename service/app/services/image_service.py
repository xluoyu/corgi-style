import os
import json
import uuid
import httpx
import asyncio
from typing import TypedDict, Optional, List
from datetime import datetime
from langgraph.constants import Send

from app.services.llm_providers import create_llm_provider, LLMProvider
from app.services.oss_uploader import oss_uploader


class ClothesAnalysisState(TypedDict):
    image_data: bytes
    user_id: str
    llm_provider: LLMProvider
    analysis_result: Optional[dict]
    bg_removed_image: Optional[bytes]
    oss_url: Optional[str]
    error: Optional[str]


CLOTHES_ANALYSIS_PROMPT = """请分析这张图片中的衣服，详细描述以下属性：
1. 颜色（如：黑色、白色、红色、蓝色等）
2. 类型（如：T恤、衬衫、牛仔裤、短裙、外套等）
3. 材质（如：棉、羊毛、丝绸、聚酯纤维、牛仔布等）
4. 适合温度（summer/spring_autumn/winter/all_season）
5. 可内搭/可外穿（inner_wear/outer_wear/single_wear/layering）
6. 适用场景（daily/work/sport/date/party，可选）

请以JSON格式返回：
{
    "color": "颜色",
    "category": "类型",
    "material": "材质",
    "temperature_range": "适合温度",
    "wear_method": "穿着方式",
    "scene": "适用场景（可选）"
}"""


def analyze_clothes_node(state: ClothesAnalysisState) -> ClothesAnalysisState:
    try:
        provider = state["llm_provider"]
        response = provider.analyze_image(state["image_data"], CLOTHES_ANALYSIS_PROMPT)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > 0:
                result = json.loads(response[start:end])
            else:
                raise ValueError("Failed to parse LLM response")
        
        state["analysis_result"] = result
    except Exception as e:
        state["error"] = f"Analysis failed: {str(e)}"
    
    return state


def remove_background_node(state: ClothesAnalysisState) -> ClothesAnalysisState:
    try:
        rembg_api_key = os.getenv("REMBG_API_KEY")
        if not rembg_api_key:
            raise ValueError("Rembg API key not configured")
        
        files = {'image': ('image.jpg', state["image_data"], 'image/jpeg')}
        headers = {'Authorization': f'Bearer {rembg_api_key}'}
        
        with httpx.Client(timeout=60) as client:
            response = client.post(
                'https://api.remove.bg/v1.0/remove-background',
                files=files,
                headers=headers
            )
        
        if response.status_code != 200:
            raise ValueError(f"Background removal failed: {response.text}")
        
        state["bg_removed_image"] = response.content
    except Exception as e:
        state["error"] = f"Background removal failed: {str(e)}"
    
    return state


def upload_to_oss_node(state: ClothesAnalysisState) -> ClothesAnalysisState:
    try:
        image_data = state["bg_removed_image"] or state["image_data"]
        state["oss_url"] = oss_uploader.upload(image_data, state["user_id"])
    except Exception as e:
        state["error"] = f"OSS upload failed: {str(e)}"
    
    return state


def parallel_start_node(state: ClothesAnalysisState) -> List[Send]:
    return [
        Send("analyze", state),
        Send("remove_bg", state),
    ]


def analyze_clothes_node_sync(state: ClothesAnalysisState) -> ClothesAnalysisState:
    return analyze_clothes_node(state)


def remove_background_node_sync(state: ClothesAnalysisState) -> ClothesAnalysisState:
    return remove_background_node(state)


class ImageService:
    def __init__(self):
        self._llm_provider = None
        self._graph = None
    
    @property
    def llm_provider(self) -> LLMProvider:
        if self._llm_provider is None:
            self._llm_provider = create_llm_provider()
        return self._llm_provider
    
    @llm_provider.setter
    def llm_provider(self, provider: LLMProvider):
        self._llm_provider = provider
    
    def _get_graph(self):
        if self._graph is None:
            from langgraph.graph import StateGraph, END
            
            builder = StateGraph(ClothesAnalysisState)
            
            builder.add_node("analyze", analyze_clothes_node_sync)
            builder.add_node("remove_bg", remove_background_node_sync)
            builder.add_node("upload", upload_to_oss_node)
            
            builder.add_conditional_edges(
                "parallel_start",
                parallel_start_node,
                ["analyze", "remove_bg"]
            )
            
            builder.set_entry_point("parallel_start")
            
            def join_results(results: List[ClothesAnalysisState]) -> ClothesAnalysisState:
                joined = results[0]
                for r in results:
                    if r.get("analysis_result"):
                        joined["analysis_result"] = r["analysis_result"]
                    if r.get("bg_removed_image"):
                        joined["bg_removed_image"] = r["bg_removed_image"]
                    if r.get("error") and not joined.get("error"):
                        joined["error"] = r["error"]
                return joined
            
            builder.add_node("join", join_results)
            
            builder.add_edge("analyze", "join")
            builder.add_edge("remove_bg", "join")
            builder.add_edge("join", "upload")
            builder.add_edge("upload", END)
            
            self._graph = builder.compile()
        
        return self._graph
    
    def analyze_clothes(self, image_data: bytes) -> dict:
        provider = self.llm_provider
        response = provider.analyze_image(image_data, CLOTHES_ANALYSIS_PROMPT)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > 0:
                result = json.loads(response[start:end])
            else:
                raise ValueError("Failed to parse LLM response")
        
        return result
    
    def remove_background(self, image_data: bytes) -> bytes:
        rembg_api_key = os.getenv("REMBG_API_KEY")
        if not rembg_api_key:
            raise ValueError("Rembg API key not configured")
        
        files = {'image': ('image.jpg', image_data, 'image/jpeg')}
        headers = {'Authorization': f'Bearer {rembg_api_key}'}
        
        with httpx.Client(timeout=60) as client:
            response = client.post(
                'https://api.remove.bg/v1.0/remove-background',
                files=files,
                headers=headers
            )
        
        if response.status_code != 200:
            raise ValueError(f"Background removal failed: {response.text}")
        
        return response.content
    
    def upload_to_oss(self, image_data: bytes, user_id: str) -> str:
        return oss_uploader.upload(image_data, user_id)
    
    async def process_clothes_parallel(self, image_data: bytes, user_id: str) -> dict:
        graph = self._get_graph()
        
        initial_state: ClothesAnalysisState = {
            "image_data": image_data,
            "user_id": user_id,
            "llm_provider": self.llm_provider,
            "analysis_result": None,
            "bg_removed_image": None,
            "oss_url": None,
            "error": None
        }
        
        result = await graph.ainvoke(initial_state)
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        return {
            "analysis": result["analysis_result"],
            "oss_url": result["oss_url"],
            "image_data": result["bg_removed_image"]
        }


image_service = ImageService()