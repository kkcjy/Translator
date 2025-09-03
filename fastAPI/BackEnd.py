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

class EmailItem(BaseModel):
    mail:EmailStr
@app.post("/token/")
def generateToken(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    try:
        token=secrets.token_hex(16)
        cmd=f"INSERT INTO TRS_AUTHTOKEN (account,token,deadline) VALUES ({item.mail},{token},{time.strftime('%Y-%m-%d',time.localtime())})"
        db.execute(cmd)
        cmd=f"DELETE FROM TRS_AUTHTOKEN WHERE deadline < '{time.strftime('%Y-%m-%d',time.localtime())}'"
        db.execute(cmd)
        db.execute("COMMIT")
        return token
    except Exception as e:
        db.execute("ROLLBACK")
        raise HTTPException(status_code=500,detail=f"Token generate failed: {str(e)}")

