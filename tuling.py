#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import time,requests,json,Queue,wx_dsb
import xlrd

def xl_list():
    data = xlrd.open_workbook('C:\Users\DK\Desktop\weixin.xlsx')
    table = data.sheets()[0] 
    nrows = table.nrows
    data=[]
    for i in range(nrows):
        data.append(tuple(table.row_values(i)))
    #print len(data)
    return data

class MyWXBot(WXBot):
    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 4 and u'刘泽明' in msg['user']['name']:
            s = Queue.Queue(100)
            list_url = xl_list()
            #print list_url
            for i in list_url[1:]:
                s.put(i)
            list1 = [u'刘泽明', u'高攀']
            while True:
                for each in list1:
                    if s.empty():
                        break
                    ss = s.get()
                    print ss
                    self.send_msg(each, ss[3])
                    time.sleep(50)
                    wx_dsb.crawl_url(int(ss[0]),int(ss[1]))
                if s.empty():
                    break
            print 'ok'
'''
    def schedule(self):
        self.send_msg(u'张三', u'测试')
        time.sleep(1)
'''


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.run()


if __name__ == '__main__':
    main()
