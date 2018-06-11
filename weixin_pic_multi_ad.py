import re,requests,json,time,os,sys,queue,multiprocessing
from multiprocessing.managers import BaseManager
import mysql.connector as connector

def wx_init():
    with open('weixin.ini') as f:
        aa = f.read()
    pro_count = re.findall(r'pro:(\d)',aa)[0]
    return pro_count

#task_queue = queue.Queue()
class QueueManager(BaseManager):
    pass

QueueManager.register('get_task_queue')
server_addr = '127.0.0.1'
m = QueueManager(address=('127.0.0.1', 5666), authkey=b'abc')
m.connect()
task = m.get_task_queue()

def handle_pro(que):
    while True:
        print('------等待队列消息------')
        while que.empty():
            time.sleep(0.5) 
        msg_dic = que.get()
        print('获取队列消息，开始处理...')
        biz_msg = msg_dic['biz_msg']
        print('连接数据库...')
        while True:
            try:
                conn = connector.connect(host="10.31.150.47", user="root", password="111111", database="test", charset="utf8",connect_timeout=10)
                print('数据库连接成功！')
                break
            except:
                print('数据库连接失败，等待延时重连......')
                time.sleep(30)
        cursor = conn.cursor()
        sql_home = 'select * from temp_headers where biz=%s'
        print('查询数据库中是否含有 %s 的home_headers信息...'% biz_msg)
        print('-------------------------------------------------------')
        time.sleep(2)
        cursor.execute(sql_home,(biz_msg,))
        home_tup = cursor.fetchone()
        if not home_tup:
            print('数据库中没有 %s 的home_headers信息，默认已抓取，继续等待消息'% biz_msg)
            continue
        print('数据库中有 %s 的home_headers信息！获取headers信息并查看当前微信号是否正在抓取...'% biz_msg)
        print('-------------------------------------------------------')
        #time.sleep(1)
        sql_monitor = 'select * from wechat_doing where x_wechat_uin=%s'
        cursor.execute(sql_monitor,(home_tup[7],))
        monitor_tup = cursor.fetchone()
        if monitor_tup:
            print('%s 微信号正在抓取，延时30秒后将msg信息压入队列继续排队'% home_tup[7])
            print('-------------------------------------------------------')
            time.sleep(30)
            que.put(msg_dic)
            continue
        else:
            print('%s 微信号没有正在抓取的任务，准备抓取...'% home_tup[7])
            #time.sleep(1)
            sql_wuin = 'insert into wechat_doing(x_wechat_uin) values (%s)'
            cursor.execute(sql_wuin,(home_tup[7],))
            conn.commit()
            print('当前任务已记录...')
            print('-------------------------------------------------------')
            #time.sleep(1)
        print('删除数据库中%s的home_headers信息...'% biz_msg)
        #time.sleep(1)
        sql_delete = 'delete from temp_headers where biz=%s'
        cursor.execute(sql_delete,(biz_msg,))
        conn.commit()
        print('%s 的home_headers信息已删除，提取公众号ID信息...'% biz_msg)
        print('-------------------------------------------------------')
        time.sleep(1)
        sql_select = 'select * from shijue_project_new where biz=%s'
        cursor.execute(sql_select,(biz_msg,))
        ids_tup = cursor.fetchall()[0]
        print('公众号ID信息提取成功！')
        conn.close()
        
        url_home = home_tup[1]
        User_Agent = home_tup[6]
        biz = home_tup[2]
        x_wechat_key = home_tup[8]
        x_wechat_uin = home_tup[7]
        Cookie_home = home_tup[12]
        url_msg2 = re.findall(r'&count=10.+?json',msg_dic['url_msg'])[0]
        Cookie_msg = msg_dic['Cookie_msg']
        
        headers_home = {'Host':'mp.weixin.qq.com',
           'Connection':'keep-alive',
           #'Upgrade-Insecure-Requests':'1',
           'User-Agent':User_Agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/wxpic,image/sharpp,*/*;q=0.8',
           'Accept-Language':'zh-CN,en-US;q=0.8',
           'x-wechat-uin':x_wechat_uin,
           'x-wechat-key':x_wechat_key,
           'Cookie':Cookie_home,
            #'Q-UA2':Q_UA2,
            #'Q-GUID':Q_GUID,
           #'Q-Auth':'31045b957cf33acf31e40be2f3e71c5217597676a9729f1b'

    }
        headers_msg = {'Host':headers_home['Host'],
           'Connection':'keep-alive',
           'X-Requested-With':'XMLHttpRequest',
           'User-Agent':headers_home['User-Agent'],
            'Accept':'*/*',
           'Referer':url_home,
            'Accept-Language':'zh-CN,en-US;q=0.8',
           'Cookie':Cookie_msg,
            #'Q-UA2':headers_home['Q-UA2'],
            #'Q-GUID':headers_home['Q-GUID'],
           #'Q-Auth':headers_home['Q-Auth']

    }
        main_id = ids_tup[1]
        sub_id = ids_tup[2]
        company_id = ids_tup[6]
        print('启动抓取程序')
        print('>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<')
        crawl_url(url_home,biz,url_msg2,main_id,sub_id,company_id,headers_home,headers_msg,x_wechat_uin)


