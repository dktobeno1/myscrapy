#coding=utf-8
import mysql.connector as connector
import queue,re
from multiprocessing.managers import BaseManager




#task_d = {}
class QueueManager(BaseManager):
    pass

QueueManager.register('get_task_queue')
server_addr = '127.0.0.1'
#print('Connect to server %s...' % server_addr)
m = QueueManager(address=('127.0.0.1', 5666), authkey=b'abc')
m.connect()
task = m.get_task_queue()



def request(flow):
    global task
    print('a')
    if flow.request.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=home'):
        print('捕获home请求')
        home_dic = {}
        conn = connector.connect(host="47.94.42.60", user="root", password="111111", database="test", charset="utf8")
        cursor = conn.cursor()
        try:home_dic['biz'] = re.findall(r'__biz=(.+?)==',flow.request.url)[0]
        except:home_dic['biz'] = re.findall(r'__biz=(.+?)&',flow.request.url)[0]
        home_dic['url_home'] = flow.request.url
        for h in flow.request.headers :
            home_dic[h] = flow.request.headers[h]
        headers_list = list(home_dic.items())
        #print(headers_list)
        #sql = 'insert into temp_headers(%s) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'% ','.join([each[0] for each in headers_list])
        print('准备将home_headers信息写入数据库')
        print('-------------------------------')
        sql = 'insert into temp_headers(%s) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'% ','.join([each[0].replace('-','_') for each in headers_list])
        cursor.execute(sql.replace('?','%s'),[each[1] for each in headers_list])
        conn.commit()
        conn.close()#f.write("%s: %s\n" % (h, flow.request.headers[h] ) )
        print('home_headers信息已写入数据库')
        print('-------------------------------')
    #elif flow.request.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=getmsg'):
    elif flow.request.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=getmsg'):
        #if bool(re.search(r'offset=1\d&',flow.request.url)) or bool(re.search(r'offset=\d&',flow.request.url)):
        print('捕获msg请求')
        msg_dic = {}
        try:msg_dic['biz_msg'] = re.findall(r'__biz=(.+?)==',flow.request.url)[0]
        except:msg_dic['biz_msg'] = re.findall(r'__biz=(.+?)&',flow.request.url)[0]
        msg_dic['url_msg'] = flow.request.url
        for h in flow.request.headers :
            msg_dic[h+'_msg'] = flow.request.headers[h]
        print('准备压入队列')
        print('-------------------------------')
        task.put(msg_dic)
        print('压入完成')
        print('-------------------------------')
#def response(flow):
    #flow.response.headers["newheader"] = "foo"
    #print(flow.response.headers)

