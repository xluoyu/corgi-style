import os
from abc import ABC, abstractmethod
from typing import Any
from langchain.schema import HumanMessage
from langchain.chat_models.base import BaseChatModel


class LLMProvider(ABC):
    @abstractmethod
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class OpenAILLMProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", api_key: str = None, base_url: str = None):
        from langchain_openai import ChatOpenAI
        
        self.model = model
        self.chat_model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0
        )
    
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        import base64
        from langchain.schema import HumanMessage
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content
    
    def get_provider_name(self) -> str:
        return f"openai-{self.model}"


class AnthropicLLMProvider(LLMProvider):
    def __init__(self, model: str = "claude-3-opus-20240229", api_key: str = None):
        from langchain_anthropic import ChatAnthropic
        
        self.model = model
        self.chat_model = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0
        )
    
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        import base64
        from langchain.schema import HumanMessage
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content
    
    def get_provider_name(self) -> str:
        return f"anthropic-{self.model}"


class LocalLLMProvider(LLMProvider):
    def __init__(self, model: str = "qwen-plus", base_url: str = None, api_key: str = None):
        from langchain_openai import ChatOpenAI
        
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "not-needed")
        
        self.chat_model = ChatOpenAI(
            model=model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0
        )
    
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        import base64
        from langchain.schema import HumanMessage
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ]
        
        response = self.chat_model.invoke(messages)
        return response.content
    
    def get_provider_name(self) -> str:
        return f"local-{self.model}"


def create_llm_provider(provider_type: str = None, **kwargs) -> LLMProvider:
    provider_type = provider_type or os.getenv("LLM_PROVIDER", "local")
    
    if provider_type == "openai":
        return OpenAILLMProvider(
            model=kwargs.get("model", os.getenv("OPENAI_MODEL", "gpt-4o")),
            api_key=kwargs.get("api_key", os.getenv("OPENAI_API_KEY")),
            base_url=kwargs.get("base_url")
        )
    elif provider_type == "anthropic":
        return AnthropicLLMProvider(
            model=kwargs.get("model", "claude-3-opus-20240229"),
            api_key=kwargs.get("api_key", os.getenv("ANTHROPIC_API_KEY"))
        )
    elif provider_type == "local":
        base_url = kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL")
        model = kwargs.get("model", os.getenv("VISION_MODEL", "qwen-vl-plus-2025-01-08"))
        api_key = kwargs.get("api_key", os.getenv("OPENAI_API_KEY"))
        return LocalLLMProvider(
            model=model,
            base_url=base_url,
            api_key=api_key
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")