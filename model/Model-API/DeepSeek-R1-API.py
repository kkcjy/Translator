"""
1. 模型下载(DeepSeek-R1-Distill-Qwen-1.5B)
https://modelscope.cn/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B

2. Python 翻译函数调用本地 vLLM 服务流程
Python 翻译函数
   │  （调用 OpenAI 兼容接口）
   ▼
HTTP 请求
   │  （发送到本地 vLLM 服务）
   ▼
vLLM 推理引擎
   │  （加载 DeepSeek-R1 模型权重、管理显存与并行计算）
   ▼
GPU/CPU 计算
   │  （模型生成翻译结果）
   ▼
返回结果
   │  （HTTP 响应回 Python 函数）
   ▼
Python 函数输出翻译文本

3. vLLM 服务启动示例
vllm serve /home/kkcjy/Translator/model/DeepSeek-R1 --host 127.0.0.1 --port 8000 --gpu-memory-utilization 0.8 --max-model-len 1504

4. 对外接口
translate_text(text: str, direction: str) -> str:
- text (str)：待翻译文本
- direction (str)：翻译方向：
    - "zh-en"：中文 -> 英文
    - "en-zh"：英文 -> 中文
- str：翻译结果
"""

from openai import OpenAI
import re

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",        # 本地 vLLM 服务地址
    api_key="sk-placeholder"
)

def clean_translation(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        return lines[-1]
    return text.strip()

def translate_text(text: str, direction: str) -> str:
    if direction not in ["zh-en", "en-zh"]:
        raise ValueError("direction must be 'zh-en' or 'en-zh'")

    target_lang = "English" if direction == "zh-en" else "Chinese"
    prompt = (
        f"Translate the following text into {target_lang}. "
        "Respond in a single line. Only provide the translated text. No explanations, no thoughts, no commentary.\n\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model="/home/kkcjy/Translator/model/DeepSeek-R1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512
        )
        raw_output = response.choices[0].message.content
        return clean_translation(raw_output)
    except Exception as e:
        print(f"翻译失败: {e}")
        return ""