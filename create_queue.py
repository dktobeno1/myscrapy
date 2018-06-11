import queue,time
from multiprocessing.managers import BaseManager

task_queue = queue.Queue()

class QueueManager(BaseManager):
    pass

def give_task_queue():
    return task_queue

def create_queue():
    QueueManager.register('get_task_queue', callable=give_task_queue)
    manager = QueueManager(address=('127.0.0.1', 5666), authkey=b'abc')
    manager.start()
    task = manager.get_task_queue()
    while True:
        print(task.qsize())
        time.sleep(5)


if __name__ == '__main__':
    
      create_queue()  
