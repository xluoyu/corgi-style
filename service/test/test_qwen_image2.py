"""
Qwen-Image-2.0 生图测试脚本
"""
import json
import os
import dashscope
from dashscope import MultiModalConversation

# 配置 API URL 和 Key
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-588d318c6a4841f98a9224bfb2960f73")

# 参考图 URL（支持私有 OSS 签名 URL）
# input_images = [
#     "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/thtclx/input1.png",
#     "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/iclsnx/input2.png",
# ]

messages = [
    {
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/thtclx/input1.png"},
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/iclsnx/input2.png"},
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/gborgw/input3.png"},
            {"text": "图1中的女生穿着图2中的黑色裙子按图3的姿势坐下"}
        ]
    }
]

# response = ImageSynthesis.call(
#     model="qwen-image-2.0",
#     prompt="生成一张白色T恤的产品图，白色背景，平铺展示",
#     input_images=input_images,
#     n=1,
#     size="1024x1024"
# )

response = MultiModalConversation.call(
    api_key=dashscope.api_key,
    model="qwen-image-2.0",
    messages=messages,
    result_format='message',
    stream=False,
    n=2,
    watermark=True,
    negative_prompt=""
)

print(json.dumps(response, ensure_ascii=False))
