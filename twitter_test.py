import tweepy,time
from tweepy import OAuthHandler
import re,json,requests,base64
CONSUMER_KEY = 'uZmS8bAmivADbAGNeR4Q35ZNv'
CONSUMER_SECRET = 'EYespkUBbFt8v86eK3mAwyy8y6PB7ln62mpDjpRQb1nEhySbf2'
access_token = '912678153100845056-UhdhJySK2PXtEPc26VbZ7y822WZVOMX'
access_secret = '5MJx20CgtZ0Kszs0rOyScT4xiZIlIRkm2SEe5l8ILXpFJ'

highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')

def mk_bs64(img_url):
    img_str = requests.get(img_url,timeout=5).content
    img_bs64 = base64.b64encode(img_str)
    return img_bs64

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)
#print(type(tweepy.Cursor(api.home_timeline)))
#for status in tweepy.Cursor(api.home_timeline).items(1):
    #text_noem = highpoints.sub('--emoji--', status.text)
    #print(text_noem)
    #print(status._json)
#print(type(api.search('US')))
for status in api.search('中国 人大'):
     #text_noem = highpoints.sub('--emoji--', status.text)
     #print(text_noem)
     #print('--'*20)
     sta_dict = status._json
     print(sta_dict)
     data = {}
     data['_id'] = sta_dict['id_str']
     data['text'] = sta_dict['text']
     #print(sta_dict['created_at'])
     aa = sta_dict['created_at'].split(' ')
     aa.pop(4)
     #print(aa)
     data['status'] = 0
     data['ctime'] = time.mktime(time.strptime(' '.join(aa), "%a %b %d %H:%M:%S %Y"))
     data['source'] = sta_dict['source']
     data['retweets_count'] = sta_dict['retweet_count']
     data['comments_count'] = 0
     data['attitudes_count'] = sta_dict['favorite_count']
     data['url'] = 'https://twitter.com/' + sta_dict['user']['screen_name'] + '/status/' + sta_dict['id_str']
     data['addtime'] = time.time()
     if sta_dict.get('extended_entities'):
         data['media_url'] = sta_dict['extended_entities']['media'][0]['media_url']
         data['media_url_dow'] = mk_bs64(data['media_url'])
     if sta_dict.get('retweeted_status'):
         data['retweeted_id'] = sta_dict['retweeted_status']['id']
         data['retweeted_uid'] = sta_dict['retweeted_status']['user']['id']
         data['retweeted_name'] = sta_dict['retweeted_status']['user']['name']
     else:
         data['retweeted_id'] = ''
         data['retweeted_uid'] = ''
         data['retweeted_name'] = ''
     data['user'] = {}
     data['user']['id'] = sta_dict['user']['id']
     data['user']['name'] = sta_dict['user']['name']
     data['user']['screen_name'] = sta_dict['user']['screen_name']
     data['user']['followers_count'] = sta_dict['user']['followers_count']
     data['user']['friends_count'] = sta_dict['user']['friends_count']
     data['user']['statuses_count'] = sta_dict['user']['statuses_count']
     data['user']['description'] = sta_dict['user']['description']
     data['user']['profile_url'] = 'https://twitter.com/' + sta_dict['user']['screen_name']
     data['user']['header_url'] = sta_dict['user']['profile_image_url_https']
     data['user']['header_url_dow'] = mk_bs64(data['user']['header_url'])
     try:
         if sta_dict['user']['entities']['url']['urls']:
             data['user']['expanded_url'] = sta_dict['user']['entities']['url']['urls'][0]['expanded_url']
     except:
         print('no urls')
     #print(sta_dict['user'])
     print(data)
     break

#help(tweepy.API)



