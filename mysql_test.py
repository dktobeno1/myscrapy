import mysql.connector as connector
import time

while True:
    try:
        conn = connector.connect(host="192.168.93.8/pma", user="root", password="111111", database="test", charset="utf8",
                                 connect_timeout=10)
        print('数据库连接成功！')
        break
    except:
        print('数据库连接失败，等待延时重连......')
        time.sleep(30)
cursor = conn.cursor()
sql_home = sql_home = 'select * from shijue_project_new where biz=%s and time is null'
cursor.execute(sql_home,('MzI5NTEzODQ1Mg==',))
home_tup = cursor.fetchone()
print(home_tup)
time.sleep(2)
conn.close()
