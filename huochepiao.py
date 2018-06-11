import requests,json,time
import re
from urllib import request
import ssl
context = ssl._create_unverified_context()
thetime = input('请输入查询日期：')
url = r'https://kyfw.12306.cn/otn/leftTicket/queryZ?leftTicketDTO.train_date='+thetime+'&leftTicketDTO.from_station=BJP&leftTicketDTO.to_station=TEK&purpose_codes=ADULT'
req = request.Request(url)
req.add_header('Connection','keep-alive')
req.add_header('Host','kyfw.12306.cn')
req.add_header('Upgrade-Insecure-Requests','1')
req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36')

while True:
    try:
        aa = request.urlopen(req,context=context).read().decode('utf-8')
        bb = json.loads(aa)
        print(bb)
        print('网页抓取成功,开始分析是否有票')
        for each in (bb)['data']['result']:
            #if '|Z19|' in each:
            try:
                train_num = re.findall(r'\|(G\d+?)\|',each)[0]
            except:
                print('非高铁车次，跳过')
                continue
            zz_list = re.findall(r'\|\|\|\|\|\|\|\|\|\|\|(.{1,3}?)\|', each)
            if not zz_list:
                print('车票信息不符合规则')
                continue
            print(zz_list)
            if zz_list[0] != '无':
                print('时间：%s 车次：%s 有二等座车票可预订'% (thetime,train_num))
        print('暂时无票，继续监测')
        time.sleep(2)
    except:
        print('网页抓取失败，等待延时重抓！！')
        time.sleep(2)
