#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-07 17:05:11


import itertools
import json
import logging
import os
import time
from collections import deque

from six import iteritems, itervalues
from six.moves import queue as Queue

from pyspider.libs import counter, utils
from pyspider.libs.base_handler import BaseHandler
from .task_queue import TaskQueue

logger = logging.getLogger('scheduler')


class Project(object):
    '''
    project for scheduler
    '''
    def __init__(self, scheduler, project_info):
        '''
        '''
        self.scheduler = scheduler

        self.active_tasks = deque(maxlen=scheduler.ACTIVE_TASKS)
        self.task_queue = TaskQueue()#创建一个任务队列实例，该任务队列可以用于优先级队列和时间队列
        self.task_loaded = False
        self._selected_tasks = False  # selected tasks after recent pause
        self._send_finished_event_wait = 0  # wait for scheduler.FAIL_PAUSE_NUM loop steps before sending the event

        self.md5sum = None
        self._send_on_get_info = False
        self.waiting_get_info = True

        self._paused = False #项目暂停状态，false为正常运行状态，true为暂停状态
        self._paused_time = 0
        self._unpause_last_seen = None

        self.update(project_info)

    @property
    def paused(self):
        #暂停失败阈值为0时返回false，应该是无论怎样都说不做暂停
        if self.scheduler.FAIL_PAUSE_NUM <= 0:
            return False

        # unpaused --(last FAIL_PAUSE_NUM task failed)--> paused --(PAUSE_TIME)--> unpause_checking
        #                         unpaused <--(last UNPAUSE_CHECK_NUM task have success)--|
        #                             paused <--(last UNPAUSE_CHECK_NUM task no success)--|
        #当项目正常运行时，做失败任务计数
        if not self._paused:
            fail_cnt = 0
            for _, task in self.active_tasks:
                # ignore select task
                #忽略被选任务
                if task.get('type') == self.scheduler.TASK_PACK:
                    continue
                if 'process' not in task['track']:
                    logger.error('process not in task, %r', task)
                if task['track']['process']['ok']:
                    break
                else:
                    fail_cnt += 1
                if fail_cnt >= self.scheduler.FAIL_PAUSE_NUM:
                    break
            if fail_cnt >= self.scheduler.FAIL_PAUSE_NUM:#失败任务数大于阈值时暂停项目
                self._paused = True
                self._paused_time = time.time()
        elif self._paused is True and (self._paused_time + self.scheduler.PAUSE_TIME < time.time()):#暂停时长已过，状态改为checking
            self._paused = 'checking'
            self._unpause_last_seen = self.active_tasks[0][1] if len(self.active_tasks) else None
        #如果状态为checking，做活动任务和失败任务计数
        elif self._paused == 'checking':
            cnt = 0
            fail_cnt = 0
            for _, task in self.active_tasks:
                if task is self._unpause_last_seen:
                    break
                # ignore select task
                if task.get('type') == self.scheduler.TASK_PACK:
                    continue
                cnt += 1
                if task['track']['process']['ok']:
                    # break with enough check cnt
                    #当遇到一个成功的活动任务时，人为的确保cnt不小于self.scheduler.UNPAUSE_CHECK_NUM，然后break
                    cnt = max(cnt, self.scheduler.UNPAUSE_CHECK_NUM)
                    break
                else:
                    fail_cnt += 1
            if cnt >= self.scheduler.UNPAUSE_CHECK_NUM:
                #如果活动任务全部是失败，则需要再次暂停
                if fail_cnt == cnt:
                    self._paused = True
                    self._paused_time = time.time()
                else:
                    self._paused = False

        return self._paused is True

    #根据项目信息更新项目
    def update(self, project_info):
        self.project_info = project_info

        self.name = project_info['name']#项目名
        self.group = project_info['group']#项目组名
        self.db_status = project_info['status']#项目状态
        self.updatetime = project_info['updatetime']
        #更新项目处理脚本
        md5sum = utils.md5string(project_info['script'])
        #如果项目为活跃状态且（项目脚本发生变化或self.waiting_get_info为True）则
        if (self.md5sum != md5sum or self.waiting_get_info) and self.active:
            self._send_on_get_info = True
            self.waiting_get_info = True
        #无论脚本是否更改都直接更新
        self.md5sum = md5sum
        #更新抓取速率和并发数
        if self.active:
            self.task_queue.rate = project_info['rate']
            self.task_queue.burst = project_info['burst']
        else:
            self.task_queue.rate = 0
            self.task_queue.burst = 0

        logger.info('project %s updated, status:%s, paused:%s, %d tasks',
                    self.name, self.db_status, self.paused, len(self.task_queue))

    def on_get_info(self, info):
        self.waiting_get_info = False
        self.min_tick = info.get('min_tick', 0)
        self.retry_delay = info.get('retry_delay', {})
        self.crawl_config = info.get('crawl_config', {})
    #查看数据库中的项目状态，'RUNNING'或'DEBUG'则返回True（运行），其他返回False（非运行）
    @property
    def active(self):
        return self.db_status in ('RUNNING', 'DEBUG')


