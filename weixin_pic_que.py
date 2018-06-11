import re,requests,json,time,os,sys,easygui,queue
from multiprocessing.managers import BaseManager
import mysql.connector as connector

headers_home = ''
headers_msg = ''

task_queue = queue.Queue()
class QueueManager(BaseManager):
    pass
def give_task_queue():
    return task_queue

def test():
    global headers_home
    global headers_msg
    
    QueueManager.register('get_task_queue', callable=give_task_queue)
    manager = QueueManager(address=('127.0.0.1', 5666), authkey=b'abc')
    manager.start()
    task = manager.get_task_queue()
    while True:
        print('等待队列消息...')
        msg_dic = task.get(True)
        print('获取队列消息，开始处理...')
        biz_msg = msg_dic['biz_msg']
        conn = connector.connect(host="47.94.42.60", user="root", password="111111", database="wx_crawl", charset="utf8")
        cursor = conn.cursor()
        sql_home = 'select * from temp_headers where biz=%s'
        cursor.execute(sql_home,(biz_msg,))
        home_tup = cursor.fetchone()
        if not home_tup:
            print('翻页过多')
            continue
        print('数据库中有 %s 的home_headers信息！'% biz_msg)
        #print(home_tup)
        sql_delete = 'delete from temp_headers where biz=%s'
        cursor.execute(sql_delete,(biz_msg,))
        conn.commit()
        print('%s 的home_headers信息已从数据库中删除'% biz_msg)
        sql_select = 'select * from shijue_weixin where biz=%s'
        cursor.execute(sql_select,(biz_msg,))
        ids_tup = cursor.fetchone()
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
        company_id = ids_tup[4]
        print('开始抓取')
        crawl_url(url_home,biz,url_msg2,main_id,sub_id,company_id)


def crawl_url(url_home,biz,url_msg2,main_id,sub_id,company_id):    
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
        r = requests.post(url,data = d)
    while True:
        time.sleep(2)
        url_msg = r'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=' + biz + r'==&f=json&frommsgid='+ str(list_id[-1]) + url_msg2
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
            print(dic_msg)
            print('Please check whether the task has only one page!')
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
            r = requests.post(url,data = d)
        print(len(url_list))
        print(list_id)
        if len(list_id) < 10:
            print('The task has finished!(%s,%s,%s)'% (main_id, sub_id,company_id))
            break

if __name__ == '__main__':
    test()
