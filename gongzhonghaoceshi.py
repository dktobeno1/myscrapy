import requests,re
url = 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzIwNzEwOTM2MA==&scene=123&uin=ODUxOTA1Mjgw&key=387780be819178878f8b0dd26aeb18f86b97eb64277f38eb29583d5dfa2fbad29ca86ff4eae7de28e1444ce8dff6a8e70e5f68938c9546cdb96bd4390c068d2e2001b5fe2e41c216498b3&devicetype=android-24&version=26051036&lang=zh_CN&nettype=WIFI&a8scene=1&pass_ticket=m2liSlu6rgmeise%2FKCRPEYE6eygzzeH5nK99JUATjLFI8p5sQEd34zFeNJLZs95Y&wx_header=1'
headers = {'Host':'mp.weixin.qq.com',
           'Connection':'keep-alive',
           'Upgrade-Insecure-Requests':'1',
           'User-Agent':'Mozilla/5.0 (Linux; Android 7.0; VTR-AL00 Build/HUAWEIVTR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043613 Safari/537.36 MicroMessenger/6.5.16.1120 NetType/WIFI Language/zh_CN',
           'x-wechat-uin':'NTI2Nzg0OTYw',
           'x-wechat-key':'ece301ae679d4d02dcd9e170952b2467eb002b9f6e277e0c31a9e678d39c396f577666a02e9fc76cfc57c72deb8a90e0e3f450aa353f4f84da855b5b9c216890b3af96a4161115c36d915c38946e4267',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/wxpic,image/sharpp,*/*;q=0.8',
           'Accept-Encoding':'gzip, deflate',
           'Accept-Language':'zh-CN,en-US;q=0.8',
           'Cookie':'wxtokenkey=3e80a1eba2529ef2c56d463ef371e63c690fa04ab72b72959b41085627effc2b; wxuin=526784960; pass_ticket=m2liSlu6rgmeise/KCRPEYE6eygzzeH5nK99JUATjLFI8p5sQEd34zFeNJLZs95Y; wap_sid2=CMCzmPsBElxFa0w0TE53OWdqSGhZMmpPa1RVeERHLXRFdjY0N2xXeU5HWXA2VGJFVkpXdXFhYy1yM0JqM1I2YjNldjhXdnNzQk5xaExWZUd5c2JDdkN3Ym55WHpVS0lEQUFBfjCZk4/QBTgMQJRO',
           'Q-UA2':'QV=3&PL=ADR&PR=WX&PP=com.tencent.mm&PPVN=6.5.16&TBSVC=43601&CO=BK&COVC=043613&PB=GE&VE=GA&DE=PHONE&CHID=0&LCID=9422&MO= VTR-AL00 &RL=1080*1920&OS=7.0&API=24',
           'Q-GUID':'9953f6e774b674572860d05713b788cb',
           'Q-Auth':'31045b957cf33acf31e40be2f3e71c5217597676a9729f1b'
           
    }
aa = requests.get(url,headers=headers,timeout=20).text
print(aa)
nickname = re.findall(r'var nickname = "([\s\S]+?)"',aa)[0]
print(nickname)
