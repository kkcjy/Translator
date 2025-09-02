from fastapi import FastAPI,Depends
from pydantic import BaseModel
from db import getdb
from pymysql import cursors
import secrets
import time

app=FastAPI()

@app.get('/')
def testMessage():
    return {"Hello":"World"}

class emailItem(BaseModel):
    mail:str
@app.post("/token/")
def generateToken(item:emailItem,db:cursors.Cursor=Depends(getdb)):
    token=secrets.token_hex(16)
    cmd=f"INSERT INTO TRS_AUTHTOKEN (account,token,deadline) VALUES ({item.mail},{token},{time.strftime('%Y-%m-%d',time.localtime())})"
    db.execute(cmd)
    cmd=f"DELETE FROM TRS_AUTHTOKEN WHERE deadline < '{time.strftime('%Y-%m-%d',time.localtime())}'"
    db.execute(cmd)
    db.execute("COMMIT")
    return token
