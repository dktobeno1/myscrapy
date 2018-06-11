import redis
r = redis.Redis(host = '116.62.237.239',port = 6379)
r.set('name','aaa')
print(r.get('name'))
