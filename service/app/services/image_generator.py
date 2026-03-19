import os
import base64
from typing import Optional, Literal
from langchain_openai import ChatOpenAI


class ImageGenerator:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("IMAGE_MODEL", "qwen-image-plus-2026-01-09")
        
        self.chat_model = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120
        )
    
    def generate(
        self,
        prompt: str,
        reference_image: Optional[bytes] = None
    ) -> bytes:
        if reference_image:
            base64_image = base64.b64encode(reference_image).decode('utf-8')
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        else:
            content = [{"type": "text", "text": prompt}]
        
        from langchain.schema import HumanMessage
        messages = [HumanMessage(content=content)]
        
        response = self.chat_model.invoke(messages)
        
        if hasattr(response, 'content') and isinstance(response.content, list):
            for item in response.content:
                if item.get('type') == 'image_url':
                    image_data = item['image_url']['url']
                    if image_data.startswith('data:image'):
                        return base64.b64decode(image_data.split(',')[1])
        
        raise ValueError(f"Failed to generate image: {response}")


image_generator = ImageGenerator()
