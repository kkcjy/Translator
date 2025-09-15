import base64
import io
import json
import random
from contextlib import asynccontextmanager

import torch
from PIL import Image
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, EmailStr
from qwen_vl_utils import process_vision_info
from starlette.middleware.cors import CORSMiddleware
from pymysql import cursors
import secrets
import time
from datetime import datetime
import logging
import requests
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from transformers import AutoModelForCausalLM, AutoProcessor

from db import getdb
from file import read_document_file
#from model.Model_API.DeepSeek_R1_API import DeepSeek_R1_translate
Model_URI = "https://www.u2985420.nyat.app:62835/"
MODEL_PATH = "../model/DotsOCR"  # 替换为你的OCR模型实际路径
ocr_model = None
ocr_processor = None

# 配置FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME="2790598460@qq.com",  # 替换为您的邮箱
    MAIL_PASSWORD="stcgixwiimlxdejc",     # 替换为您的邮箱密码或应用专用密码
    MAIL_FROM="2790598460@qq.com",      # 替换为您的邮箱
    MAIL_PORT=465,
    MAIL_SERVER="smtp.qq.com",            # 替换为您的邮件服务器
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    VALIDATE_CERTS=True
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app:FastAPI):
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
    yield

app=FastAPI(lifespan=lifespan)#lifespan=lifespan

#跨域请求开放，需根据前端地址更改。
app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=True,
    allow_methods='*',
    allow_headers='*'
)

#用于申请Token/获取账户密码的Model/获取验证码
class EmailItem(BaseModel):
    email:EmailStr

#用于根据邮箱和Token查找保存的密码的Model
class EmailTokenItem(BaseModel):
    email:EmailStr
    token:str

#用于注册的Model
class UserItem(BaseModel):
    username:str
    email:EmailStr
    password:str

#用于设置修改的Model
class USettingItem(BaseModel):
    userId:int
    avatar:str
    fontSize:int
    bgMode:str

#用于密码重置的Model
class ResetItem(BaseModel):
    email:EmailStr
    new_password:str

#用于删除历史记录的Model
class DelHistoryItem(BaseModel):
    ids:list

class TranslationRequest(BaseModel):
    source_text: str
    source_lang: str = "zh"
    target_lang: str = "en"
    model_name: str
    userId:str | None

class UserHistoryRequest(BaseModel):
    user_mail:EmailStr
    limit:int = 10
    offset: int =0

#用于用户反馈的Model
class FeedbackItem(BaseModel):
    userId:str
    hisId:str
    model:str
    judge:bool
    comment:str

