from tkinter import *
from bo_lib.general.mongodb_helper import MongoDBHelper

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.var = Variable()
        self.show_tvids = IntVar()
        self.pack()
        self.createWidgets()
        self.client = MongoDBHelper()
        self.url_title = []
        self.comment_ts = []
        self.albumid_tvid = []
        self.album_info = []
        self.play_num = []
        self.video_ts = []
        self.video_url_info = self.client.get_collection(collection_name='video_url_list', database_name='Aiqiyi')
        self.comment_info = self.client.get_collection(collection_name='comment_info', database_name='Aiqiyi')
        self.albumid_tvid_coll = self.client.get_collection(collection_name='albumid_tvid', database_name='Aiqiyi')
        self.video_info_coll = self.client.get_collection(collection_name='video_info_dup', database_name='Aiqiyi')
        self.album_info_coll = self.client.get_collection(collection_name='album_info', database_name='Aiqiyi')
        self.play_info = self.client.get_collection(collection_name='play_info', database_name='Aiqiyi')
        self.coll_list = [(self.video_url_info, 'video_url_list'),
                          (self.comment_info, 'comment_info'),
                          (self.albumid_tvid_coll, 'albumid_tvid'),
                          (self.video_info_coll, 'video_info'),
                          (self.album_info_coll, 'album_info'),
                          (self.play_info, 'play_info')]

    def createWidgets(self):
        self.mainLabel = Label(self, text='albumId', )
        self.mainLabel.pack()
        self.albumId = Entry(self)
        self.albumId.pack()
        self.subLabel = Label(self, text='tvId')
        self.subLabel.pack()
        self.tvId = Entry(self)
        self.tvId.pack()
        self.r1 = Radiobutton(self, text="show tvids", variable=self.show_tvids, value=1)
        self.r1.pack()
        self.r2 = Radiobutton(self, text="no tvids", variable=self.show_tvids, value=0)
        self.r2.pack()
        self.crawl_Button = Button(self, text='查询', command=self.select_mongo)
        self.crawl_Button.pack()
        self.resultLabel = Label(self, text='查询结果')
        self.resultLabel.pack()
        self.mss = Message(self, textvariable=self.var)
        self.mss.pack()

    def select_mongo(self):
        albumId = self.albumId.get()
        tvId = self.tvId.get()
        self.select_execute(albumId, tvId)

        #messagebox.showinfo('result', self.make_info())

    def select_url_info(self, item):
        video_conf_l = ['video_self', 'video_db', 'video_vip', 'video_paid', 'video_voucher']
        item_tup_l = []
        item_tup_l.append(item['url'])
        item_tup_l.append(item['title'])
        item_tup_l.append(item['update_time_string'])
        for video_conf in video_conf_l:
            if int(item[video_conf]) == 1:
                item_tup_l.append(video_conf)
            elif int(item[video_conf]) == -1:
                item_tup_l.append('未获取vip等信息')
                item_tup = tuple(item_tup_l)
                return item_tup
        item_tup = tuple(item_tup_l)
        return item_tup

    def select_aubum_info(self, item):
        album_info = item['album_info']
        if isinstance(album_info, dict):
            result = tuple([d['name'] for d in album_info['categories']])
        else:
            result = album_info
        return result

    def select_execute(self, albumId, tvId):
        if albumId:
            if not tvId:
                for coll in self.coll_list:
                    if coll[1] == 'video_url_list':
                        self.url_title = [self.select_url_info(item) for item in
                                          coll[0].find({'albumId': str(albumId).strip()})]
                    elif coll[1] == 'albumid_tvid':
                        self.albumid_tvid = [item.get('tvids', 'no_tvid') for item in
                                          coll[0].find({'albumId': str(albumId).strip()})]
                    elif coll[1] == 'album_info':
                        self.album_info = [self.select_aubum_info(item) for item in
                                          coll[0].find({'albumId': str(albumId).strip()})] #select_aubum_info(item) if coll[0].find({'albumId': str(albumId).strip()}).count() else '查不到数据'
                    elif coll[1] == 'play_info':
                        self.play_num = [(item['play_num'], item['ts_string']) for item in
                                           coll[0].find({'albumid': str(albumId).strip()})]
                self.var.set(self.make_info(albumid=True))
            else:
                self.var.set('albumId与tvId不能同时查询，请重新输入')
        else:
            if tvId:
                for coll in self.coll_list:
                    if coll[1] == 'comment_info':
                        self.comment_ts = [(item['comment_info']['count'], item['ts_string']) for item in
                                           coll[0].find({'tvid': int(str(tvId).strip())})]
                        if not self.comment_ts:
                            self.comment_ts = [(item['comment_info']['count'], item['ts_string']) for item in
                                               coll[0].find({'tvid': str(tvId).strip()})]
                    elif coll[1] == 'video_info':
                        self.video_ts = [(item['video_info']['name'] if item['video_info'].get('name') else item['video_info'].get('videoName'),
                                          item['duration'], item['publishTime'], item['ts_string']) for item in
                                           coll[0].find({'tvid': int(str(tvId).strip())})]
                self.var.set(self.make_info(tvid=True))
            else:
                self.var.set('请输入您要查询的albumId或tvId')

    def make_info(self, albumid=False, tvid=False):
        if albumid:
            url_title = '\n'.join([str(t) for t in self.url_title]) if self.url_title else '查不到数据'
            #comment_ts = '\n'.join([str(t) for t in self.comment_ts]) if self.url_title else '无数据'
            if self.albumid_tvid:
                if isinstance(self.albumid_tvid[0], list):
                    tvids = '\n'.join([str(t) for t in self.albumid_tvid[0]])
                    tvid_num = len(self.albumid_tvid[0])
                else:
                    tvids = 0
                    tvid_num = 0
            else:
                tvids = '查不到数据'
                tvid_num = '查不到数据'

            album_info = '\n'.join([str(t) for t in self.album_info]) if self.album_info else '查不到数据'
            play_num = '\n'.join([str(t) for t in self.play_num]) if self.play_num else '查不到数据'
            if not self.show_tvids.get():
                result = 'albumId:{}\nvideo_url_list:\n{}\ntv_num:{}\nalbum_info:\n{}\nplay_num:\n{}'.\
                    format(self.albumId.get(), url_title, tvid_num, album_info, play_num)
                return result
            else:
                result = 'albumId:{}\nvideo_url_list:\n{}\ntv_num:{}\nalbum_info:\n{}\nplay_num:\n{}\ntvids:\n{}'. \
                    format(self.albumId.get(), url_title, tvid_num, album_info, play_num, tvids)
                return result
        elif tvid:
            comment_ts = '\n'.join([str(t) for t in self.comment_ts]) if self.comment_ts else '查不到数据'
            video_ts = '\n'.join([str(t) for t in self.video_ts]) if self.video_ts else '查不到数据'
            result = 'tvId:{}\nvideo_info:\n{}\ncomment_info:\n{}'. \
                format(self.tvId.get(), video_ts, comment_ts)
            return result
        else:
            return('代码逻辑有误，请检查！！！')

if __name__ == '__main__':
    app = Application()
    app.master.title('爱奇艺数据查询')
    app.master.geometry('1000x2000')
    app.mainloop()
