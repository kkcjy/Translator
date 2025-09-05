import pymysql
def getConnection():
    connection=pymysql.connect(
        host="localhost",
        user="server",
        password="server",
        database="Translator",
        charset="utf8"
    )
    return connection
def getdb():
    connection=getConnection()
    db=connection.cursor()
    try:
        yield db
    finally:
        db.close()
        connection.close()