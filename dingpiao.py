# coding: utf-8
from PIL import Image
from pylab import *
from http import cookiejar
from urllib import request,parse
import ssl,time,re,json
ssl._create_default_https_context = ssl._create_unverified_context
cookie=cookiejar.MozillaCookieJar()
handler=request.HTTPCookieProcessor(cookie)
opener=request.build_opener(handler)
#home_url = 'https://kyfw.12306.cn/otn/leftTicket/init'
#home_url_html = opener.open(home_url).read().decode('utf-8')
#print(home_url_html)
#dingpiao_url = 'https://kyfw.12306.cn/otn/leftTicket/queryX?leftTicketDTO.train_date=2017-10-18&leftTicketDTO.from_station=XAY&leftTicketDTO.to_station=BXP&purpose_codes=ADULT'
#headers_dingpiao = {'Connection':'keep-alive',
                   # 'Host':'kyfw.12306.cn',
                    #'Upgrade-Insecure-Requests':'1',
                    #'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
   # }
#req_dp = request.Request(dingpiao_url,None,headers_dingpiao)
#print(request.urlopen(req_dp).read().decode('utf-8'))
#while True:
#    try:
#        cc = json.loads(request.urlopen(req_dp).read().decode('utf-8'))
#        print('网页抓取成功')
#        for each in cc['data']['result']:
#            if '|G656|' in each:
 #               bb = request.unquote(re.findall(r'(.+?)\|预订',each)[0])#url解码
  #              print(bb)
   #     break
    #except:
     #   print('网页抓取失败，等待延时重抓！！')
      #  time.sleep(2)


pic_url = 'http://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand'
#req_pic = request.Request(pic_url)
#request.urlretrieve(pic_url,r'captcha-image.jpg')
aa = opener.open(pic_url).read()
with open('captcha-image.jpg','wb') as f:
    f.write(aa)
#time.sleep(3)
im = array(Image.open('captcha-image.jpg')) 
imshow(im)
x =ginput(1)
count = input('请输入符合要求的图片数：')
imshow(im)
x =ginput(int(count))
x_list = []
for each in x:
    each_list = list(each)
    each_list[0] = str(int(each_list[0]))
    each_list[1] = str(int((each_list[1]-40)*15/16))
    #print(each_list)
    x_list += each_list
    #print(x_list)
x_str = ','.join(x_list)
print(x_str)
cap_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
data = {'answer':x_str,
        'login_site':'E',
        'rand':'sjrand'
    }
headers = {'Connection':'keep-alive',
           'Host':'kyfw.12306.cn',
           'Origin':'https://kyfw.12306.cn',
           'Referer':'https://kyfw.12306.cn/otn/leftTicket/init',
           'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
           'X-Requested-With':'XMLHttpRequest'
               }

cap_req = request.Request(cap_url,parse.urlencode(data).encode('utf-8'),headers)
cap_res = opener.open(cap_req).read().decode('utf-8')
print('cap_res>>>>>>',cap_res)
login_url = 'https://kyfw.12306.cn/passport/web/logi' \
            'n'
data_login = {'username':'ruyeweiliang',
              'password':'123dds123',
              'appid':'otn',
              '_json_att':''
    }
login_req = request.Request(login_url,parse.urlencode(data_login).encode('utf-8'),headers)
login_res = opener.open(login_req).read().decode('utf-8')
print('login_res>>>>>>',login_res)
uamtk_url = 'https://kyfw.12306.cn/passport/web/auth/uamtk?callback=jQuery19106315542983567741_1504598628086'
data_uamtk = {'appid':'otn',
              '_json_att':''
    }
uamtk_req = request.Request(uamtk_url,parse.urlencode(data_uamtk).encode('utf-8'),headers)
uamtk_res = opener.open(uamtk_req).read().decode('utf-8')
json_uamtk = re.findall(r'\((.+?)\)',uamtk_res)[0]
print('json_uamtk>>>>>>',json_uamtk)                     
newapptk = json.loads(json_uamtk)['newapptk']
print('newapptk>>>>>>',newapptk)
uama_url = 'https://kyfw.12306.cn/otn/uamauthclient'
data_uama = {'tk':newapptk,
              '_json_att':''
    }
uama_req = request.Request(uama_url,parse.urlencode(data_uama).encode('utf-8'),headers)
uama_res = opener.open(uama_req).read().decode('utf-8')
print('uama_res>>>>>>',uama_res)


submit_url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
submit_data = {'secretStr':request.unquote('vVqey3Gq6MI%2FtigXByCPnFDU9DhXm51eAN12g0V67rcESnrAmWuMn%2F9qpDKjtEZF%2BrdKf06dRXpy%0Aaj6sBe2YLJENAPYo1uBYI1y%2BMlKYIeAeHNRAKUKbkLhfvOlzhdFm48dQ0XYRGn7NGRNaCuHXBpHL%0AegXQgE%2BNIP4n7y0wdj66yTB1N37eAPfwYdIO7%2Ba3YjnBD%2BVepVQUTcWUmfnafx3tFx2Eh4%2BWAjwe%0Ar%2BJH2qhLP15gKnfGGQ%3D%3D'),
               'train_date':'2018-02-13',
               'back_train_date':'2017-09-19',
               'tour_flag':'dc',
               'purpose_codes':'ADULT',
               'query_from_station_name':'北京',
               'query_to_station_name':'滕州',
               'undefined':''
    }
req_sub = request.Request(submit_url,parse.urlencode(submit_data).encode('utf-8'),headers)
sub_res = opener.open(req_sub).read().decode('utf-8')
print('sub_res>>>>>>',sub_res)

