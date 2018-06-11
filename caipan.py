import requests
headers = {'Connection':'keep-alive',
           'Host':'wenshu.court.gov.cn',
           'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/3.0 Safari/536.11',
           'X-Requested-With':'XMLHttpRequest',
           'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
    }
data = {'Param':'裁判年份:2016',
        'Index':'1',
        'Page':'20',
        'Order':'法院层级',
        'Direction':'asc',
        #'number':'N8SWTT3K',
        #'vl5x':'daf4236860222f1d1e797e7a',
        #'guid':'29e3b025-a13e-700c3e81-ee271d83fb6e'
    }
url = 'http://wenshu.court.gov.cn/List/ListContent'
print(requests.post(url ,data = data ,headers=headers).text)
