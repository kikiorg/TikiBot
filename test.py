#!/usr/bin/python
#from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import time

#####################
# Bottom Hat motors #
#####################
# Note: The pumps are indexed by the ingredient name
#   range(1,5) means make a set of 5 numbers, 0-indexed, start at 1
#   Keep in mind, 0-index to 5, is [0,1,2,3,4]
#   So starting at 1 means [1,2,3,4]
#   Index #0 is the name "Recipe" so it is skipped
ingr_pumps = {}
ingr_list = ["one", "two", "three", "four"]
temp_ingr_list = iter(ingr_list)
for each_motor in range(1, 5):
#    ingr_pumps[temp_ingr_list.next()] = bottom_hat.getMotor(each_motor)
    ingr_pumps[temp_ingr_list.next()] = "blah"

for each_pump in ingr_pumps:
    print each_pump


import threading

class SummingThread(threading.Thread):
     def __init__(self,low,high):
         super(SummingThread, self).__init__()
         self.low=low
         self.high=high
         self.total=0

     def run(self):
         for i in range(self.low,self.high):
             self.total+=i

class Motors(threading.Thread):
    def __init__(self, motor, ounces):
        super(Motors, self).__init__()
        self.motor = motor
        self.ounces = ounces
        self.start()
        self.join()

    def run(self):
        #self.motor.setSpeed(255)
        #self.motor.run(Adafruit_MotorHAT.FORWARD)
        time.sleep(self.ounces)
        print "Motor done."
        #self.motor.run(Adafruit_MotorHAT.RELEASE)


thread1 = Motors(ingr_pumps["one"],1)
thread2 = Motors(ingr_pumps["two"],3)
thread3 = Motors(ingr_pumps["three"],6)
thread4 = Motors(ingr_pumps["four"],9)
