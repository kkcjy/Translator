from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel, EmailStr
from db import getdb
from pymysql import cursors
import secrets
import time
from datetime import datetime, timedelta
# 新增OCR相关依赖
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
import io
import json  # 用于处理OCR返回的JSON结果

app = FastAPI()

# ------------------------------
# OCR模型初始化（启动时加载一次）
# ------------------------------
MODEL_PATH = "../weights/DotsOCR"  # 替换为你的OCR模型实际路径
ocr_model = None
ocr_processor = None


@app.on_event("startup")
def load_ocr_model():
    """服务启动时加载OCR模型（避免每次请求重复加载）"""
    global ocr_model, ocr_processor
    try:
        ocr_model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            load_in_8bit=True
        )
        ocr_processor = AutoProcessor.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True
        )
        print("OCR模型加载成功")
    except Exception as e:
        print(f"OCR模型加载失败: {str(e)}")
        raise  # 模型加载失败时终止服务启动


# ------------------------------
# OCR处理核心函数
# ------------------------------
def process_ocr(image: Image.Image) -> dict:
    """处理图片并返回OCR结果（解析为JSON）"""
    prompt = """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]
2. Layout Categories: ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title']
3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown.
4. Constraints: Original text, sorted by reading order
5. Output: Single JSON object.
"""
    # 构造模型输入
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},  # 传入PIL图片对象
                {"type": "text", "text": prompt}
            ]
        }
    ]
    # 处理输入
    text = ocr_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = ocr_processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    ).to(ocr_model.device)
    # 生成结果
    generated_ids = ocr_model.generate(**inputs, max_new_tokens=24000)
    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    output_text = ocr_processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]
    # 解析为JSON（确保模型输出符合JSON格式）
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        raise ValueError(f"OCR结果格式错误: {output_text}")


# ------------------------------
# 原有接口保持不变
# ------------------------------
@app.get('/')
def test_message():
    return {"message": "文枢翻译API服务", "status": "运行中"}


class EmailItem(BaseModel):
    mail: EmailStr


@app.post("/token/")
def generateToken(item: EmailItem, db: cursors.Cursor = Depends(getdb)):
    try:
        token = secrets.token_hex(16)
        deadline = time.strftime('%Y-%m-%d', time.localtime())
        # 修复SQL注入风险：使用参数化查询
        cmd = "INSERT INTO TRS_AUTHTOKEN (account, token, deadline) VALUES (%s, %s, %s)"
        db.execute(cmd, (item.mail, token, deadline))
        # 清理过期token
        cmd = "DELETE FROM TRS_AUTHTOKEN WHERE deadline < %s"
        db.execute(cmd, (deadline,))
        db.execute("COMMIT")
        return token
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500, detail=f"Token生成失败: {str(e)}")


class EmailTokenItem(BaseModel):
    email: str
    token: str


@app.post("/password")
def getPassword(item: EmailTokenItem, db: cursors.Cursor = Depends(getdb)):
    try:
        current_date = time.strftime('%Y-%m-%d', time.localtime())
        # 修复SQL注入风险：使用参数化查询
        cmd = "SELECT account FROM TRS_AUTHTOKEN WHERE token = %s AND deadline > %s"
        db.execute(cmd, (item.token, current_date))
        tokenRecords = db.fetchall()
        for record in tokenRecords:
            if record[0] == item.email:
                cmd = "SELECT password FROM TRS_USER WHERE email = %s"
                db.execute(cmd, (item.email,))
                password = db.fetchone()
                return password
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"密码获取失败: {str(e)}")


# ------------------------------
# 新增OCR处理接口
# ------------------------------
@app.post("/ocr-process")
async def ocr_process(
        file: UploadFile = File(...),  # 接收上传的图片文件
        db: cursors.Cursor = Depends(getdb)
):
    """上传图片并返回OCR解析结果（可选存储到数据库）"""
    try:
        # 验证文件类型（仅允许图片）
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="仅支持图片文件（png/jpg等）")

        # 读取图片内容并转换为PIL Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 调用OCR处理
        ocr_result = process_ocr(image)

        # 可选：将结果存储到数据库（需先创建表TRS_OCR_RESULTS）
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        cmd = """
            INSERT INTO TRS_OCR_RESULTS 
            (filename, content_type, ocr_result, create_time) 
            VALUES (%s, %s, %s, %s)
        """
        # 将JSON结果转为字符串存储
        db.execute(cmd, (file.filename, file.content_type, json.dumps(ocr_result), current_time))
        db.execute("COMMIT")

        # 返回OCR结果
        return {
            "filename": file.filename,
            "ocr_result": ocr_result
        }
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")
    finally:
        await file.close()  # 确保文件句柄关闭