#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import time
import atexit


############################################
# Initialize the motors on the Bot         #
############################################
# Set up the address for each of the pumps #
# NOTE: Since we don't have all 3 hats,    #
#   I've commented out for the other       #
#   two boards, until they come in         #
############################################

############################################
# Initialize the motors on the Bot         #
############################################
# Set up the address for each of the pumps #
# NOTE: Since we don't have all 3 hats,    #
#   I've commented out for the other       #
#   two boards, until they come in         #
############################################

# bottom hat is default address 0x60
# Board 0: Address = 0x60 Offset = binary 0000 (no jumpers required)
bottom_hat = Adafruit_MotorHAT(addr=0x60)

# middle hat has A0 jumper closed, so its address 0x61.
# Board 1: Address = 0x61 Offset = binary 0001 (bridge A0)
middle_hat = Adafruit_MotorHAT(addr=0x61)


# top hat has A0 jumper closed, so its address 0x62.
# Board 2: Address = 0x62 Offset = binary 0010 (bridge A1, the one above A0)
###   top_hat = Adafruit_MotorHAT(addr=0x62)

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    bottom_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)


# middle_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

#####################
# Bottom Hat motors #
#####################
# Note: The pumps are indexed by the ingredient name
#   range(1,5) means make a set of 5 numbers, 0-indexed, start at 1
#   Keep in mind, 0-index to 5, is [0,1,2,3,4]
#   So starting at 1 means [1,2,3,4]
#   Index #0 is the name "Recipe" so it is skipped


#####################
# PUMP CALIBRATION  #
#####################

# OLD CODE!!!  REMOVE WHEN DONE!!!
# This is the calibration for how long to run the pump for 1 ounce
# Note: The drink calibration factor is the number of ounces delivered in 60 seconds -- around 2oz
# Thus, drinks["Calibration"][each_ingredient] should be near to 2oz, the amount that pump delivered in 60 seconds
# In short, the calibration_factor for each pump is multiplied by the number of ounces delivered for that drink
#def calibrate_pump(pump):
#    pump.setSpeed(255)
#    pump.run(Adafruit_MotorHAT.FORWARD)
#    time.sleep(calibration_seconds)
#    pump.run(Adafruit_MotorHAT.RELEASE)
#    print "60 seconds of run have been delivered."
#    print "Please enter into your calibration line the exact amount just dispensed."



import threading

class ThreadMe(threading.Thread):
    def __init__(self, motor_list, time, name):
        # I need only the motor, not the whole list for this.
        # Passing the name, though, assures the key and name match
        super(ThreadMe, self).__init__()
        self.motor = motor_list[name]
        self.time = time
        self.name = name
        self.start()
        self.join()

    def run(self):
        self.motor.setSpeed(255)
        self.motor.run(Adafruit_MotorHAT.FORWARD)
        time.sleep(self.time)
        print self.name + " finished dispensing."
        self.motor.run(Adafruit_MotorHAT.RELEASE)

############################
#  PUMP CALIBRATION TABLE  #
############################
# This is a standardized calibration table.
# To pump 1 ounce, you run each pump approximately this amount.
# The way the rest of the calibration code works, is you run the pump this amount
# Then enter how many ounces you *actually* got from that run.
# The real time to run the pump is then Normalized against this number.
#
# formula: time = ounces * factor
# factor = initial_calibration_factor
# 2 ounces = normalized time
# normalized time = initial time
# normalized ounces = ounces expected / ounces delivered
#
# We calibrate against 2 ounces -- the larger amount we calibrate against, the more accurate.
# 2 ounces delivers decent accuracy, while not waiting too long for it to finish.
# So we run the pump for 60 seconds and measure the actual ounces delivered -- which should be close to 2 ounces.
# We simply enter the actual ounces delivered into the calibration "drink".
#
# Here's the calibration formula:
# 2oz = about 60 seconds -- but it isn't
# 60 seconds = X ounces
# 2oz/Xoz * 60 = accurate 2oz -- my original formula
# 2oz/Xoz * 60 / 2oz = accurate 1oz -- scaled to 1oz
# 1oz/Xoz * 60 = accurate 1oz -- complete normalized formula

class Motors():
    calibration_seconds = 60
    # This pumps should dispense 2oz in calibration_seconds amount of time
    peristaltic_2oz = 2
    # If the calibration value for a pump is 0, then this pump is not calibr$
    not_calibrated = 0
    # This is how long it should take to fill the pump tubing to dispense
    prime_seconds = 2

    # Ok, this is sneaky.  We have (possibly) 3 Hats, each with 4 possible pump controllers.
    # As I create more and more pumps, I want to iterate through all the pumps available.
    # I'm going to use a class variable to iterate through them.

    # Motor controllers are numbered [1-4]
    next_pump_number = 1
    # Start with the bottom most Hat
    current_motor = bottom_hat.getMotor(next_pump_number)

    def __init__(self, name, calibration):
        self.motor = Motors.current_motor
        self.name = name
        self.calibration = self.calibrate_pump(calibration)


    # This returns the best calibration value.
    # If the calibration was not set in the .csv file, then ask the user to calibrate the pump
    # If the pump needs to be calibrated, it dispenses for 2 seconds, then asks for the amount actuall dispensed.
    # It then calculates a normalized 1oz dispense rate.
    def calibrate_pump(self, calibration):
        if calibration == self.not_calibrated:
            yesno = raw_input("Do you want to calibrate pump for " + self.name + "?")
            if yesno == "yes":
                self.calibrate()
                new_factor = raw_input("How much liquid was delivered?")
                return 1 / float(new_factor) * Motors.calibration_seconds
                print "Note: please change the value in your .csv file for " + name
            else:
                print "Well...ok, but that means I'll enter a standard 2oz for this pump and it will be inaccurate!"
                return 1 / 2 * Motors.calibration_seconds
        else:
            return calibration

    # Define primeMe code
    def prime(self):
        my_thread = ThreadMe(self.motor, Motors.prime_seconds, self.name)

        answer = raw_input("More?")
        while answer == "y":
            my_thread = ThreadMe(self.motor, Motors.prime_seconds / 10, self.name)
            answer = raw_input("More? [y/n]")

    def dispense(self, ounces):
        my_thread = ThreadMe(self.motor, ounces * self.calibration, self.name)

    def calibrate(self):
        my_thread = ThreadMe(self.motor, Motors.calibration_seconds, self.name)
