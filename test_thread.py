#!/usr/bin/python
import time
import threading

class Kiki(threading.Thread):
    def __init__(self, time):
        super(Kiki, self).__init__()
        self.time = time
        self.start()
        #self.join()

    def run(self):
        print "Kiki start."
        time.sleep(self.time)
        print "Kiki done."

# This runs sequentially -- I now understand: the .join() holds the main thread until the joined thread finishes.
thread1 = Kiki(1)
thread1.join()
thread2 = Kiki(3)
thread2.join()
thread3 = Kiki(6)
thread3.join()
thread4 = Kiki(9)
thread4.join()



#From this discussion: http://stackoverflow.com/questions/25165148/python-threading-lock-not-working-in-simple-example
from threading import Thread, Lock
some_var = 0
# lo = Lock() # With the lock here, these don't thread, they are sequential

def some_func(id):
    #lo = Lock() # With the lock here, these thread ok
    #with lo:
        global some_var
        print("{} here!".format(id))
        for i in range(1000000):
            some_var += 1
        print("{} leaving!".format(id))


t1 = Thread(target=some_func, args=(1,))
t2 = Thread(target=some_func, args=(2,))
t3 = Thread(target=some_func, args=(3,))
t4 = Thread(target=some_func, args=(4,))
t1.start()
t2.start()
t3.start()
t4.start()
t1.join()
t2.join()
t3.join()
t4.join()
print(some_var)