def crawl_url(url_home,biz,url_msg2,main_id,sub_id,company_id,headers_home,headers_msg,x_wechat_uin):
    #更新数据库中数据状态
    print('连接数据库以更新任务状态...')
    while True:
        try:
            conn = connector.connect(host="10.31.150.47", user="root", password="111111", database="test", charset="utf8",connect_timeout=10)
            print('数据库连接成功！')
            break
        except:
            print('数据库连接失败，等待延时重连......')
            time.sleep(30)
    cursor = conn.cursor()
    status_doing = 'update shijue_project_new set status=%s where biz=%s'
    cursor.execute(status_doing,(3,biz))
    conn.commit()
    print('更新数据库任务状态为抓取中')
    
    result_home = requests.get(url_home, headers = headers_home, timeout = 20)
    pattern_url = re.compile(r'content_url&quot;:&quot;(http:.+?wechat_redirect).+?cover&quot;:&quot;(http:.+?)&quot;')
    pattern_id = re.compile(r'&quot;id&quot;:(.+?),')
    list_url = re.findall(pattern_url, result_home.text)
    list_id = re.findall(pattern_id, result_home.text)
    list_urlupdate = []
    for each in list_url:
        each_new = []
        for i in each:            
            each_new.append(i.replace(r'\\/',r'/').replace(r'amp;',''))
        list_urlupdate.append(each_new)
    print(len(list_urlupdate))
    print(list_id)
    for url_content in list_urlupdate:
        data = {}
        data['url_article'] = url_content[0]
        data['url_pic'] = url_content[1]
        data['task_id'] = main_id
        data['clue_id'] = sub_id
        data['company_id'] = company_id
        a = {'resource':data}
        d = json.dumps(a)
        url = 'http://shijue.qingapi.cn/shijue_weixin/start'
        #print('发送数据')
        try:
            r = requests.post(url,data = d,timeout=20)
            print(r.text)
        except:
            print('发送失败')
    while True:
        time.sleep(2)
        try:
            url_msg = r'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=' + biz + r'==&f=json&frommsgid='+ str(list_id[-1]) + url_msg2
        except:
            print('--------'*7)
            print('--------'*7)
            print('抓取失败，请查看微信号是否被封')
            print('--------'*7)
            print('--------'*7)
            #更新数据库数据状态
            status_done = 'update shijue_project_new set status=%s where biz=%s'
            cursor.execute(status_done,(5,biz))
            conn.commit()
            print('更新数据库任务状态为抓取失败')
            time.sleep(1)
            sql_upd_uin = 'delete from wechat_doing where x_wechat_uin=%s'
            cursor.execute(sql_upd_uin,(x_wechat_uin,))
            conn.commit()
            print('%s 微信号抓取状态已更新'% x_wechat_uin)
            print('<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>')
            break
        result_msg = requests.get(url_msg, headers = headers_msg, timeout = 20)
        dic_msg = json.loads(result_msg.text)
        url_list = []
        list_id = []
        try:
            for each in json.loads(dic_msg['general_msg_list'])['list']:
                if 'app_msg_ext_info' in each.keys():
                    if each['app_msg_ext_info']['content_url']:
                        url_list.append([each['app_msg_ext_info']['content_url'],each['app_msg_ext_info']['cover']])
                    if 'multi_app_msg_item_list' in each['app_msg_ext_info'].keys():
                        for a in each['app_msg_ext_info']['multi_app_msg_item_list']:
                            if a['content_url']:
                                url_list.append([a['content_url'],a['cover']])
                            
                list_id.append(each['comm_msg_info']['id'])
        except:
            print('--------'*7)
            print('--------'*7)
            print('抓取失败，请查看微信号是否被封')
            print('--------'*7)
            print('--------'*7)
            #更新数据库数据状态
            status_done = 'update shijue_project_new set status=%s where biz=%s'
            cursor.execute(status_done,(5,biz))
            conn.commit()
            print('更新数据库任务状态为抓取失败')
            time.sleep(1)
            sql_upd_uin = 'delete from wechat_doing where x_wechat_uin=%s'
            cursor.execute(sql_upd_uin,(x_wechat_uin,))
            conn.commit()
            print('%s 微信号抓取状态已更新'% x_wechat_uin)
            print('<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>')
            break
        for content_url in url_list:
            data = {}
            data['url_article'] = content_url[0]
            data['url_pic'] = content_url[1]
            data['task_id'] = main_id
            data['clue_id'] = sub_id
            data['company_id'] = company_id
            a = {'resource':data}
            d = json.dumps(a)
            url = 'http://shijue.qingapi.cn/shijue_weixin/start'
            #print('发送数据')
            try:
                r = requests.post(url,data = d,timeout=20)
                print(r.text)
            except:
                print('发送失败')
        print(len(url_list))
        print(list_id)
        if len(list_id) < 10:
            print('任务抓取完成(%s,%s,%s)'% (main_id, sub_id,company_id))
            #更新数据库数据状态
            status_done = 'update shijue_project_new set status=%s,time=%s where biz=%s'
            cursor.execute(status_done,(4,time.time(),biz))
            conn.commit()
            print('更新数据库任务状态为抓取完成')
            #更新微信号抓取状态
            time.sleep(1)
            sql_upd_uin = 'delete from wechat_doing where x_wechat_uin=%s'
            cursor.execute(sql_upd_uin,(x_wechat_uin,))
            conn.commit()
            print('%s 微信号抓取状态已更新'% x_wechat_uin)
            time.sleep(1)
            #更新客户接口任务状态
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
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>')
                    break
                except:
                    print('客户接口更新失败，等待延时更新')
                    time.sleep(5)
            break
    conn.close()

if __name__ == '__main__':
    pro_count = wx_init()
    pro_list = [multiprocessing.Process(target = handle_pro,args = (task,)) for each in range(0,int(pro_count))]

    for each in pro_list:
        each.start()
        time.sleep(5)
    for each in pro_list:
        each.join()

    
