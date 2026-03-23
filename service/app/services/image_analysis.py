import os
import json
import base64
from typing import Optional
from langchain_openai import ChatOpenAI


class ImageAnalyzer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("VISION_MODEL", "qwen-image-plus-2026-01-09")
        
        self.chat_model = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0,
            timeout=60
        )
    
    def analyze(
        self,
        image_data: bytes,
        prompt: str
    ) -> dict:
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        from langchain_core.messages import HumanMessage
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ]
        
        response = self.chat_model.invoke(messages)
        
        content = response.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > 0:
                return json.loads(content[start:end])
            raise ValueError(f"Failed to parse LLM response: {content}")


image_analyzer = ImageAnalyzer()
