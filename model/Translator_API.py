"""
https://modelscope.cn/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
https://modelscope.cn/models/Qwen/Qwen3-0.6B
"""
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import re
import subprocess
import time
import sys
import socket
import threading

clients = {
    "DeepSeek-R1": OpenAI(
        base_url="http://127.0.0.1:8010/v1",
        api_key="sk-placeholder"
    ),
    "Qwen3": OpenAI(
        base_url="http://127.0.0.1:8020/v1",
        api_key="sk-placeholder"
    )
}

model_path = {
    "DeepSeek-R1": "/home/kkcjy/Translator/model/DeepSeek-R1",
    "Qwen3": "/home/kkcjy/Translator/model/Qwen3"
}

app = FastAPI()

def clean_translation(text: str, single_line: bool = False) -> str:
    if "</think>" in text.lower():
        text = text.split("</think>", maxsplit=1)[-1].strip()
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    if not lines:
        return text
    
    return " ".join(lines) if single_line else "\n".join(lines)

def model_translate(model: str, text: str, direction: str, single_line: bool = False) -> str:
    if model not in clients:
        raise ValueError(f"未知模型: {model} (可选模型: {list(clients.keys())})")

    if direction not in ["zh-en", "en-zh"]:
        raise ValueError("无效的翻译方向，必须是 'zh-en' 或 'en-zh'")
    
    target_lang = "English" if direction == "zh-en" else "Chinese"

    prompt = (
        f"Translate the following text into {target_lang} accurately and professionally. "
        "Maintain the original meaning, tone, and style. "
        "Provide only the translated text without any explanations, comments, or additional text. "
        "Preserve formatting, punctuation, and line breaks if present.\n\n"
        f"{text}"
    )

    try:
        response = clients[model].chat.completions.create(
            model=model_path[model],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024 
        )
        raw_output = response.choices[0].message.content
        return clean_translation(raw_output, single_line=single_line)
    except Exception as e:
        print(f"{model} 翻译失败: {e}")
        return ""

class TranslationRequest(BaseModel):
    text: str
    direction: str
    model: str

@app.post("/")
def translate(req: TranslationRequest):
    result = model_translate(req.model, req.text, req.direction)
    return {req.model: result}

def print_output(pipe, model_name):
    while True:
        line = pipe.readline()
        if not line:
            break
        print(f"[{model_name}] {line.decode().strip()}")

def load_model_blocking(model: str, host="127.0.0.1", port=None, timeout=600):
    if model == "DeepSeek-R1":
        port = port or 8010
        cmd = [
            "vllm", "serve", model_path[model],
            "--host", host,
            "--port", str(port),
            "--gpu-memory-utilization", "0.8",
            "--max-model-len", "1504"
        ]
    elif model == "Qwen3":
        port = port or 8020
        cmd = [
            "vllm", "serve", model_path[model],
            "--host", host,
            "--port", str(port),
            "--gpu-memory-utilization", "0.8",
            "--max-model-len", "2048"
        ]
    else:
        raise ValueError(f"未知模型: {model}")

    print(f"🔧 启动命令: {' '.join(cmd)}")
    print("-" * 60)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    threading.Thread(target=print_output, args=(proc.stdout, model), daemon=True).start()
    threading.Thread(target=print_output, args=(proc.stderr, model), daemon=True).start()

    wait_for_port(host, port, timeout=timeout)

    print(f"✅ {model} 模型服务已完全就绪")
    return proc, port

def wait_for_port(host: str, port: int, timeout: int = 300):
    start_time = time.time()
    loading_chars = ["|", "/", "-", "\\"]
    i = 0
    
    print(f"⏳ 等待 {host}:{port} 服务就绪...")
    
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"\n✅ 端口 {host}:{port} 已就绪")
                return True
        except OSError:
            elapsed = int(time.time() - start_time)
            print(f"🕒 等待中 {elapsed}s {loading_chars[i % 4]}", end='\r')
            i += 1
            time.sleep(2)
    raise TimeoutError(f"❌ 等待端口 {host}:{port} 超时")

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("❌ 输入格式不正确，请使用: python3 Translator_API.py <DeepSeek-R1 / Qwen3>")
        sys.exit(1)

    model_name = sys.argv[1]
    if model_name not in ["DeepSeek-R1", "Qwen3"]:
        print(f"❌ 不支持的模型: {model_name}")
        sys.exit(1)

    print(f"🚀 阻塞启动模型 {model_name} ...")
    proc, port = load_model_blocking(model_name)

    test_text = "模型启动"
    test_dir = "zh-en"
    print("🧪 测试翻译接口...")
    result = model_translate(model_name, test_text, test_dir)
    print(f"📊 [测试结果] {model_name}: {test_text} -> {result}")

    uvicorn.run("__main__:app", host="0.0.0.0", port=8866, reload=False)

    if proc:
        proc.terminate()
        print(f"🛑 已终止 {model_name} 进程")