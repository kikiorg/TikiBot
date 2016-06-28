#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# Motors class:                             #
#############################################
# This class handles the motors:
#   It addresses and connects with the RasPi Hats
#   Executes all the turning on and off of the pumps using threading
#   It handles priming and calibrating functions for a single pump
# This class is the hardware interface with the rest of the code
#############################################

# Needed to sleep-wait for pump to finish dispensing.
import time
# Needed to assure all pumps have been turned off if the program ends.
# Pumps have a state either on or off.
import atexit

import threading
from yesno import yesno

#############################################
# ThreadMe class:                             #
#############################################
# This class allows the pumps to all run ath the same time.
# If we didn't, it would take a very long time to make one cocktail!
#############################################
class ThreadMe(threading.Thread):
    # motor = which motor by ref; time = actual time to run; name = name assigned to pump
    def __init__(self, motor, time, name, forwards = True):
        # I need only the motor, not the whole list for this.
        # Passing the name, though, assures the key and name match
        super(ThreadMe, self).__init__()
        self.motor = motor
        self.time = time
        self.name = name
        self.forwards = forwards
        self.start()

    def run(self):
        self.motor.setSpeed(255)
        if self.forwards:
            self.motor.run(Adafruit_MotorHAT.FORWARD)
        else:
            self.motor.run(Adafruit_MotorHAT.BACKWARD)
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

hat_stack = []
# bottom Hat: Board 0: Address = 0x60 Offset = binary 0000 (no jumpers required)
# middle Hat: Board 1: Address = 0x61 Offset = binary 0001 (bridge A0)
# top Hat: Board 1: Address = 0x62 Offset = binary 0010 (bridge A1)
hat_stack.append(Adafruit_MotorHAT(addr=0x60))
hat_stack.append(Adafruit_MotorHAT(addr=0x61))
hat_stack.append(Adafruit_MotorHAT(addr=0x62))

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
    calibration_default = 2.0
    calibration_seconds = 60.0
    # This is how long it should take to fill the pump tubing to dispense -- no longer, so none is wasted
    prime_seconds_default = 13
    # Reverse purge a little longer to be sure the tube is completely purged
    purge_seconds_default = 17
    # The pumps spike in current for about this amount of time.
    # This is used between pump startups so there's not a massive current spike
    # from all pumps starting at once.
    current_spike_stabilze = 0.1
    my_yesno = yesno() # Handy little class for user input

    # Ok, this is sneaky.  We have (possibly) 3 Hats, each with 4 possible pump controllers.
    # As I create more and more ingredient pumps, I want to iterate through all the pumps available.
    # I'm going to use a class variable to iterate through them.

    # Motor controllers are numbered [1-4] -- this increments before it's first used, so initialized to 0
    next_pump_number = 0
    # Start with the bottom most Hat
    current_hat = hat_stack[0]

    def __init__(self, name, calibration_oz = calibration_default):
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
        # Change June 20, 2016: Changedthe function of the calibration factor
        #   Now the factor is calculated in one place: dispense, and if no calibration is provided, it uses a default
        self.calibration_oz = calibration_oz


    # If the pump needs to be calibrated, it dispenses for calibration_seconds (probably 2),
    # then asks for the amount actually dispensed.
    # It then calculates a normalized 1oz dispense rate.
    def force_calibrate_pump(self):
        # Must assign some kind of calibration value before dispensing -- default is calibration_default
        print "Old calibration ounces: ", self.calibration_oz
        self.dispense(Motors.calibration_default) # Dispense a calibrated 2.0oz and see if it's correct.  If so, make no changes.
        self.wait_until_done()
        amount_dispensed = self.my_yesno.get_number(message="How much liquid was delivered [press Enter if exactly 2.0]? : ", default_val=2.0)

        # This is where things get tricky: we now have to reverse engineer the actual ounces
        # Let's say, given the current calibration, 2oz should be 2oz:
        # 2oz theory / 2oz actual = X * (formula) * 2oz / (formula) * 2oz
        # Test this formula with numbers:
        # last dispensed 2.5oz in 60 seconds, formula = 1oz/2.5oz*60sec = ~24sec
        # now dispenses 2.7 in 60 seconds, so now it dispenses more
        # 2oz theory / 2oz actual = X
        self.calibration_oz = self.calibration_oz * (float(amount_dispensed) / Motors.calibration_default)
        print "Adjusted amount for " + self.name + ":" + str(self.calibration_oz)
        print "Factor: " + str(float(
            amount_dispensed) / Motors.calibration_default)  # Note: it's more useful to return the actual amount dispensed, not the calibration number, because
        #   you can find that here: self.calibration_oz
        return amount_dispensed



    # This primes the pump.  It assumes the tubing is totally empty, but also allows the user to
    # kick the pump by 1/10ths too.
    def prime(self, prime_value=0.0):
        if prime_value == 0.0:
            prime_value = Motors.prime_seconds_default
        elif prime_value < 0.0:
            print "Invalid prime value!  Less than zero!  Using default: ", Motors.prime_seconds_default
            prime_value = Motors.prime_seconds_default
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        self.thread = ThreadMe(self.motor, prime_value, self.name)

    def reverse_purge(self, my_purge_seconds = purge_seconds_default):
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        self.thread = ThreadMe(self.motor, my_purge_seconds, self.name, forwards = False)
    def forward_purge(self, my_purge_seconds = purge_seconds_default):
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        self.thread = ThreadMe(self.motor, my_purge_seconds, self.name)

    # Dispense the ingredients!  ounces is in ounces, multiplied by the calibration time for 1oz
    def dispense(self, ounces):
        # Formala: 1oz / actual oz dispensed in 60 seconds = time for 1oz / 60 seconds -- solve for time for 1oz
        #          1oz / calibration_oz = X / Motors.calibration_seconds
        # Or:      time for one ounce = 1oz / actual oz dispensed in 60 seconds * 60 seconds
        #          calibrated_time = 1oz / calibration_oz * Motors.calibration_seconds
        # Multiply X times ounces for the actual time for those calibrated ounces
        calibrated_time = float(float(ounces) / self.calibration_oz * Motors.calibration_seconds)
        # Note: this should always be true, but being safe here!
        if calibrated_time <= 0.0:
            raise LessThanZeroException(
                self.name + ' - calibration:' + str(self.calibration_oz) + ' Must be >0 for motors to run!')
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        # The pumps are run as processor threads, so all pumps can run concurrently.
        self.thread = ThreadMe(self.motor, calibrated_time, self.name)
        # print "Finished dispensing ", ounces, " of ", self.name, "."

    # This is important: .join() attaches the thread back to the main thread -- essentally un-threading it.
    # It causes the main program to wait until the pump has completed before it moves on to the next drink.
    # The upshot is that you have to separate the .join() function from the .start() function, so all
    # pumps get started first. If you .start() then immediately .join(), then the pumps will run one after the other
    # instead of all at once.  .join() must be run for every pump *after* all the pumps have started.
    def wait_until_done(self):
        self.thread.join()