class Scheduler(object):
    #项目更新周期
    UPDATE_PROJECT_INTERVAL = 5 * 60                                                                            
    #默认调度参数
    default_schedule = {
        'priority': 0,
        'retries': 3,
        'exetime': 0,
        'age': -1,
        'itag': None,
    }
    LOOP_LIMIT = 1000
    LOOP_INTERVAL = 0.1
    ACTIVE_TASKS = 100
    INQUEUE_LIMIT = 0
    EXCEPTION_LIMIT = 3
    DELETE_TIME = 24 * 60 * 60
    DEFAULT_RETRY_DELAY = {
        0: 30,
        1: 1*60*60,
        2: 6*60*60,
        3: 12*60*60,
        '': 24*60*60
    }
    #默认暂停的任务失败数阈值
    FAIL_PAUSE_NUM = 10
    PAUSE_TIME = 5*60
    #检查阈值
    UNPAUSE_CHECK_NUM = 3
    #特殊任务类型
    TASK_PACK = 1
    STATUS_PACK = 2  # current not used
    REQUEST_PACK = 3  # current not used

    def __init__(self, taskdb, projectdb, newtask_queue, status_queue,
                 out_queue, data_path='./data', resultdb=None):
        self.taskdb = taskdb
        self.projectdb = projectdb
        self.resultdb = resultdb
        self.newtask_queue = newtask_queue
        self.status_queue = status_queue
        self.out_queue = out_queue
        self.data_path = data_path

        self._send_buffer = deque()
        self._quit = False
        self._exceptions = 0
        self.projects = dict()
        self._force_update_project = False
        self._last_update_project = 0
        self._last_tick = int(time.time())
        self._postpone_request = []
        #所有项目各时间段内的任务数
        self._cnt = {
            "5m_time": counter.CounterManager(
                lambda: counter.TimebaseAverageEventCounter(30, 10)),
            "5m": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(30, 10)),
            "1h": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(60, 60)),
            "1d": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(10 * 60, 24 * 6)),
            "all": counter.CounterManager(
                lambda: counter.TotalCounter()),
        }
        #从文件中读取活动任务数信息
        self._cnt['1h'].load(os.path.join(self.data_path, 'scheduler.1h'))
        self._cnt['1d'].load(os.path.join(self.data_path, 'scheduler.1d'))
        self._cnt['all'].load(os.path.join(self.data_path, 'scheduler.all'))
        self._last_dump_cnt = 0

    def _update_projects(self):
        '''Check project update'''
        now = time.time()
        #如果没到按更新周期确定的更新时间且强制更新参数为false，则不进行更新
        if (
                not self._force_update_project
                and self._last_update_project + self.UPDATE_PROJECT_INTERVAL > now
        ):
            return
        #更新所有项目
        for project in self.projectdb.check_update(self._last_update_project):#（？？？？）
            self._update_project(project)
            logger.debug("project: %s updated.", project['name'])
        self._force_update_project = False
        self._last_update_project = now

    get_info_attributes = ['min_tick', 'retry_delay', 'crawl_config']
    #更新一个项目
    def _update_project(self, project):
        '''update one project'''
        #如果需要更新的项目名称不在self.projects的keys中，则在self.projects中加入该项目名称和Project对象的key-values对
        if project['name'] not in self.projects:
            self.projects[project['name']] = Project(self, project)
        else:
            #更新Project对象（包括项目名称、项目处理脚本等）
            self.projects[project['name']].update(project)
        #将Project对象赋给project
        project = self.projects[project['name']]
        #如果_send_on_get_info为True，发送_on_get_info请求
        if project._send_on_get_info:
            # update project runtime info from processor by sending a _on_get_info
            # request, result is in status_page.track.save
            #_send_on_get_info置位false
            project._send_on_get_info = False
            #制作特定task并将其压入输出队列
            self.on_select_task({
                'taskid': '_on_get_info',
                'project': project.name,
                'url': 'data:,_on_get_info',
                'status': self.taskdb.SUCCESS,
                'fetch': {
                    'save': self.get_info_attributes,
                },
                'process': {
                    'callback': '_on_get_info',
                },
            })

        # load task queue when project is running and delete task_queue when project is stoped
        if project.active:
            if not project.task_loaded:
                #从数据库中load任务到task_queue
                self._load_tasks(project)
                project.task_loaded = True
        else:
            #如果项目非活跃则初始化task_queue
            if project.task_loaded:
                project.task_queue = TaskQueue()
                project.task_loaded = False

            if project not in self._cnt['all']:
                #如果project没有在self._cnt['all']中，则查询数据库更新项目各类任务数(success,failed,pending)
                self._update_project_cnt(project.name)

    scheduler_task_fields = ['taskid', 'project', 'schedule', ]

    #从数据库中load任务到task_queue
    def _load_tasks(self, project):
        '''load tasks from database'''
        task_queue = project.task_queue

        for task in self.taskdb.load_tasks(
                self.taskdb.ACTIVE, project.name, self.scheduler_task_fields
        ):
            taskid = task['taskid']
            _schedule = task.get('schedule', self.default_schedule)
            priority = _schedule.get('priority', self.default_schedule['priority'])
            exetime = _schedule.get('exetime', self.default_schedule['exetime'])
            #把每个任务都压入task queue(根据不同的条件选择压入priority_queue或者time_queue)
            task_queue.put(taskid, priority, exetime)
        #把project.task_loaded置位为true表示该项目任务已load
        project.task_loaded = True
        logger.debug('project: %s loaded %d tasks.', project.name, len(task_queue))
        if project not in self._cnt['all']:
            #如果project没有在self._cnt['all']中，则查询数据库更新项目各类任务数(success,failed,pending)
            self._update_project_cnt(project.name)
        #将project的pending任务数更新为task_queue的大小
        self._cnt['all'].value((project.name, 'pending'), len(project.task_queue))
    #查询数据库更新项目各类任务数(success,failed,pending)
    def _update_project_cnt(self, project_name):
        status_count = self.taskdb.status_count(project_name)
        self._cnt['all'].value(
            (project_name, 'success'),
            status_count.get(self.taskdb.SUCCESS, 0)
        )
        self._cnt['all'].value(
            (project_name, 'failed'),
            status_count.get(self.taskdb.FAILED, 0) + status_count.get(self.taskdb.BAD, 0)
        )
        self._cnt['all'].value(
            (project_name, 'pending'),
            status_count.get(self.taskdb.ACTIVE, 0)
        )
    #检查任务相关各参数是否完善
    def task_verify(self, task):
        '''
        return False if any of 'taskid', 'project', 'url' is not in task dict
                        or project not in task_queue
        '''
        for each in ('taskid', 'project', 'url', ):
            if each not in task or not task[each]:
                logger.error('%s not in task: %.200r', each, task)
                return False
        if task['project'] not in self.projects:
            logger.error('unknown project: %s', task['project'])
            return False

        project = self.projects[task['project']]
        if not project.active:
            logger.error('project %s not started, please set status to RUNNING or DEBUG',
                         task['project'])
            return False
        return True
    #向taskdb写入task
    def insert_task(self, task):
        '''insert task into database'''
        return self.taskdb.insert(task['project'], task['taskid'], task)

    # 更新taskdb
    def update_task(self, task):
        '''update task in database'''
        return self.taskdb.update(task['project'], task['taskid'], task)
    #将任务压入task queue
    def put_task(self, task):
        '''put task to task queue'''
        _schedule = task.get('schedule', self.default_schedule)
        self.projects[task['project']].task_queue.put(
            task['taskid'],
            priority=_schedule.get('priority', self.default_schedule['priority']),
            exetime=_schedule.get('exetime', self.default_schedule['exetime'])
        )

    #向输出队列中发送任务
    def send_task(self, task, force=True):
        '''
        dispatch task to fetcher
        out queue may have size limit to prevent block, a send_buffer is used
        '''
        try:
            #向输出队列中压入任务
            self.out_queue.put_nowait(task)
        except Queue.Full:
            #若输出队列已满，则将任务左加到_send_buffer双向队列中
            if force:
                self._send_buffer.appendleft(task)
            else:
                raise
    #从status_queue队列里取processor已完成任务，并做一系列分析处理
    def _check_task_done(self):
        '''Check status queue'''
        #对status_queue已完成任务做计数（去除_on_get_info任务和bad task）
        cnt = 0
        try:
            while True:
                #从status_queue队列里取任务
                task = self.status_queue.get_nowait()
                # check _on_get_info result here
                if task.get('taskid') == '_on_get_info' and 'project' in task and 'track' in task:
                    if task['project'] not in self.projects:
                        continue
                    project = self.projects[task['project']]
                    project.on_get_info(task['track'].get('save') or {})
                    logger.info(
                        '%s on_get_info %r', task['project'], task['track'].get('save', {})
                    )
                    continue
                #检查任务各参数是否完善
                elif not self.task_verify(task):
                    continue
                #对从status_queue队列里取到的任务做一系列分析处理，包括更新taskdb、失败重抓、自动重抓、更新项目任务计数等
                self.on_task_status(task)
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    merge_task_fields = ['taskid', 'project', 'url', 'status', 'schedule', 'lastcrawltime']
    #从newtask_queue中获取processor新产生的任务并做一系列处理
    def _check_request(self):
        '''Check new task queue'''
        # check _postpone_request first
        todo = []
        for task in self._postpone_request:
            if task['project'] not in self.projects:
                continue
            if self.projects[task['project']].task_queue.is_processing(task['taskid']):
                todo.append(task)
            else:
                self.on_request(task)
        self._postpone_request = todo

        tasks = {}
        while len(tasks) < self.LOOP_LIMIT:
            try:
                #从newtask_queue获取新任务
                task = self.newtask_queue.get_nowait()
            except Queue.Empty:
                break

            if isinstance(task, list):
                _tasks = task
            else:
                _tasks = (task, )

            for task in _tasks:
                #如果该任务不符合要求，跳过
                if not self.task_verify(task):
                    continue
                #如果task的taskid在项目的task_queue中
                if task['taskid'] in self.projects[task['project']].task_queue:
                    #如果无force_update参数或者该参数置位False时忽略该newtask
                    if not task.get('schedule', {}).get('force_update', False):
                        logger.debug('ignore newtask %(project)s:%(taskid)s %(url)s', task)
                        continue
                #如果该taskid已经在tasks中存在，同样忽略该newtask
                if task['taskid'] in tasks:
                    if not task.get('schedule', {}).get('force_update', False):
                        continue
                #将该newtask添加到tasks
                tasks[task['taskid']] = task
        #历遍tasks里的所有task（itervalues(tasks):返回一个由tasks所有values组成的迭代器）
        for task in itervalues(tasks):
            self.on_request(task)

        return len(tasks)

    def _check_cronjob(self):
        """Check projects cronjob tick, return True when a new tick is sended"""
        now = time.time()
        self._last_tick = int(self._last_tick)
        if now - self._last_tick < 1:
            return False
        self._last_tick += 1
        for project in itervalues(self.projects):
            if not project.active:
                continue
            if project.waiting_get_info:
                continue
            if int(project.min_tick) == 0:
                continue
            if self._last_tick % int(project.min_tick) != 0:
                continue
            self.on_select_task({
                'taskid': '_on_cronjob',
                'project': project.name,
                'url': 'data:,_on_cronjob',
                'status': self.taskdb.SUCCESS,
                'fetch': {
                    'save': {
                        'tick': self._last_tick,
                    },
                },
                'process': {
                    'callback': '_on_cronjob',
                },
            })
        return True

    request_task_fields = [
        'taskid',
        'project',
        'url',
        'status',
        'schedule',
        'fetch',
        'process',
        'track',
        'lastcrawltime'
    ]

    def _check_select(self):
        '''Select task to fetch & process'''
        while self._send_buffer:
            _task = self._send_buffer.pop()
            try:
                # use force=False here to prevent automatic send_buffer append and get exception
                self.send_task(_task, False)
            except Queue.Full:
                self._send_buffer.append(_task)
                break

        if self.out_queue.full():
            return {}

        taskids = []
        cnt = 0
        cnt_dict = dict()
        limit = self.LOOP_LIMIT
        for project in itervalues(self.projects):
            if not project.active:
                continue
            # only check project pause when select new tasks, cronjob and new request still working
            if project.paused:
                continue
            if project.waiting_get_info:
                continue
            if cnt >= limit:
                break

            # task queue
            task_queue = project.task_queue
            task_queue.check_update()
            project_cnt = 0

            # check send_buffer here. when not empty, out_queue may blocked. Not sending tasks
            while cnt < limit and project_cnt < limit / 10:
                taskid = task_queue.get()
                if not taskid:
                    break

                taskids.append((project.name, taskid))
                if taskid != 'on_finished':
                    project_cnt += 1
                cnt += 1

            cnt_dict[project.name] = project_cnt
            if project_cnt:
                project._selected_tasks = True
                project._send_finished_event_wait = 0

            # check and send finished event to project
            if not project_cnt and len(task_queue) == 0 and project._selected_tasks:
                # wait for self.FAIL_PAUSE_NUM steps to make sure all tasks in queue have been processed
                if project._send_finished_event_wait < self.FAIL_PAUSE_NUM:
                    project._send_finished_event_wait += 1
                else:
                    project._selected_tasks = False
                    project._send_finished_event_wait = 0

                    self._postpone_request.append({
                        'project': project.name,
                        'taskid': 'on_finished',
                        'url': 'data:,on_finished',
                        'process': {
                            'callback': 'on_finished',
                        },
                        "schedule": {
                            "age": 0,
                            "priority": 9,
                            "force_update": True,
                        },
                    })

        for project, taskid in taskids:
            self._load_put_task(project, taskid)

        return cnt_dict

    def _load_put_task(self, project, taskid):
        try:
            task = self.taskdb.get_task(project, taskid, fields=self.request_task_fields)
        except ValueError:
            logger.error('bad task pack %s:%s', project, taskid)
            return
        if not task:
            return
        task = self.on_select_task(task)

    def _print_counter_log(self):
        # print top 5 active counters
        keywords = ('pending', 'success', 'retry', 'failed')
        total_cnt = {}
        project_actives = []
        project_fails = []
        for key in keywords:
            total_cnt[key] = 0
        for project, subcounter in iteritems(self._cnt['5m']):
            actives = 0
            for key in keywords:
                cnt = subcounter.get(key, None)
                if cnt:
                    cnt = cnt.sum
                    total_cnt[key] += cnt
                    actives += cnt

            project_actives.append((actives, project))

            fails = subcounter.get('failed', None)
            if fails:
                project_fails.append((fails.sum, project))

        top_2_fails = sorted(project_fails, reverse=True)[:2]
        top_3_actives = sorted([x for x in project_actives if x[1] not in top_2_fails],
                               reverse=True)[:5 - len(top_2_fails)]

        log_str = ("in 5m: new:%(pending)d,success:%(success)d,"
                   "retry:%(retry)d,failed:%(failed)d" % total_cnt)
        for _, project in itertools.chain(top_3_actives, top_2_fails):
            subcounter = self._cnt['5m'][project].to_dict(get_value='sum')
            log_str += " %s:%d,%d,%d,%d" % (project,
                                            subcounter.get('pending', 0),
                                            subcounter.get('success', 0),
                                            subcounter.get('retry', 0),
                                            subcounter.get('failed', 0))
        logger.info(log_str)

    def _dump_cnt(self):
        '''Dump counters to file'''
        self._cnt['1h'].dump(os.path.join(self.data_path, 'scheduler.1h'))
        self._cnt['1d'].dump(os.path.join(self.data_path, 'scheduler.1d'))
        self._cnt['all'].dump(os.path.join(self.data_path, 'scheduler.all'))

    def _try_dump_cnt(self):
        '''Dump counters every 60 seconds'''
        now = time.time()
        if now - self._last_dump_cnt > 60:
            self._last_dump_cnt = now
            self._dump_cnt()
            self._print_counter_log()

    def _check_delete(self):
        '''Check project delete'''
        now = time.time()
        for project in list(itervalues(self.projects)):
            if project.db_status != 'STOP':
                continue
            if now - project.updatetime < self.DELETE_TIME:
                continue
            if 'delete' not in self.projectdb.split_group(project.group):
                continue

            logger.warning("deleting project: %s!", project.name)
            del self.projects[project.name]
            self.taskdb.drop(project.name)
            self.projectdb.drop(project.name)
            if self.resultdb:
                self.resultdb.drop(project.name)
            for each in self._cnt.values():
                del each[project.name]

    def __len__(self):
        return sum(len(x.task_queue) for x in itervalues(self.projects))

    def quit(self):
        '''Set quit signal'''
        self._quit = True
        # stop xmlrpc server
        if hasattr(self, 'xmlrpc_server'):
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_server.stop)
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_ioloop.stop)

    def run_once(self):
        '''comsume queues and feed tasks to fetcher, once'''

        self._update_projects()
        self._check_task_done()
        self._check_request()
        while self._check_cronjob():
            pass
        self._check_select()
        self._check_delete()
        self._try_dump_cnt()

    def run(self):
        '''Start scheduler loop'''
        logger.info("scheduler starting...")

        while not self._quit:
            try:
                time.sleep(self.LOOP_INTERVAL)
                self.run_once()
                self._exceptions = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception(e)
                self._exceptions += 1
                if self._exceptions > self.EXCEPTION_LIMIT:
                    break
                continue

        logger.info("scheduler exiting...")
        self._dump_cnt()

    def trigger_on_start(self, project):
        '''trigger an on_start callback of project'''
        self.newtask_queue.put({
            "project": project,
            "taskid": "on_start",
            "url": "data:,on_start",
            "process": {
                "callback": "on_start",
            },
        })

    def xmlrpc_run(self, port=23333, bind='127.0.0.1', logRequests=False):
        '''Start xmlrpc interface'''
        from pyspider.libs.wsgi_xmlrpc import WSGIXMLRPCApplication

        application = WSGIXMLRPCApplication()

        application.register_function(self.quit, '_quit')
        application.register_function(self.__len__, 'size')

        def dump_counter(_time, _type):
            try:
                return self._cnt[_time].to_dict(_type)
            except:
                logger.exception('')
        application.register_function(dump_counter, 'counter')

        def new_task(task):
            if self.task_verify(task):
                self.newtask_queue.put(task)
                return True
            return False
        application.register_function(new_task, 'newtask')

        def send_task(task):
            '''dispatch task to fetcher'''
            self.send_task(task)
            return True
        application.register_function(send_task, 'send_task')

        def update_project():
            self._force_update_project = True
        application.register_function(update_project, 'update_project')

        def get_active_tasks(project=None, limit=100):
            allowed_keys = set((
                'type',
                'taskid',
                'project',
                'status',
                'url',
                'lastcrawltime',
                'updatetime',
                'track',
            ))
            track_allowed_keys = set((
                'ok',
                'time',
                'follows',
                'status_code',
            ))

            iters = [iter(x.active_tasks) for k, x in iteritems(self.projects)
                     if x and (k == project if project else True)]
            tasks = [next(x, None) for x in iters]
            result = []

            while len(result) < limit and tasks and not all(x is None for x in tasks):
                updatetime, task = t = max(t for t in tasks if t)
                i = tasks.index(t)
                tasks[i] = next(iters[i], None)
                for key in list(task):
                    if key == 'track':
                        for k in list(task[key].get('fetch', [])):
                            if k not in track_allowed_keys:
                                del task[key]['fetch'][k]
                        for k in list(task[key].get('process', [])):
                            if k not in track_allowed_keys:
                                del task[key]['process'][k]
                    if key in allowed_keys:
                        continue
                    del task[key]
                result.append(t)
            # fix for "<type 'exceptions.TypeError'>:dictionary key must be string"
            # have no idea why
            return json.loads(json.dumps(result))
        application.register_function(get_active_tasks, 'get_active_tasks')

        def get_projects_pause_status():
            result = {}
            for project_name, project in iteritems(self.projects):
                result[project_name] = project.paused
            return result
        application.register_function(get_projects_pause_status, 'get_projects_pause_status')

        def webui_update():
            return {
                'pause_status': get_projects_pause_status(),
                'counter': {
                    '5m_time': dump_counter('5m_time', 'avg'),
                    '5m': dump_counter('5m', 'sum'),
                    '1h': dump_counter('1h', 'sum'),
                    '1d': dump_counter('1d', 'sum'),
                    'all': dump_counter('all', 'sum'),
                },
            }
        application.register_function(webui_update, 'webui_update')

        import tornado.wsgi
        import tornado.ioloop
        import tornado.httpserver

        container = tornado.wsgi.WSGIContainer(application)
        self.xmlrpc_ioloop = tornado.ioloop.IOLoop()
        self.xmlrpc_server = tornado.httpserver.HTTPServer(container, io_loop=self.xmlrpc_ioloop)
        self.xmlrpc_server.listen(port=port, address=bind)
        logger.info('scheduler.xmlrpc listening on %s:%s', bind, port)
        self.xmlrpc_ioloop.start()
    #处理从newtask_queue获得的task
    def on_request(self, task):
        #如果len(self.projects[task['project']].task_queue) >= self.INQUEUE_LIMIT，报task_queue任务超限，忽略该任务
        if self.INQUEUE_LIMIT and len(self.projects[task['project']].task_queue) >= self.INQUEUE_LIMIT:
            logger.debug('overflow task %(project)s:%(taskid)s %(url)s', task)
            return
        #查看该task是否是旧任务
        oldtask = self.taskdb.get_task(task['project'], task['taskid'],
                                       fields=self.merge_task_fields)
        if oldtask:
            #如果是taskdb中已存在的任务，则执行on_old_request
            return self.on_old_request(task, oldtask)
        else:
            #如果是真正的新任务则执行on_new_request
            return self.on_new_request(task)
    #当一个真正的新任务来到时调用
    def on_new_request(self, task):
        '''Called when a new request is arrived'''
        #更改任务状态为活跃
        task['status'] = self.taskdb.ACTIVE
        self.insert_task(task)
        self.put_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'pending'), +1)
        self._cnt['1h'].event((project, 'pending'), +1)
        self._cnt['1d'].event((project, 'pending'), +1)
        self._cnt['all'].event((project, 'pending'), +1)
        logger.info('new task %(project)s:%(taskid)s %(url)s', task)
        return task
    #当一个taskdb中已存在的任务到来时调用
    def on_old_request(self, task, old_task):
        '''Called when a crawled task is arrived'''
        now = time.time()

        _schedule = task.get('schedule', self.default_schedule)
        old_schedule = old_task.get('schedule', {})
        #如果有该任务ID有对应的任务正在处理，则将该task暂时推入_postpone_request保存并返回（前提还得force_update为True）
        if _schedule.get('force_update') and self.projects[task['project']].task_queue.is_processing(task['taskid']):
            # when a task is in processing, the modify may conflict with the running task.
            # postpone the modify after task finished.
            logger.info('postpone modify task %(project)s:%(taskid)s %(url)s', task)
            self._postpone_request.append(task)
            return

        restart = False
        #比较新任务age以及itag参数是否相同，且判断itag参数优先，从而判断重抓参数restart是否置位True（还要注意force_update参数）
        schedule_age = _schedule.get('age', self.default_schedule['age'])
        if _schedule.get('itag') and _schedule['itag'] != old_schedule.get('itag'):
            restart = True
        elif schedule_age >= 0 and schedule_age + (old_task.get('lastcrawltime', 0) or 0) < now:
            restart = True
        elif _schedule.get('force_update'):
            restart = True

        if not restart:
            logger.debug('ignore newtask %(project)s:%(taskid)s %(url)s', task)
            return

        if _schedule.get('cancel'):
            logger.info('cancel task %(project)s:%(taskid)s %(url)s', task)
            task['status'] = self.taskdb.BAD
            self.update_task(task)
            self.projects[task['project']].task_queue.delete(task['taskid'])
            return task

        task['status'] = self.taskdb.ACTIVE
        self.update_task(task)
        self.put_task(task)

        project = task['project']
        if old_task['status'] != self.taskdb.ACTIVE:
            self._cnt['5m'].event((project, 'pending'), +1)
            self._cnt['1h'].event((project, 'pending'), +1)
            self._cnt['1d'].event((project, 'pending'), +1)
        if old_task['status'] == self.taskdb.SUCCESS:
            self._cnt['all'].event((project, 'success'), -1).event((project, 'pending'), +1)
        elif old_task['status'] == self.taskdb.FAILED:
            self._cnt['all'].event((project, 'failed'), -1).event((project, 'pending'), +1)
        logger.info('restart task %(project)s:%(taskid)s %(url)s', task)
        return task
    #处理从status queue中获得的task
    def on_task_status(self, task):
        '''Called when a status pack is arrived'''
        try:
            procesok = task['track']['process']['ok']
            if not self.projects[task['project']].task_queue.done(task['taskid']):
                logging.error('not processing pack: %(project)s:%(taskid)s %(url)s', task)
                return None
        except KeyError as e:
            logger.error("Bad status pack: %s", e)
            return None
        #task成功完成时调用on_task_done，task失败时调用on_task_failed
        if procesok:
            ret = self.on_task_done(task)
        else:
            ret = self.on_task_failed(task)
        #更新self._cnt['5m_time']
        if task['track']['fetch'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'fetch_time'),
                                       task['track']['fetch']['time'])
        if task['track']['process'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'process_time'),
                                       task['track']['process'].get('time'))
        #将(time.time(), task)左加到该task所在project的active_tasks双向队列中去
        self.projects[task['project']].active_tasks.appendleft((time.time(), task))
        return ret
    #当一个task成功完成时调用
    def on_task_done(self, task):
        '''Called when a task is done and success, called by `on_task_status`'''
        #task.status标记成功，更新lastcrawltime
        task['status'] = self.taskdb.SUCCESS
        task['lastcrawltime'] = time.time()
        if 'schedule' in task:
            #如果task['schedule']中有自动重抓字段且为True则task状态标记为active，任务以age参数为周期做重复抓取
            if task['schedule'].get('auto_recrawl') and 'age' in task['schedule']:
                task['status'] = self.taskdb.ACTIVE
                next_exetime = task['schedule'].get('age')
                task['schedule']['exetime'] = time.time() + next_exetime
                self.put_task(task)
            else:
                del task['schedule']
        #更新taskdb
        self.update_task(task)
        #更新任务成功数
        project = task['project']
        self._cnt['5m'].event((project, 'success'), +1)
        self._cnt['1h'].event((project, 'success'), +1)
        self._cnt['1d'].event((project, 'success'), +1)
        self._cnt['all'].event((project, 'success'), +1).event((project, 'pending'), -1)
        logger.info('task done %(project)s:%(taskid)s %(url)s', task)
        return task
    #任务失败时调用
    def on_task_failed(self, task):
        '''Called when a task is failed, called by `on_task_status`'''
        #如果任务中没有schedule字段则从taskdb去找旧任务的schedule来替代
        if 'schedule' not in task:
            old_task = self.taskdb.get_task(task['project'], task['taskid'], fields=['schedule'])
            if old_task is None:
                logging.error('unknown status pack: %s' % task)
                return
            task['schedule'] = old_task.get('schedule', {})
        #查找retries和retried参数
        retries = task['schedule'].get('retries', self.default_schedule['retries'])
        retried = task['schedule'].get('retried', 0)
        #查找task所在项目的retry_delay，没有则使用默认的DEFAULT_RETRY_DELAY
        project_info = self.projects[task['project']]
        retry_delay = project_info.retry_delay or self.DEFAULT_RETRY_DELAY
        #令next_exetime为该次重抓时延
        next_exetime = retry_delay.get(retried, retry_delay.get('', self.DEFAULT_RETRY_DELAY['']))
        #若果该task恰巧有自动重抓机制，则取重抓时延和age中较小的时间为next_exetime
        if task['schedule'].get('auto_recrawl') and 'age' in task['schedule']:
            next_exetime = min(next_exetime, task['schedule'].get('age'))
        else:
            #如果重抓次数到达次数上限则next_exetime置位-1（不再继续尝试）
            if retried >= retries:
                next_exetime = -1
            #如果可以继续尝试重抓，则取重抓时延和age中较小的时间为next_exetime
            elif 'age' in task['schedule'] and next_exetime > task['schedule'].get('age'):
                next_exetime = task['schedule'].get('age')

        if next_exetime < 0:
            #更新taskdb
            task['status'] = self.taskdb.FAILED
            task['lastcrawltime'] = time.time()
            self.update_task(task)
            #更新项目失败任务数
            project = task['project']
            self._cnt['5m'].event((project, 'failed'), +1)
            self._cnt['1h'].event((project, 'failed'), +1)
            self._cnt['1d'].event((project, 'failed'), +1)
            self._cnt['all'].event((project, 'failed'), +1).event((project, 'pending'), -1)
            logger.info('task failed %(project)s:%(taskid)s %(url)s' % task)
            return task
        else:
            #可以继续重抓，更新retried，exetime，lastcrawltime，更新taskdb，将task压入task queue
            task['schedule']['retried'] = retried + 1
            task['schedule']['exetime'] = time.time() + next_exetime
            task['lastcrawltime'] = time.time()
            self.update_task(task)
            self.put_task(task)
            #更新项目重抓任务数
            project = task['project']
            self._cnt['5m'].event((project, 'retry'), +1)
            self._cnt['1h'].event((project, 'retry'), +1)
            self._cnt['1d'].event((project, 'retry'), +1)
            # self._cnt['all'].event((project, 'retry'), +1)
            logger.info('task retry %d/%d %%(project)s:%%(taskid)s %%(url)s' % (
                retried, retries), task)
            return task
    #制作selected（特定）的任务并压入输出队列
    def on_select_task(self, task):
        '''Called when a task is selected to fetch & process'''
        # inject informations about project
        logger.info('select %(project)s:%(taskid)s %(url)s', task)
        #拿到该项目的Project对象
        project_info = self.projects.get(task['project'])
        assert project_info, 'no such project'
        
        task['type'] = self.TASK_PACK
        task['group'] = project_info.group
        task['project_md5sum'] = project_info.md5sum
        task['project_updatetime'] = project_info.updatetime

        # lazy join project.crawl_config
        if getattr(project_info, 'crawl_config', None):
            #初始化task的fetch和process字段
            task = BaseHandler.task_join_crawl_config(task, project_info.crawl_config)
        #在双向的活动任务队列中左加上该特殊任务
        project_info.active_tasks.appendleft((time.time(), task))
        #发送该任务，即把任务压入输出队列
        self.send_task(task)
        return task