def translate(text: str, source_lang: str, target_lang: str, model_name: str) -> str:
    direction = source_lang + "-" + target_lang
    name2request={"DeepSeek-R1":"DeepSeek-R1","通义千问":"Qwen3"}
    if model_name == "高速翻译模型":
        if source_lang == "zh" and target_lang == "en":
            return f"[Fast Model] English translation of: {text}"
        else:
            return f"[Fast Model] 中文翻译: {text}"

    elif model_name == "高精度翻译模型":
        if source_lang == "zh" and target_lang == "en":
            return f"[Precision Model] Accurate English translation: {text}"
        else:
            return f"[Precision Model] 精准中文翻译: {text}"

    else:
        json_data={"text":text,"direction":source_lang+'-'+target_lang,"model":name2request[model_name]}
        try:
            response=requests.post(Model_URI,json=json_data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print("Failed to translate.")
            print(e)
            raise HTTPException(status_code=503,detail=e)

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

@app.get('/')
def test_message():
    return {"message": "文枢翻译API服务", "status": "运行中"}

#请求Token
@app.post("/token")
def generateToken(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    try:
        token=secrets.token_hex(16)
        cmd=f"INSERT INTO TRS_AUTHTOKEN (account,token,deadline) VALUES ('{item.email}','{token}','{time.strftime('%Y-%m-%d',time.localtime(time.time()+7*86400))}')"
        db.execute(cmd)
        cmd=f"DELETE FROM TRS_AUTHTOKEN WHERE deadline < '{time.strftime('%Y-%m-%d',time.localtime())}'"
        db.execute(cmd)
        db.execute("COMMIT")
        return token
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Token generate failed: {str(e)}")

#根据邮箱和Token查找保存的密码
@app.post("/password")
def getPassword(item:EmailTokenItem,db:cursors.Cursor=Depends(getdb)):
    cmd=f"SELECT account FROM TRS_AUTHTOKEN WHERE token = '{item.token}' AND deadline > '{time.strftime('%Y-%m-%d',time.localtime())}'"
    db.execute(cmd)
    tokenRecords=db.fetchall()
    for record in tokenRecords:
        if record[0]==item.email:
            cmd=f"SELECT password FROM TRS_USER WHERE email = '{item.email}'"
            db.execute(cmd)
            password=db.fetchone()
            return password
    return None

#根据邮箱查找用户密码和ID（登录验证）
@app.post("/login")
def authAccount(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    cmd=f"SELECT password,userId FROM TRS_USER WHERE email = '{item.email}'"
    db.execute(cmd)
    if db.rowcount!=1:
        return None
    else:
        user=db.fetchone()
        cmd = f"SELECT avatar,size,color FROM TRS_SETTING WHERE userId = {user[1]}"
        db.execute(cmd)
        setting = db.fetchone()
        if not setting:
            return {
                "user": user,
                "data": None,
            }
        else:
            return {
                "user": user,
                "data": setting,
            }
#查找可能已经注册的邮箱
@app.get("/users")
def registered(email:str,db:cursors.Cursor=Depends(getdb)):
    cmd=f"SELECT * FROM TRS_USER WHERE email = '{email}'"
    db.execute(cmd)
    if db.rowcount>=1:
        return "registered"
    else:
        return None

# 发送验证码端点
@app.post("/send-verification-code")
async def send_verification_code(request: EmailItem):
    email = request.email
    # 生成6位随机验证码
    code = ''.join(random.choices('0123456789', k=6))
    # 创建邮件内容
    message = MessageSchema(
        subject="您的验证码",
        recipients=[email],
        body=f"您的验证码是: {code}。该验证码10分钟内有效。",
        subtype="plain"
    )
    # 发送邮件
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        print(e)
    return {
        "message": "验证码已发送",
        "code":code
    }
#注册
@app.post("/register")
def register(item:UserItem,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd=f"INSERT INTO TRS_USER (email,password) VALUE ('{item.email}','{item.password}')"
        db.execute(cmd)
        db.execute("COMMIT")
        db.execute(f"SELECT userId FROM TRS_USER WHERE email = '{item.email}' AND password = '{item.password}'")
        UID=db.fetchone()
        with open("img/default_ava.jpg", 'rb') as file:
            image_blob = file.read()
        cmd = f"INSERT INTO TRS_SETTING (userId,username,avatar) VALUE ({UID[0]},'{item.username}','{'data:image/jpeg;base64,' + base64.b64encode(image_blob).decode('utf-8')}')"
        db.execute(cmd)
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Fail to write into database:{str(e)}")

#修改设置
@app.put("/settings")
def setting(item:USettingItem, db:cursors.Cursor=Depends(getdb)):
    try:
        cmd=f"UPDATE TRS_SETTING SET avatar='{item.avatar}', size={item.fontSize}, color='{item.bgMode}' WHERE userId={item.userId}"
        db.execute(cmd)
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Fail to write into database:{str(e)}")

#获取用户名
@app.get("/user/{userId}")
def uid(userId:int,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd="SELECT username FROM TRS_SETTING WHERE userId=%s"
        db.execute(cmd,userId)
        if db.rowcount>1:
            raise HTTPException(500,"从数据库读取到多条满足条件的用户，请联系系统管理员")
        else:
            return db.fetchone()
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(500,detail=f"Fail to get data:{str(e)}")

#修改用户名
@app.put("/user/{userId}")
def mdfuid(userId:int,newname:str,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd="UPDATE TRS_SETTING SET username=%s WHERE userId=%s"
        db.execute(cmd,(newname,userId))
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(500,detail=f"Fail to write into database:{str(e)}")

#修改密码
@app.put("/password/reset")
def reset(item:ResetItem,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd=f"UPDATE TRS_USER SET password='{item.new_password}' WHERE email='{item.email}'"
        db.execute(cmd)
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Fail to write into database:{str(e)}")

# 执行翻译任务
@app.post("/translate")
async def translate_text(request: TranslationRequest, db: cursors.Cursor = Depends(getdb)):
    name2request={"DeepSeek-R1":"DeepSeek-R1","通义千问":"Qwen3"}
    try:
        translated = translate(request.source_text, request.source_lang, request.target_lang, request.model_name)
        translated_text=translated[name2request[request.model_name]]
        hisId=None
        if request.userId:
            cmd="INSERT INTO TRS_T_HISTORY (userId,date,type,input,output) VALUES (%s,%s,%s,%s,%s)"
            db.execute(cmd,(request.userId,datetime.now(),0,request.source_text,translated_text))
            hisId=db.lastrowid
            db.connection.commit()
        print(translated_text,'\n',hisId)
        return {"text":translated_text,"hisId":hisId}

    except Exception as e:
        db.connection.rollback()
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

#图片翻译
@app.post("/translate/pic")
async def read_pic(file:UploadFile=File(...)):
    name2request = {"DeepSeek-R1": "DeepSeek-R1", "通义千问": "Qwen3"}
    try:
        # 验证文件类型（仅允许图片）
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="仅支持图片文件（png/jpg等）")

        # 读取图片内容并转换为PIL Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 调用OCR处理
        ocr_result = process_ocr(image)

        # # 可选：将结果存储到数据库（需先创建表TRS_OCR_RESULTS）
        # current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        # cmd = """
        #     INSERT INTO TRS_OCR_RESULTS
        #     (filename, content_type, ocr_result, create_time)
        #     VALUES (%s, %s, %s, %s)
        # """
        # # 将JSON结果转为字符串存储
        # db.execute(cmd, (file.filename, file.content_type, json.dumps(ocr_result), current_time))
        # db.execute("COMMIT")
        # 返回OCR结果
        return {
            "filename": file.filename,
            "ocr_result": ocr_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")
    finally:
        await file.close()  # 确保文件句柄关闭

# 文件翻译
@app.post("/translate/file")
async def read_file(file:UploadFile=File(...)):
    try:
        if not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".docx")):
            raise HTTPException(status_code=400, detail="仅支持 PDF 或 DOCX 文件")

        contents = await file.read()
        file_obj = io.BytesIO(contents)

        text = read_document_file(file_obj, file.filename)

        # 返回文件名与文件内容
        return {
            "filename": file.filename,
            "text": text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        await file.close()

#获取用户翻译历史记录
@app.get("/history/{userId}")
def getHistory(userId:int,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd=f"SELECT hisId,date,type,input,output FROM TRS_T_HISTORY WHERE userId={userId}"
        db.execute(cmd)
        results=db.fetchall()
        rtn=[]
        for row in results:
            jsonstr='{"id":"'+str(row[0])+'","time":"'+row[1].strftime("%Y-%m-%d %H:%M")+'","original":"'+row[3]+'","translation":"'+row[4]+'","type":"'
            if row[2]==1:
                jsonstr+='picture"}'
            elif row[2]==2:
                jsonstr+='file"}'
            else:
                jsonstr+='text"}'
            rtn.append(jsonstr)
        return rtn
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Fail to read from database:{e}")

@app.post("/history/delete")
def delHistory(item:DelHistoryItem,db:cursors.Cursor=Depends(getdb)):
    cmd="DELETE FROM TRS_T_HISTORY WHERE hisId=%s"
    try:
        for hid in item.ids:
            db.execute(cmd,hid)
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Fail to write into database:{str(e)}")

#用户反馈存储
@app.put("/feedback")
def feedback(item:FeedbackItem,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd="INSERT INTO TRS_T_FEEDBACK (userId,hisId,model,judge,comment) VALUES (%s,%s,%s,%s,%s)"
        db.execute(cmd,(item.userId,item.hisId,item.model,item.judge,item.comment))
        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(500,f"Fail to write into database:{str(e)}")

# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)