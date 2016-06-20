#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

# Needed to sleep-wait for pump to finish dispensing.
import time
# Needed to assure all pumps have been turned off if the program ends.
# Pumps have a state either on or off.
import atexit

import threading


class ThreadMe(threading.Thread):
    def __init__(self, motor, time, name):
        # I need only the motor, not the whole list for this.
        # Passing the name, though, assures the key and name match
        super(ThreadMe, self).__init__()
        self.motor = motor
        self.time = time
        self.name = name
        self.start()
        # self.join() # Oops, this immediately stops the main thread and waits for your thread to finish

    def run(self):
        self.motor.setSpeed(255)
        self.motor.run(Adafruit_MotorHAT.FORWARD)
        # print self.name + " Kiki dispensing now for", self.time, "seconds."
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


############################################
# Initialize the motors on the Bot         #
############################################
# Set up the address for each of the pumps #
# NOTE: Since we don't have all 3 hats,    #
#   I've commented out for the other       #
#   two boards, until they come in         #
############################################

# self.__modulations = (nfc.nfc_modulation * len(mods))()
# for i in range(len(mods)):
#    self.__modulations[i].nmt = mods[i][0]
#    self.__modulations[i].nbr = mods[i][1]

hat_stack = []
# bottom hat is default address 0x60
# Board 0: Address = 0x60 Offset = binary 0000 (no jumpers required)
hat_stack.append(Adafruit_MotorHAT(addr=0x60))

# middle hat has A0 jumper closed, so its address 0x61.
# Board 1: Address = 0x61 Offset = binary 0001 (bridge A0)
hat_stack.append(Adafruit_MotorHAT(addr=0x61))
# hat_stack[1] = Adafruit_MotorHAT(addr=0x61)

# top hat has A1 jumper closed, so its address 0x62.
# Board 1: Address = 0x62 Offset = binary 0010 (bridge A1)
hat_stack.append(Adafruit_MotorHAT(addr=0x62))
# hat_stack[2] = Adafruit_MotorHAT(addr=0x62)

all_hats = Adafruit_MotorHAT(addr=0x70)  # Not used, but should address all hats at once


# Quick test of all motors -- this turns them all on for one second
def test_all_motors():
    # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
    for each_hat in range(3):
        for each_motor in range(1, 5):
            hat_stack[each_hat].getMotor(each_motor).run(Adafruit_MotorHAT.FORWARD)
            print "Testing Hat: ", each_hat, " and Motor: ", each_motor
            time.sleep(1)
            hat_stack[each_hat].getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)


# Turn off all motors -- this is registered to run at program exit: atexit.register(turnOffMotors)
# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
    for each_motor in range(1, 5):
        hat_stack[0].getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
        hat_stack[1].getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
        hat_stack[2].getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
        # Motors.top_hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)


# recommended for auto-disabling motors on shutdown!
atexit.register(turnOffMotors)


