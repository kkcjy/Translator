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

class EmailItem(BaseModel):
    mail:str
@app.post("/token/")
def generateToken(item:EmailItem,db:cursors.Cursor=Depends(getdb)):
    token=secrets.token_hex(16)
    cmd=f"INSERT INTO TRS_AUTHTOKEN (account,token,deadline) VALUES ('{item.mail}','{token}','{time.strftime('%Y-%m-%d',time.localtime(time.time()+7*86400))}')"
    db.execute(cmd)
    cmd=f"DELETE FROM TRS_AUTHTOKEN WHERE deadline < '{time.strftime('%Y-%m-%d',time.localtime())}'"
    db.execute(cmd)
    db.execute("COMMIT")
    return token
class EmailTokenItem(BaseModel):
    email:str
    token:str
@app.post("/password")
def getPassword(item:EmailTokenItem,db:cursors.Cursor=Depends(getdb)):
    cmd=f"SELECT account FROM TRS_AUTHTOKEN WHERE token = '{item.token}' AND deadline > '{time.strftime('%Y-%m-%d',time.localtime())}'"
    db.execute(cmd)
    tokenRecords=db.fetchall()
    for record in tokenRecords:
        print(record[0])
        if record[0]==item.email:
            cmd=f"SELECT password FROM TRS_USER WHERE email = '{item.email}'"
            db.execute(cmd)
            password=db.fetchone()
            return password
    return None