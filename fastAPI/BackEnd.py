from fastapi import FastAPI,Depends,HTTPException, status, Header,Response
from pydantic import BaseModel, EmailStr
from starlette.middleware.cors import CORSMiddleware
import base64

from db import getdb
from pymysql import cursors
import secrets
import time
from datetime import datetime
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app=FastAPI()

#跨域请求开放，需根据前端地址更改。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://0.0.0.0:8080","http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods='*',
    allow_headers='*'
)
#用于申请Token/获取账户密码的Model
class EmailItem(BaseModel):
    mail:EmailStr

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

class TranslationRequest(BaseModel):
    source_text: str
    source_lang: str = "zh"
    target_lang: str = "en"
    model_name: str

class TranslationResponse(BaseModel):
    translation_id: int
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    model_name: str
    translation_time: datetime

class UserHistoryRequest(BaseModel):
    user_mail:EmailStr
    limit:int = 10
    offset: int =0

class TranslationModel:
    def __init__(self):
        pass

    def translate(self, text: str, source_lang: str, target_lang: str, model_name: str) -> str:
        time.sleep(0.5)

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

        elif model_name == "DeepSeek-R1":
            if source_lang == "zh" and target_lang == "en":
                return f"[DeepSeek-R1] AI-powered English translation: {text}"
            else:
                return f"[DeepSeek-R1] AI驱动的中文翻译: {text}"

        elif model_name == "通义千问":
            if source_lang == "zh" and target_lang == "en":
                return f"[Tongyi Qianwen] Multilingual translation: {text}"
            else:
                return f"[通义千问] 多语言翻译: {text}"

        else:
            if source_lang == "zh" and target_lang == "en":
                return f"Translation: {text}"
            else:
                return f"翻译: {text}"


translation_model = TranslationModel()


async def verify_token(authorization: str = Header(...), db: cursors.Cursor = Depends(getdb)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )

    token = authorization[7:]

    query = "SELECT account, deadline FROM TRS_AUTHTOKEN WHERE token = %s"
    db.execute(query, (token,))
    result = db.fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    account, deadline = result
    if datetime.now().date() > deadline:
        delete_query = "DELETE FROM TRS_AUTHTOKEN WHERE token = %s"
        db.execute(delete_query, (token,))
        db.connection.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )

    return account

@app.get('/')
def test_message():
    return {"message": "文枢翻译API服务", "status": "运行中"}

#请求Token
@app.post("/token/")
def generateToken(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    try:
        token=secrets.token_hex(16)
        cmd=f"INSERT INTO TRS_AUTHTOKEN (account,token,deadline) VALUES ('{item.mail}','{token}','{time.strftime('%Y-%m-%d',time.localtime(time.time()+7*86400))}')"
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

#根据邮箱查找用户密码，ID（登录验证）和设置
@app.post("/login")
def authAccount(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    cmd=f"SELECT password,userId FROM TRS_USER WHERE email = '{item.mail}'"
    db.execute(cmd)
    if db.rowcount!=1:
        return None
    else:
        user=db.fetchone()
        cmd=f"SELECT avatar,size,color FROM TRS_SETTING WHERE userId = {user[1]}"
        db.execute(cmd)
        setting=db.fetchone()
        if not setting:
            return {
                "user":user,
                "data":None,
            }
        else:
            return {
                "user":user,
                "data":setting,
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

#注册
@app.post("/register")
def register(item:UserItem,db:cursors.Cursor=Depends(getdb)):
    try:
        cmd=f"INSERT INTO TRS_USER (email,password) VALUE ('{item.email}','{item.password}')"
        db.execute(cmd)
        db.execute("COMMIT")
        db.execute(f"SELECT userId FROM TRS_USER WHERE email = '{item.email}' AND password = '{item.password}'")
        UID=db.fetchone()
        with open("default_ava.jpg",'rb') as file:
            image_blob=file.read()
        cmd=f"INSERT INTO TRS_SETTING (userId,username,avatar) VALUE ({UID[0]},'{item.username}','{'data:image/jpeg;base64,'+base64.b64encode(image_blob).decode('utf-8')}')"
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

@app.post("/translate/", response_model=TranslationResponse)
async def translate_text(
        request: TranslationRequest,
        user_email: str = Depends(verify_token),
        db: cursors.Cursor = Depends(getdb)
):
    try:
        # 调用翻译模型
        translated_text = translation_model.translate(
            request.source_text,
            request.source_lang,
            request.target_lang,
            request.model_name
        )

        # 获取当前时间
        current_time = datetime.now()

        # 将翻译结果存入数据库
        insert_cmd = """
            INSERT INTO TRS_TRANSLATION_HISTORY 
            (account, source_text, translated_text, source_lang, target_lang, model_used, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        db.execute(insert_cmd, (
            user_email,
            request.source_text,
            translated_text,
            request.source_lang,
            request.target_lang,
            request.model_name,
            current_time
        ))

        # 获取插入的ID
        translation_id = db.lastrowid

        # 提交事务
        db.connection.commit()

        logger.info(f"Translation saved for user {user_email}, ID: {translation_id}")

        # 返回响应
        return TranslationResponse(
            translation_id=translation_id,
            source_text=request.source_text,
            translated_text=translated_text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            model_name=request.model_name,
            translation_time=current_time
        )

    except Exception as e:
        db.connection.rollback()
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.get("/history/", response_model=List[TranslationResponse])
async def get_translation_history(
        limit: int = 10,
        offset: int = 0,
        user_email: str = Depends(verify_token),
        db: cursors.Cursor = Depends(getdb)
):
    try:
        query = """
            SELECT id, source_text, translated_text, source_lang, target_lang, model_used, create_time
            FROM TRS_TRANSLATION_HISTORY 
            WHERE account = %s 
            ORDER BY create_time DESC 
            LIMIT %s OFFSET %s
        """

        db.execute(query, (user_email, limit, offset))
        results = db.fetchall()

        # 转换为响应模型
        history = []
        for row in results:
            history.append(TranslationResponse(
                translation_id=row[0],
                source_text=row[1],
                translated_text=row[2],
                source_lang=row[3],
                target_lang=row[4],
                model_name=row[5],
                translation_time=row[6]
            ))

        return history

    except Exception as e:
        logger.error(f"Failed to retrieve translation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@app.get("/translation/{translation_id}", response_model=TranslationResponse)
async def get_translation_by_id(
        translation_id: int,
        user_email: str = Depends(verify_token),
        db: cursors.Cursor = Depends(getdb)
):
    try:
        # 查询特定翻译记录
        query = """
            SELECT id, account, source_text, translated_text, source_lang, target_lang, model_used, create_time
            FROM TRS_TRANSLATION_HISTORY 
            WHERE id = %s
        """

        db.execute(query, (translation_id,))
        result = db.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Translation not found")

        # 检查用户是否有权访问此记录
        if result[1] != user_email:
            raise HTTPException(status_code=403, detail="Access denied")

        # 返回结果
        return TranslationResponse(
            translation_id=result[0],
            source_text=result[2],
            translated_text=result[3],
            source_lang=result[4],
            target_lang=result[5],
            model_name=result[6],
            translation_time=result[7]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve translation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve translation: {str(e)}")


# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}