class Motors():
    # We assume these are pumps that dispense about 2oz every 60 seconds.
    peristaltic_2oz = 2
    calibration_seconds = 60
    # If the calibration value for a pump is 0, then this pump is not calibrated
    not_calibrated = 0.0
    # This is how long it should take to fill the pump tubing to dispense
    prime_seconds = 10
    # The pumps spike in current for about this amount of time.
    # This is used between pump startups so there's not a massive current spike
    # from all pumps starting at once.
    current_spike_stabilze = 0.1

    # Ok, this is sneaky.  We have (possibly) 3 Hats, each with 4 possible pump controllers.
    # As I create more and more ingredient pumps, I want to iterate through all the pumps available.
    # I'm going to use a class variable to iterate through them.

    # Motor controllers are numbered [1-4] -- this increments before it's first used, so initialized to 0
    next_pump_number = 0
    # Start with the bottom most Hat
    current_hat = hat_stack[0]
    # Kiki remove this or fix it
    calibration_string = ""

    def __init__(self, name, calibration):
        # This is my sneaky code to iterate through all the motors as each is initialized
        # It goes through the 4 pumps for each hat
        if Motors.next_pump_number >= 4:
            Motors.next_pump_number = 1
            if Motors.current_hat == hat_stack[0]:
                Motors.current_hat = hat_stack[1]
                # print "Note: now adding pumps from the middle hat."
            elif Motors.current_hat == hat_stack[1]:
                Motors.current_hat = hat_stack[2]
                # print "Note: now adding pumps from the top hat."
            elif Motors.current_hat == hat_stack[2]:
                raise HatNotConnected("Trying to use a Hat at address 0x63!  Does not exist!")
                # Motors.current_hat = top_hat
                # print "Note: now adding pumps from the top hat."
            else:
                raise HatNotConnected("Trying to use a Hat beyond address 0x63!  Does not exist!")
        else:
            Motors.next_pump_number += 1
        self.motor = Motors.current_hat.getMotor(Motors.next_pump_number)
        # print "Current motor: ", self.motor
        self.name = name
        self.thread = None
        # Quick test of each motor --Kiki
        # self.motor.run(Adafruit_MotorHAT.FORWARD)
        # time.sleep(1)
        # self.motor.run(Adafruit_MotorHAT.RELEASE)

        # If the calibration == not_calibrated, it will run a calibration
        # Note: not-calibrated is generally 0.0 (will not dispense!), so don't just copy this into self!
        # Note: calibration was not always a float, so we must force it
        # The problem arises when 0.0 == 0 is false.
        self.calibration = 0.0
        self.calibration = self.calibrate_pump(float(calibration))

    # This returns the best calibration value.
    # If the calibration was not set in the .csv file, then ask the user to calibrate the pump
    # If the pump needs to be calibrated, it dispenses for calibration_seconds (probably 2),
    # then asks for the amount actually dispensed.
    # It then calculates a normalized 1oz dispense rate.
    def calibrate_pump(self, calibration):
        if calibration == self.not_calibrated:
            yesno = raw_input("Do you want to calibrate pump for " + self.name + "? ")
            if yesno in ["yes", "y", "Y", "YES"]:
                # Must assign some kind of calibration value before dispensing -- default is peristaltic_2oz
                self.calibration = float(1.0 / Motors.peristaltic_2oz * Motors.calibration_seconds)
                self.dispense(Motors.peristaltic_2oz)
                self.wait_until_done()
                amount_dispensed = raw_input("How much liquid was delivered? ")
                # 1oz / actual oz = X seconds / actual dispense time
                # solve for X -- which is the time it really should run to dispense 1oz
                # X seconds = 1oz/actual oz * actual dispense time
                # So now to dispense, say, 1.5oz, you multiply 1.5 * X to equal the seconds to run
                new_factor = float(1.0 / float(amount_dispensed) * Motors.calibration_seconds)
                print "New factor ", new_factor
                Motors.calibration_string += str(amount_dispensed) + ","
                return new_factor
            else:
                print "Well...ok, but that means I'll enter a standard ", Motors.peristaltic_2oz, " for this pump and it will be inaccurate!"
                new_factor = float(1.0 / Motors.peristaltic_2oz * Motors.calibration_seconds)
                return new_factor
        else:
            new_factor = float(1.0 / calibration * Motors.calibration_seconds)
            return new_factor

    # This primes the pump.  It assumes the tubing is totally empty, but also allows the user to
    # kick the pump by 1/10ths too.
    def prime(self):
        self.thread = ThreadMe(self.motor, Motors.prime_seconds, self.name)
        self.thread.join()  # Wait until pump is done before continuing

        answer = raw_input("More?")
        while answer == "y":
            my_thread = ThreadMe(self.motor, Motors.prime_seconds / 10, self.name)
            answer = raw_input("More? [y/n]")

    # Dispense the ingredients!  ounces is in ounces, multiplied by the calibration time for 1oz
    def dispense(self, ounces):
        # self.calibration is multiplied by the ounces to find the time to run the pump -- must be >0
        # Note: this should always be true, but being safe here!
        if self.calibration <= 0.0:
            raise LessThanZeroException(
                self.name + ' - calibration:' + str(self.calibration) + ' Must be >0 for motors to run!')
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        # The pumps are run as processor threads, so all pumps can run concurrently.
        # print "Kiki Disepensing for this seconds: ", ounces * self.calibration, " name: ", self.name
        # print "Kiki ounces: ", ounces , " calibration factor: ", self.calibration, " name: ", self.name
        self.thread = ThreadMe(self.motor, ounces * self.calibration, self.name)
        # print "Finished dispensing ", ounces, " of ", self.name, "."

    # This is important: .join() attaches the thread back to the main thread -- essentally un-threading it.
    # It causes the main program to wait until the pump has completed before it moves on to the next drink.
    # The upshot is that you have to separate the .join() function from the .start() function, so all
    # pumps get started first. If you .start() then immediately .join(), then the pumps will run one after the other
    # instead of all at once.  .join() must be run for every pump *after* all the pumps have started.
    def wait_until_done(self):
        self.thread.join()
