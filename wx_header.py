#coding=utf-8
print('aaa')
def request(flow):
    if flow.request.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=home'):
        with open('home.txt','w') as f:
            f.write(flow.request.url +"\n")
            for h in flow.request.headers :
                f.write("%s: %s\n" % (h, flow.request.headers[h] ) )
    elif flow.request.url.startswith('https://mp.weixin.qq.com/mp/profile_ext?action=getmsg'):
        with open('message.txt','w') as f:
            f.write(flow.request.url +"\n")
            for h in flow.request.headers :
                f.write("%s: %s\n" % (h, flow.request.headers[h] ) )

#def response(flow):
    #flow.response.headers["newheader"] = "foo"
    #print(flow.response.headers)
