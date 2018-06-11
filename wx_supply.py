import re,requests,json,time,os,sys,easygui,queue,multiprocessing
import mysql.connector as connector

def handle_supply():
    print('连接数据库...')
    while True:
        try:
            conn = connector.connect(host="47.94.42.60", user="root", password="111111", database="test", charset="utf8",connect_timeout=10)
            print('数据库连接成功！')
            break
        except:
            print('数据库连接失败，等待延时重连......')
            time.sleep(10)
    cursor = conn.cursor()
    print('提取所有home_headers信息...')
    time.sleep(1)
    sql_select = 'select * from temp_headers'
    cursor.execute(sql_select)
    home_list = cursor.fetchall()
    print('home_headers信息提取成功，开始处理...')
    for home_tup in home_list:
        biz = home_tup[2]
        #print(biz)
        time.sleep(1)
        sql_delete = 'delete from temp_headers where biz=%s'
        cursor.execute(sql_delete,(biz,))
        conn.commit()
        print('%s 的home_headers信息已从数据库中删除，提取公众号ID信息'% biz)
        time.sleep(1)
        sql_select1 = 'select * from shijue_project_new where biz=%s'
        cursor.execute(sql_select1,(biz,))
        ids_tup = cursor.fetchone()
        print('公众号ID信息提取成功！开始抓取数据...')
        time.sleep(10)
        main_id = ids_tup[1]
        sub_id = ids_tup[2]
        print('数据抓取完成，更改数据库状态...')
        time.sleep(1)
        status_done = 'update shijue_project_new set status=%s,time=%s where biz=%s'
        cursor.execute(status_done,(4,time.time(),biz))
        conn.commit()
        print('更新数据库任务状态为抓取完成，更新客户接口状态...')
        #更新客户接口任务状态
        time.sleep(2)
        url_client = 'http://eagle.elephant.vcg.com/api/spider-update-clue'
        data_client = {}
        data_client['task_id'] = main_id
        data_client['clue_id'] = sub_id
        data_client['status'] = 3
        while True:
            try:
                r_client = requests.post(url_client,data = data_client,timeout=10)
                print(r_client.status_code)
                print('客户接口任务（%s,%s）状态已更新！'% (main_id,sub_id))
                break
            except:
                print('客户接口更新失败，等待延时更新')
                time.sleep(5)       
    conn.close()

if __name__ == '__main__':
    handle_supply()