from tornado import gen


class OneScheduler(Scheduler):
    """
    Scheduler Mixin class for one mode
    overwirted send_task method
    call processor.on_task(fetcher.fetch(task)) instead of consuming queue
    """

    def _check_select(self):
        """
        interactive mode of select tasks
        """
        if not self.interactive:
            return super(OneScheduler, self)._check_select()

        # waiting for running tasks
        if self.running_task > 0:
            return

        is_crawled = []

        def run(project=None):
            return crawl('on_start', project=project)

        def crawl(url, project=None, **kwargs):
            """
            Crawl given url, same parameters as BaseHandler.crawl
            url - url or taskid, parameters will be used if in taskdb
            project - can be ignored if only one project exists.
            """

            # looking up the project instance
            if project is None:
                if len(self.projects) == 1:
                    project = list(self.projects.keys())[0]
                else:
                    raise LookupError('You need specify the project: %r'
                                      % list(self.projects.keys()))
            project_data = self.processor.project_manager.get(project)
            if not project_data:
                raise LookupError('no such project: %s' % project)

            # get task package
            instance = project_data['instance']
            instance._reset()
            task = instance.crawl(url, **kwargs)
            if isinstance(task, list):
                raise Exception('url list is not allowed in interactive mode')

            # check task in taskdb
            if not kwargs:
                dbtask = self.taskdb.get_task(task['project'], task['taskid'],
                                              fields=self.request_task_fields)
                if not dbtask:
                    dbtask = self.taskdb.get_task(task['project'], task['url'],
                                                  fields=self.request_task_fields)
                if dbtask:
                    task = dbtask

            # select the task
            self.on_select_task(task)
            is_crawled.append(True)

            shell.ask_exit()

        def quit_interactive():
            '''Quit interactive mode'''
            is_crawled.append(True)
            self.interactive = False
            shell.ask_exit()

        def quit_pyspider():
            '''Close pyspider'''
            is_crawled[:] = []
            shell.ask_exit()

        shell = utils.get_python_console()
        banner = (
            'pyspider shell - Select task\n'
            'crawl(url, project=None, **kwargs) - same parameters as BaseHandler.crawl\n'
            'quit_interactive() - Quit interactive mode\n'
            'quit_pyspider() - Close pyspider'
        )
        if hasattr(shell, 'show_banner'):
            shell.show_banner(banner)
            shell.interact()
        else:
            shell.interact(banner)
        if not is_crawled:
            self.ioloop.add_callback(self.ioloop.stop)

    def __getattr__(self, name):
        """patch for crawl(url, callback=self.index_page) API"""
        if self.interactive:
            return name
        raise AttributeError(name)

    def on_task_status(self, task):
        """Ignore not processing error in interactive mode"""
        if not self.interactive:
            super(OneScheduler, self).on_task_status(task)

        try:
            procesok = task['track']['process']['ok']
        except KeyError as e:
            logger.error("Bad status pack: %s", e)
            return None

        if procesok:
            ret = self.on_task_done(task)
        else:
            ret = self.on_task_failed(task)
        if task['track']['fetch'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'fetch_time'),
                                       task['track']['fetch']['time'])
        if task['track']['process'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'process_time'),
                                       task['track']['process'].get('time'))
        self.projects[task['project']].active_tasks.appendleft((time.time(), task))
        return ret

    def init_one(self, ioloop, fetcher, processor,
                 result_worker=None, interactive=False):
        self.ioloop = ioloop
        self.fetcher = fetcher
        self.processor = processor
        self.result_worker = result_worker
        self.interactive = interactive
        self.running_task = 0

    @gen.coroutine
    def do_task(self, task):
        self.running_task += 1
        result = yield gen.Task(self.fetcher.fetch, task)
        type, task, response = result.args
        self.processor.on_task(task, response)
        # do with message
        while not self.processor.inqueue.empty():
            _task, _response = self.processor.inqueue.get()
            self.processor.on_task(_task, _response)
        # do with results
        while not self.processor.result_queue.empty():
            _task, _result = self.processor.result_queue.get()
            if self.result_worker:
                self.result_worker.on_result(_task, _result)
        self.running_task -= 1

    def send_task(self, task, force=True):
        if self.fetcher.http_client.free_size() <= 0:
            if force:
                self._send_buffer.appendleft(task)
            else:
                raise self.outqueue.Full
        self.ioloop.add_future(self.do_task(task), lambda x: x.result())

    def run(self):
        import tornado.ioloop
        tornado.ioloop.PeriodicCallback(self.run_once, 100,
                                        io_loop=self.ioloop).start()
        self.ioloop.start()

    def quit(self):
        self.ioloop.stop()
        logger.info("scheduler exiting...")


