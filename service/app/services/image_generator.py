import os
import base64
from typing import Optional
import dashscope
from dashscope import MultiModalConversation


class ImageGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    def generate(
        self,
        prompt: str,
        reference_image: Optional[bytes] = None,
        reference_image_url: Optional[str] = None
    ) -> bytes:
        """
        使用 Qwen-Image-2.0 生成图片。

        Args:
            prompt: 生成提示词
            reference_image_url: 参考图 OSS 签名 URL（优先使用）
            reference_image: 参考图字节数据（转 base64）

        Returns:
            生成的图片字节数据
        """
        content = []

        if reference_image_url:
            content.append({"image": reference_image_url})
        elif reference_image:
            b64 = base64.b64encode(reference_image).decode('utf-8')
            content.append({"image": f"data:image/jpeg;base64,{b64}"})

        content.append({"text": prompt})

        messages = [{"role": "user", "content": content}]

        response = MultiModalConversation.call(
            api_key=self.api_key,
            model="qwen-image-2.0",
            messages=messages,
            result_format='message',
            stream=False,
            n=1,
            watermark=False,
            negative_prompt=""
        )

        if response.status_code != 200:
            raise ValueError(f"Qwen-Image-2.0 调用失败: {response.message}")

        output = response.output.choices[0].message.content
        for item in output:
            if "image" in item:
                image_url = item["image"]
                import urllib.request
                with urllib.request.urlopen(image_url, timeout=60) as resp:
                    return resp.read()

        raise ValueError(f"Qwen-Image-2.0 未返回图片: {response}")


image_generator = ImageGenerator()
