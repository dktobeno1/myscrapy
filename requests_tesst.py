import requests
headers = {'Upgrade-Insecure-Requests':'1',
           'Host':'www.tadu.com',
           'Connection':'keep-alive',
           'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
    }
url = 'http://www.tadu.com/store/0-a-0-0-a-10-p-1'

aa = requests.get(url)
print aa.text
