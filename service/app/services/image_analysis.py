import os
import json
import dashscope
from dashscope import MultiModalConversation
from typing import Optional


class ImageAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    def analyze(
        self,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        prompt: str = ""
    ) -> dict:
        """
        使用 qwen3.5-plus 分析图片中的衣物属性。

        Args:
            image_url: 参考图 OSS 签名 URL（优先使用）
            image_data: 参考图字节数据（转 base64）
            prompt: 分析提示词

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
            model="qwen3.5-plus",
            messages=messages,
            result_format='message',
            stream=False,
        )

        if response.status_code != 200:
            raise ValueError(f"qwen3.5-plus 调用失败: {response.message}")

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

        raise ValueError(f"qwen3.5-plus 未返回文本: {response}")


image_analyzer = ImageAnalyzer()
