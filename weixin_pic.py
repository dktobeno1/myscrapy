import re,requests,json,time,os,sys,easygui
#pass_ticket = '2UyijGulNJQjbCcllN9JOUmyI8p8gCd5vx3i2AHSgvKBVkjHgL3A1hnXCUVOOLeE'
#renwu = '21175'
main_id = sys.argv[1]
#main_id = 1
sub_id = sys.argv[2]
company_id = sys.argv[3]
#sub_id = 1
with open('home.txt','r') as f:
    home_headers = f.read()
with open('message.txt','r') as f:
    msg_headers = f.read()
    
url_home = re.findall(r'https.+?header=1',home_headers)[0]
#url_home = 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzIyNTU2ODgzMA==&scene=123&uin=ODUxOTA1Mjgw&key=d6901a04ff0e16e8417abab8643ba0f30f1543ac02b44105340098187d6ae355ec7e37a139806f32c08761c5883e4317bb12b5dd2c282863acf78de747e0f69c3b9bf949c67d7b4775e54'
User_Agent = re.findall(r'User-Agent:\s(.+?)\n',home_headers)[0]
biz = re.findall(r'__biz=(.+?)==',url_home)[0]
#biz = 'MzIyNTU2ODgzMA'
x_wechat_key = re.findall(r'x-wechat-key:\s(.+?)\n',home_headers)[0]
x_wechat_uin = re.findall(r'x-wechat-uin:\s(.+?)\n',home_headers)[0]
Cookie_home = re.findall(r'Cookie:\s(.+?)\n',home_headers)[0]
#Q_UA2 = re.findall(r'Q-UA2:\s(.+?)\n',home_headers)[0]
#Q_GUID = re.findall(r'Q-GUID:\s(.+?)\n',home_headers)[0]
url_msg2 = re.findall(r'&count=10.+?json',msg_headers)[0]
#url_msg2 = '&count=10&is_ok=1&scene=123&uin=MTQ4NzI5MTcwMw%3D%3D&key='+'909c3adce6ce91458b258a905e50c72aa7463e64568269d11c16ab8d39cade13d13accc68abeec17cdcca13f21329c05e165e82d0e3009577ec99d4aefba5e38ebdd30aa057595b832cfb'+'&pass_ticket=38M9KnGHOZh216Qf3EbOAodxKDnirrv7iUf2tOWPF9emloKK1W%2FMa%2FmTPe1Uj7Y9&wxtoken=&appmsg_token=927_jYg8Dg03PgYE2Q94oVHeq-wmd0DhyToVxxXjZA~~&x5=1&f=json'
Cookie_msg = re.findall(r'Cookie:\s(.+?)\n',msg_headers)[0]


def get_header():
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
    headear_list = [headers_home, headers_msg]
    return headear_list

def crawl_url():    
    result_home = requests.get(url_home, headers = get_header()[0], timeout = 20)
    #print(result_home.text)
    pattern_url = re.compile(r'content_url&quot;:&quot;(http:.+?wechat_redirect).+?cover&quot;:&quot;(http:.+?)&quot;')
    #pattern_pic = re.compile(r'cover&quot;:&quot;(http:.+?wx_fmt=jpeg)')
    pattern_id = re.compile(r'&quot;id&quot;:(.+?),')
    list_url = re.findall(pattern_url, result_home.text)
    #print(list_url)
    #list_pic = re.findall(pattern_pic, result_home.text)
    list_id = re.findall(pattern_id, result_home.text)
    list_urlupdate = []
    for each in list_url:
        each_new = []
        for i in each:            
            each_new.append(i.replace(r'\\/',r'/').replace(r'amp;',''))
        list_urlupdate.append(each_new)
    #print(list_urlupdate)
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
        #print r.text
    while True:
        time.sleep(2)
        url_msg = r'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=' + biz + r'==&f=json&frommsgid='+ str(list_id[-1]) + url_msg2
        result_msg = requests.get(url_msg, headers = get_header()[1], timeout = 20)
        #print(result.text)
        dic_msg = json.loads(result_msg.text)
        url_list = []
        list_id = []
            
        #if type(json.loads(dic_msg['general_msg_list'])['list']) == type()
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
            #print(url_list)
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
            #print r.text
        print(len(url_list))
        print(list_id)
        if len(list_id) < 10:
            print('The task has finished!(%s,%s)'% (main_id, sub_id))
            break

if __name__ == '__main__':
    crawl_url()
    easygui.msgbox('Task has finished!')
