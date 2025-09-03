from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel, EmailStr
from db import getdb
from pymysql import cursors
import secrets
import time
from datetime import datetime, timedelta

app=FastAPI()

@app.get('/')
def testMessage():
    return {"Hello":"World"}

class emailItem(BaseModel):
    mail:EmailStr
@app.post("/token/")
def generateToken(item:emailItem,db:cursors.Cursor=Depends(getdb)):
    try:
        # 生成token和有效期（7天）
        token = secrets.token_hex(16)
        current_time = datetime.now()
        deadline = current_time + timedelta(days=7)

        # 使用参数化查询防止SQL注入
        insert_cmd = "INSERT INTO TRS_AUTHTOKEN (account, token, deadline) VALUES (%s, %s, %s)"
        db.execute(insert_cmd, (item.mail, token, deadline.strftime('%Y-%m-%d')))

        # 清理过期token（使用当前时间）
        delete_cmd = "DELETE FROM TRS_AUTHTOKEN WHERE deadline < %s"
        db.execute(delete_cmd, (current_time.strftime('%Y-%m-%d'),))

        # 提交事务
        db.connection.commit()
        return token

    except Exception as e:
        # 发生错误时回滚
        db.connection.rollback()
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")
