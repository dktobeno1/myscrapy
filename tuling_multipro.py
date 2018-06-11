#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import time,requests,json,Queue,wx_dsb,multiprocessing,wx_dsb1
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

s = multiprocessing.Queue()
list_url = xl_list()
for i in list_url:
    s.put(i)

class MyWXBot(WXBot):
    def wx_process(self,que):
        ss = que.get()
        #self.send_msg(u'侯', ss[3])
        #self.send_msg(u'高攀', str(ss[0])+','+str(ss[1]))
        #time.sleep(70)
        log_cont = wx_dsb.crawl_url(int(ss[0]),int(ss[1]),ss[3])
        with open('crawl_logger.txt','a+') as f:
            f.write(log_cont+'\n')
        if not que.empty():
            self.wx_process(que)
            
    def wx_process1(self,que):
        ss = que.get()
        #self.send_msg(u'郑阳', ss[3])
        #self.send_msg(u'刘泽明', str(ss[0])+','+str(ss[1]))
        #time.sleep(70)
        log_cont = wx_dsb1.crawl_url(int(ss[0]),int(ss[1]),ss[3])
        with open('crawl1_logger.txt','a+') as f:
            f.write(log_cont+'\n')
        if not que.empty():
            self.wx_process1(que)      
        
    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 4 and u'宝贝老婆' in msg['user']['name']:
            p = multiprocessing.Process(target = self.wx_process,args = (s,))
            q = multiprocessing.Process(target = self.wx_process1,args = (s,))
            p.start()
            q.start()
            p.join()
            q.join()
            print u'全部完成'
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
