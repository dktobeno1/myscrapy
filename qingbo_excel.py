from http import cookiejar
from urllib import request,parse
from bs4 import BeautifulSoup
import json
import xlwt
#from urllib import request

wbk = xlwt.Workbook()
sheet = wbk.add_sheet('微信榜单')

types_list = ['all','政务','时事','文化','生活','健康','美食','时尚','旅行','母婴','科技','创业','职场','娱乐','搞笑','动漫','游戏','体育','汽车','金融','房产','教育','民生','企业','其他']

cookie = cookiejar.MozillaCookieJar()
handler = request.HTTPCookieProcessor(cookie)
opener = request.build_opener(handler)
def log_in():
    login_url = 'http://www.gsdata.cn/member/login'
    headers = {'Connection':'keep-alive',
               'Host':'www.gsdata.cn',
               'Referer':'http://www.gsdata.cn/member/login',
               'Upgrade-Insecure-Requests':'1',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
        }

    data = {'username':'15321366639',
            'password':'qingyuan'
        }

    login_req = request.Request(login_url,parse.urlencode(data).encode('utf-8'),headers)
    login_resp = opener.open(login_req).read().decode('utf-8')
#print(login_resp)
def crawl_data(types,types_num):
    global sheet
    for page in range(1,5):
        aa_url = 'http://www.gsdata.cn/rank/ajax_wxrank?type=day&post_time=2017-10-29&page='+str(page)+'&types='+types+'&industry=all&proName=&dataType=json'
        headers = {'Connection':'keep-alive',
                   'Host':'www.gsdata.cn',
                   'Referer':'http://www.gsdata.cn/rank/wxrank',
                   'X-Requested-With':'XMLHttpRequest',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
            }
        aa_req = request.Request(aa_url,None,headers)
        aa_resp = opener.open(aa_req).read().decode('utf-8')
        #print(aa_resp)
        aa_soup = BeautifulSoup(json.loads(aa_resp)['data'], "html.parser")
        #print(aa_soup.prettify())
        #print(len(aa_soup.select('tr')))
        for i in aa_soup.select('tr'):
            #print(aa_soup.index(i))
            des_list = [each for each in i.get_text().split('\n') if each]
            print(des_list[0],des_list[1])
            for a in range(9):
                #print(int((aa_soup.index(i)-1)/2))
                sheet.write(int((aa_soup.index(i)-1)/2)+25*(page-1)+100*types_num,a,des_list[a])

if __name__ == '__main__':
    log_in()
    for each in types_list:
        url_str = request.quote(each)
        print(each)
        crawl_data(url_str,types_list.index(each))
        print(each,'抓取并导入EXCEL完成')
    wbk.save('test.xls')