init_url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
data_init = {'_json_att':''
    }
init_headers = {'Connection':'keep-alive',
           'Host':'kyfw.12306.cn',
           'Origin':'https://kyfw.12306.cn',
           'Referer':'https://kyfw.12306.cn/otn/leftTicket/init',
           'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
           'Upgrade-Insecure-Requests':'1'
               }
init_req = request.Request(init_url,parse.urlencode(data_init).encode('utf-8'),init_headers)
init_res = opener.open(init_req).read().decode('utf-8')
#print(init_res)
REPEAT_SUBMIT_TOKEN = re.findall(r"globalRepeatSubmitToken\s=\s'(.+?)';",init_res)[0]
print('REPEAT_SUBMIT_TOKEN>>>>>>',REPEAT_SUBMIT_TOKEN)
key_check_isChange = re.findall(r"'key_check_isChange':'(.+?)'",init_res)[0]
print('key_check_isChange>>>>>>',key_check_isChange)
leftTicketStr = re.findall(r"'leftTicketStr':'(.+?)'",init_res)[0]
print('leftTicketStr>>>>>>',leftTicketStr)

checkorder_url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
checkorder_data = {'cancel_flag':'2',
             'bed_level_order_num':'000000000000000000000000000000',
             'passengerTicketStr':'3,0,1,杜康,1,370481199312054353,15683053437,N',
             'oldPassengerStr':'杜康,1,370481199312054353,1_',
             'tour_flag':'dc',
             'randCode':'',
             '_json_att':'',
             'REPEAT_SUBMIT_TOKEN':REPEAT_SUBMIT_TOKEN
    }
checkorder_headers = {'Connection':'keep-alive',
           'Host':'kyfw.12306.cn',
           'Origin':'https://kyfw.12306.cn',
           'Referer':'https://kyfw.12306.cn/otn/confirmPassenger/initDc',
           'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
           'X-Requested-With':'XMLHttpRequest'
               }
checkorder_req = request.Request(checkorder_url,parse.urlencode(checkorder_data).encode('utf-8'),checkorder_headers)
checkorder_res = opener.open(checkorder_req).read().decode('utf-8')
print('checkorder_res>>>>>>',checkorder_res)

getqueue_url = 'https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'
getqueue_data = {'train_date':'Sat Oct 14 2017 00:00:00 GMT+0800 (中国标准时间)',
             'train_no':'880000Z15202',
             'stationTrainCode':'Z152',
             'seatType':'3',
             'fromStationTelecode':'XAY',
             'toStationTelecode':'BXP',
             'leftTicket':leftTicketStr,
             'purpose_codes':'00',
                'train_location':'01',
                '_json_att':'',
                'REPEAT_SUBMIT_TOKEN':REPEAT_SUBMIT_TOKEN
    }
getqueue_req = request.Request(getqueue_url,parse.urlencode(getqueue_data).encode('utf-8'),checkorder_headers)
getqueue_res = opener.open(getqueue_req).read().decode('utf-8')
print('getqueue_res>>>>>>',getqueue_res)


confirm_url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
confirm_data = {'passengerTicketStr':'3,0,1,杜康,1,370481199312054353,15683053437,N',
             'oldPassengerStr':'杜康,1,370481199312054353,1_',
             'randCode':'',
             'purpose_codes':'00',
             'key_check_isChange':key_check_isChange,
             'leftTicketStr':leftTicketStr,
             'train_location':'01',
             'choose_seats':'',
                'seatDetailType':'000',
                'roomType':'00',
                'dwAll':'N',
                '_json_att':'',
                'REPEAT_SUBMIT_TOKEN':REPEAT_SUBMIT_TOKEN
    }
confirm_req = request.Request(confirm_url,parse.urlencode(confirm_data).encode('utf-8'),checkorder_headers)
confirm_res = opener.open(confirm_req).read().decode('utf-8')
print('confirm_res>>>>>>',confirm_res)

queryorder_url = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random=1505797698091&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN='+REPEAT_SUBMIT_TOKEN
queryorder_req = request.Request(queryorder_url,None,checkorder_headers)
queryorder_res = opener.open(queryorder_req).read().decode('utf-8')
print('queryorder_res>>>>>>',queryorder_res)
orderSequence_no = json.loads(queryorder_res)['data']['orderId']
print('orderSequence_no>>>>>>',orderSequence_no)
queryorder_url_1 = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random=1505797699112&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN='+REPEAT_SUBMIT_TOKEN
queryorder_req_1 = request.Request(queryorder_url_1,None,checkorder_headers)
queryorder_res_1 = opener.open(queryorder_req_1).read().decode('utf-8')
print('queryorder_res_1>>>>>>',queryorder_res_1)
queryorder_url_2 = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random=1505797700112&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN='+REPEAT_SUBMIT_TOKEN
queryorder_req_2 = request.Request(queryorder_url_2,None,checkorder_headers)
queryorder_res_2 = opener.open(queryorder_req_2).read().decode('utf-8')
print('queryorder_res_1>>>>>>',queryorder_res_2)

resultOrder_url = 'https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue'
resultOrder_data = {'orderSequence_no':orderSequence_no,
                    '_json_att':'',
                    'REPEAT_SUBMIT_TOKEN':REPEAT_SUBMIT_TOKEN
    }
resultOrder_req = request.Request(resultOrder_url,parse.urlencode(resultOrder_data).encode('utf-8'),checkorder_headers)
resultOrder_res = opener.open(resultOrder_req).read().decode('utf-8')
print('resultOrder_res>>>>>>',resultOrder_res)




