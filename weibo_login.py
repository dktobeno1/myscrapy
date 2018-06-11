#-*- encoding:utf-8 -*-

import base64
import requests
import re,json
import rsa
import binascii

def Get_cookies():
    '''登陆新浪微博，获取登陆后的Cookie，返回到变量cookies中'''
    username = input(u'请输入用户名：')
    password = input(u'请输入密码：')

    url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&su=%s&rsakt=mod&client=ssologin.js(v1.4.19)'+username
    html_dic = json.loads(requests.get(url).text)

    servertime = html_dic['servertime']
    nonce = html_dic['nonce']
    pubkey = html_dic['pubkey']
    rsakv = html_dic['rsakv']

    username = base64.b64encode(username.encode('utf-8')) #加密用户名
    rsaPublickey = int(pubkey, 16)
    key = rsa.PublicKey(rsaPublickey, 65537) #创建公钥
    print(type(key))
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password) #拼接明文js加密文件中得到
    passwd = rsa.encrypt(message.encode('utf-8'), key) #加密
    passwd = binascii.b2a_hex(passwd) #将加密信息转换为16进制。

    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
    data = {'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'qrcode_flag':'false',
        'userticket': '1',
        'pagerefer':'https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D%252F',
        #'ssosimplelogin': '1',
        'vsnf': '1',
        #'vsnval': '',
        'su': username,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv' : rsakv,
        'sp': passwd,
        'encoding': 'UTF-8',
        'prelt': '518',
        'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
        }
    headers = {'Host':'login.sina.com.cn',
               'Connection':'keep-alive',
               'Upgrade-Insecure-Requests':'1',
               'Origin':'https://weibo.com',
               'Referer':'https://weibo.com/',
               'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        }
    resp = requests.post(login_url,data=data,headers=headers)
    print(resp.content.decode('gbk'))
    print(resp.headers)
    #urlnew = re.findall('location.replace\(\'(.*?)\'',html,re.S)[0]

    #发送get请求并保存cookies
    #cookies = requests.get(urlnew).cookies
    #return cookies


if __name__ == '__main__':
    Get_cookies()
