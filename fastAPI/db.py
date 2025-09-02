import pymysql
def getConnection():
    connection=pymysql.connect(
        host="localhost",
        user="server",
        password="server",
        database="Translator",
        charset="UTF8"
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