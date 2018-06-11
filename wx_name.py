#coding=utf-8
def response(flow):
    if flow.response.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=home'):
        print(flow.response.text)
