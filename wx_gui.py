from tkinter import *
import tkinter.messagebox as messagebox
import re,requests,json,time,os,sys,easygui

tardir = r'C:\Users\DK\Desktop\gongzhonghao'
if not os.path.isdir(tardir):
    os.mkdir(tardir)

def crawl_url(main_id,sub_id):
    with open('home.txt','r') as f:
        home_headers = f.read()
    with open('message.txt','r') as f:
        msg_headers = f.read()
    
    url_home = re.findall(r'https.+?header=1',home_headers)[0]
    User_Agent = re.findall(r'User-Agent:\s(.+?)\n',home_headers)[0]
    biz = re.findall(r'__biz=(.+?)==',url_home)[0]
    x_wechat_key = re.findall(r'x-wechat-key:\s(.+?)\n',home_headers)[0]
    x_wechat_uin = re.findall(r'x-wechat-uin:\s(.+?)\n',home_headers)[0]
    Cookie_home = re.findall(r'Cookie:\s(.+?)\n',home_headers)[0]
    Q_UA2 = re.findall(r'Q-UA2:\s(.+?)\n',home_headers)[0]
    Q_GUID = re.findall(r'Q-GUID:\s(.+?)\n',home_headers)[0]
    url_msg2 = re.findall(r'&count=10.+?json',msg_headers)[0]
    Cookie_msg = re.findall(r'Cookie:\s(.+?)\n',msg_headers)[0]

    headers_home = {'Host':'mp.weixin.qq.com',
           'Connection':'keep-alive',
           'Upgrade-Insecure-Requests':'1',
           'User-Agent':User_Agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/wxpic,image/sharpp,*/*;q=0.8',
           'Accept-Language':'zh-CN,en-US;q=0.8',
           'x-wechat-uin':x_wechat_uin,
           'x-wechat-key':x_wechat_key,
           'Cookie':Cookie_home,
            'Q-UA2':Q_UA2,
            'Q-GUID':Q_GUID,
           'Q-Auth':'31045b957cf33acf31e40be2f3e71c5217597676a9729f1b'

    }

    headers_msg = {'Host':headers_home['Host'],
           'Connection':'keep-alive',
           'X-Requested-With':'XMLHttpRequest',
           'User-Agent':headers_home['User-Agent'],
            'Accept':'*/*',
           'Referer':url_home,
            'Accept-Language':'zh-CN,en-US;q=0.8',
           'Cookie':Cookie_msg,
            'Q-UA2':headers_home['Q-UA2'],
            'Q-GUID':headers_home['Q-GUID'],
           'Q-Auth':headers_home['Q-Auth']

    }
        
    result_home = requests.get(url_home, headers = headers_home, timeout = 20)
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
    with open(r'C:\Users\DK\Desktop\gongzhonghao\%s%s.txt'% (main_id, sub_id), 'w') as f:
        for url_content in list_urlupdate:
            f.write(','.join(url_content)+',%s,%s'% (main_id, sub_id))
            f.write('\n')
        while True:
            time.sleep(4)
            url_msg = r'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=' + biz + r'==&f=json&frommsgid='+ str(list_id[-1]) + url_msg2
            result_msg = requests.get(url_msg, headers = headers_msg, timeout = 20)
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
                f.write(','.join(content_url)+',%s,%s'% (main_id, sub_id))
                f.write('\n')
            print(len(url_list))
            print(list_id)
            if len(list_id) < 10:
                print('The task has finished!(%s,%s)'% (main_id, sub_id))
                break

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.mainLabel = Label(self, text='主ID')
        self.mainLabel.pack()
        self.mainID = Entry(self)
        self.mainID.pack()
        self.subLabel = Label(self, text='子ID')
        self.subLabel.pack()
        self.subID = Entry(self)
        self.subID.pack()
        self.crawl_Button = Button(self, text='开始抓取', command=self.crawl)
        self.crawl_Button.pack()
    def crawl(self):
        mainID = self.mainID.get()
        subID = self.subID.get()
        crawl_url(mainID,subID)
        messagebox.showinfo('alert','The task has finished!(%s,%s)'% (mainID, subID))
if __name__ == '__main__':
    app = Application()
    app.master.title('公众号GUI')
    app.mainloop()
