import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Tuple
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel


class LLMProvider(ABC):
    @abstractmethod
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class OpenAILLMProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", api_key: str = None, base_url: str = None, timeout: float = 60.0):
        from langchain_openai import ChatOpenAI

        self.model = model
        self.chat_model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
            request_timeout=timeout
        )
    
    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        import base64
        from langchain_core.messages import HumanMessage
        
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
        from langchain_core.messages import HumanMessage
        
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
    def __init__(self, model: str = None, base_url: str = None, api_key: str = None, timeout: float = 60.0):
        from langchain_openai import ChatOpenAI

        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "not-needed")

        # chat_model：纯文本模型，用于 intent/planning 等文本任务
        text_model = model or os.getenv("TEXT_MODEL", "qwen-plus")
        self.chat_model = ChatOpenAI(
            model=text_model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0,
            request_timeout=timeout,
            streaming=False
        )

        # vision_model：VL 模型，仅用于 analyze_image
        vision_model = os.getenv("VISION_MODEL", "qwen-vl-plus")
        self.vision_model = ChatOpenAI(
            model=vision_model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0,
            request_timeout=timeout,
            streaming=False
        )

    def analyze_image(self, image_data: bytes, prompt: str) -> dict:
        import base64
        from langchain_core.messages import HumanMessage

        base64_image = base64.b64encode(image_data).decode('utf-8')

        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ]

        response = self.vision_model.invoke(messages)
        return response.content

    def get_provider_name(self) -> str:
        return f"local-text"


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
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        return LocalLLMProvider(
            model=kwargs.get("model") or os.getenv("TEXT_MODEL", "qwen-plus"),
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")


@lru_cache(maxsize=4)
def get_cached_provider(provider_type: str = None, **kwargs) -> LLMProvider:
    """
    获取缓存的 LLM Provider 实例。

    使用 lru_cache 避免每次调用都重新：
    - 读取 os.getenv()
    - 执行条件 import（ChatOpenAI, ChatAnthropic 等）
    - 创建新的模型实例

    同一 (provider_type, base_url, model, api_key) 组合只创建一次。
    """
    # 预填充所有 kwargs，避免 os.getenv 重复读取
    resolved_kwargs = {}
    for key, default in [
        ("base_url", None),
        ("model", None),
        ("api_key", None),
    ]:
        if key in kwargs:
            resolved_kwargs[key] = kwargs[key]
        elif key == "model":
            env_map = {
                "openai": "OPENAI_MODEL",
                "anthropic": None,
                "local": "TEXT_MODEL",
            }
            env_key = env_map.get(provider_type or "local")
            resolved_kwargs[key] = os.getenv(env_key) if env_key else None
        elif key == "api_key":
            env_key = "OPENAI_API_KEY" if provider_type != "anthropic" else "ANTHROPIC_API_KEY"
            resolved_kwargs[key] = os.getenv(env_key)

    return create_llm_provider(provider_type, **resolved_kwargs)