#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import time
import atexit


# top hat has A0 jumper closed, so its address 0x62.
# Board 2: Address = 0x62 Offset = binary 0010 (bridge A1, the one above A0)
###   top_hat = Adafruit_MotorHAT(addr=0x62)


import threading

class ThreadMe(threading.Thread):
    def __init__(self, motor, time, name):
        # I need only the motor, not the whole list for this.
        # Passing the name, though, assures the key and name match
        super(ThreadMe, self).__init__()
        self.motor = motor
        self.time = time
        self.name = name
        #self.start()
        #self.join()

    def run(self):
        self.motor.setSpeed(255)
        self.motor.run(Adafruit_MotorHAT.FORWARD)
        print self.name + " dispensing now."
        time.sleep(self.time)
        self.motor.run(Adafruit_MotorHAT.RELEASE)


#############################
#  NOTES: PUMP CALIBRATION  #
#############################
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

class LessThanZeroException(Exception):
    pass

class HatNotConnected(Exception):
    pass

class Motors():
    calibration_seconds = 60
    # This pumps should dispense 2oz in calibration_seconds amount of time
    peristaltic_2oz = 2
    # If the calibration value for a pump is 0, then this pump is not calibr$
    not_calibrated = 0
    # This is how long it should take to fill the pump tubing to dispense
    prime_seconds = 2

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

    # top hat has A1 jumper closed, so its address 0x62.
    # Board 1: Address = 0x62 Offset = binary 0010 (bridge A1)
    # top_hat = Adafruit_MotorHAT(addr=0x62)

    # Turn off all motors -- this is registered to run at program exit: atexit.register(turnOffMotors)
    # recommended for auto-disabling motors on shutdown!
    def turnOffMotors(self):
        # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
        for each_motor in range(1, 5):
            Motors.bottom_hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
            Motors.middle_hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
            # Motors.top_hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)

    # Ok, this is sneaky.  We have (possibly) 3 Hats, each with 4 possible pump controllers.
    # As I create more and more pumps, I want to iterate through all the pumps available.
    # I'm going to use a class variable to iterate through them.

    # Motor controllers are numbered [1-4] -- this increments before it's used, so initialized to 0
    next_pump_number = 0
    # Start with the bottom most Hat
    current_hat = bottom_hat
    current_motor = None

    def __init__(self, name, calibration):
        # recommended for auto-disabling motors on shutdown!
        atexit.register(self.turnOffMotors)

        # This is my sneaky code to iterate through all the motors as each is initialized
        # It goes through the 4 pumps for each hat
        if Motors.next_pump_number >= 4:
            Motors.next_pump_number = 1
            if Motors.current_hat == Motors.bottom_hat:
                Motors.current_hat = Motors.middle_hat
                print "Note: now adding pumps from the middle hat."
            elif Motors.current_hat == Motors.middle_hat:
                raise HatNotConnected("Trying to use a Hat at address 0x62!  Does not exist!")
                Motors.current_hat = top_hat
                print "Note: now adding pumps from the top hat."
            else:
                raise HatNotConnected("Trying to use a Hat at address 0x63!  Does not exist!")
        else:
            Motors.next_pump_number += 1
        print "Initializing Motor: ", Motors.next_pump_number
        Motors.current_motor = Motors.current_hat.getMotor(Motors.next_pump_number)
        self.motor = Motors.current_motor
        self.name = name
        # If the calibration == not_calibrated, it will run a calibration
        # Note: not-calibrated is generally 0 (will not dispense!), so don't just copy this into self!
        self.calibration = self.calibrate_pump(calibration)

    # This returns the best calibration value.
    # If the calibration was not set in the .csv file, then ask the user to calibrate the pump
    # If the pump needs to be calibrated, it dispenses for calibration_seconds (probably 2),
    # then asks for the amount actually dispensed.
    # It then calculates a normalized 1oz dispense rate.
    def calibrate_pump(self, calibration):
        if calibration == self.not_calibrated:
            yesno = raw_input("Do you want to calibrate pump for " + self.name + "?")
            if yesno == "yes":
                self.dispense(Motors.calibration_seconds)
                new_factor = raw_input("How much liquid was delivered?")
                return float(1 / new_factor * Motors.calibration_seconds)
                print "Note: please change the value in your .csv file for " + name
            else:
                print "Well...ok, but that means I'll enter a standard 2oz for this pump and it will be inaccurate!"
                return float(1 / Motors.peristaltic_2oz * Motors.calibration_seconds)
        else:
            return float(calibration)

    # This primes the pump.  It assumes the lines are totally empty, but also allows the user to
    # kick the pump by 1/10ths too.
    def prime(self):
        my_thread = ThreadMe(self.motor, Motors.prime_seconds, self.name)

        answer = raw_input("More?")
        while answer == "y":
            my_thread = ThreadMe(self.motor, Motors.prime_seconds / 10, self.name)
            answer = raw_input("More? [y/n]")

    # Dispense the ingredients!  ounces is in ounces, multiplied by the calibration time for 1oz
    def dispense(self, ounces, my_thread):
        # self.calibration is multiplied by the ounces to find the time to run the pump -- must be >0
        # Note: this should always be true, but being safe here!
        if self.calibration <= 0:
            raise LessThanZeroException(self.name + ' - calibration:' + str(self.calibration) + ' Must be >0 for motors to run!')
        my_thread = ThreadMe(self.motor, ounces * self.calibration, self.name)
        my_thread.start()
        my_thread.join()
        # print "Finished dispensing ", ounces, " of ", self.name, "."
