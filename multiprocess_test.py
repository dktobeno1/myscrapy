import multiprocessing,time

dd = ''
def asd(que):
    
    print dd
    aa = que.get()
    print aa,'asd'
    time.sleep(3)
    if not que.empty():
        asd(que)

def asd1(que):
    print dd
    aa = que.get()
    print aa,'asd1'
    time.sleep(3)
    if not que.empty():
        asd1(que)

if __name__ == '__main__':
    s = multiprocessing.Queue()
    dd = 'hello'
    print dd
    print '123'
    for i in range(10):
        s.put(i)
    print '321'
    p = multiprocessing.Process(target=asd,args=(s,))
    q = multiprocessing.Process(target=asd1,args=(s,))
    p.start()
    q.start()
    p.join()
    
    q.join()