import random
import threading
from pyspider.database.sqlite.sqlitebase import SQLiteMixin


class ThreadBaseScheduler(Scheduler):
    def __init__(self, threads=4, *args, **kwargs):
        self.local = threading.local()

        super(ThreadBaseScheduler, self).__init__(*args, **kwargs)

        if isinstance(self.taskdb, SQLiteMixin):
            self.threads = 1
        else:
            self.threads = threads

        self._taskdb = self.taskdb
        self._projectdb = self.projectdb
        self._resultdb = self.resultdb

        self.thread_objs = []
        self.thread_queues = []
        self._start_threads()
        assert len(self.thread_queues) > 0

    @property
    def taskdb(self):
        if not hasattr(self.local, 'taskdb'):
            self.taskdb = self._taskdb.copy()
        return self.local.taskdb

    @taskdb.setter
    def taskdb(self, taskdb):
        self.local.taskdb = taskdb

    @property
    def projectdb(self):
        if not hasattr(self.local, 'projectdb'):
            self.projectdb = self._projectdb.copy()
        return self.local.projectdb

    @projectdb.setter
    def projectdb(self, projectdb):
        self.local.projectdb = projectdb

    @property
    def resultdb(self):
        if not hasattr(self.local, 'resultdb'):
            self.resultdb = self._resultdb.copy()
        return self.local.resultdb

    @resultdb.setter
    def resultdb(self, resultdb):
        self.local.resultdb = resultdb

    def _start_threads(self):
        for i in range(self.threads):
            queue = Queue.Queue()
            thread = threading.Thread(target=self._thread_worker, args=(queue, ))
            thread.daemon = True
            thread.start()
            self.thread_objs.append(thread)
            self.thread_queues.append(queue)

    def _thread_worker(self, queue):
        while True:
            method, args, kwargs = queue.get()
            try:
                method(*args, **kwargs)
            except Exception as e:
                logger.exception(e)

    def _run_in_thread(self, method, *args, **kwargs):
        i = kwargs.pop('_i', None)
        block = kwargs.pop('_block', False)

        if i is None:
            while True:
                for queue in self.thread_queues:
                    if queue.empty():
                        break
                else:
                    if block:
                        time.sleep(0.1)
                        continue
                    else:
                        queue = self.thread_queues[random.randint(0, len(self.thread_queues)-1)]
                break
        else:
            queue = self.thread_queues[i % len(self.thread_queues)]

        queue.put((method, args, kwargs))

        if block:
            self._wait_thread()

    def _wait_thread(self):
        while True:
            if all(queue.empty() for queue in self.thread_queues):
                break
            time.sleep(0.1)

    def _update_project(self, project):
        self._run_in_thread(Scheduler._update_project, self, project)

    def on_task_status(self, task):
        i = hash(task['taskid'])
        self._run_in_thread(Scheduler.on_task_status, self, task, _i=i)

    def on_request(self, task):
        i = hash(task['taskid'])
        self._run_in_thread(Scheduler.on_request, self, task, _i=i)

    def _load_put_task(self, project, taskid):
        i = hash(taskid)
        self._run_in_thread(Scheduler._load_put_task, self, project, taskid, _i=i)

    def run_once(self):
        super(ThreadBaseScheduler, self).run_once()
        self._wait_thread()
