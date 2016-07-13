#!/usr/bin/python

# This forces using the local library, which has been modified
import sys
sys.path.insert(1, "Adafruit-Motor-HAT-Python-Library")
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# Motors class:                             #
#############################################
# This class handles the motors:
#   It addresses and connects with the RasPi Hats
#   Executes all the turning on and off of the motors using threading
#   It handles priming and calibrating functions for a single pump
# This class is the hardware interface with the rest of the code
#############################################

# Needed to sleep-wait for motor to finish running.
import time
# Needed to assure all motors have been turned off if the program ends.
# Motors have a state either on or off.
import atexit

# Allows motors to run concurrently
import threading
from yesno import yesno

# Notes for pump calibration:

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


############################################################################
# Generalized Motors class for using Adafruit Motor Hats on a Raspberry Pi #
############################################################################
# This class is for simple output controlling for Motor Hats
# This ignores the center pin, and assumes 4 simple motors
class Motors():
    ############################################
    # Find all Hats on the Raspberry Pi
    # --------
    # Hats in the RasPi are addressed by soldering jumpers on the Hat board.
    # There are 4 jumpers, and make addresses in binary fashion: 00001=0x60, 00010=0x61, 00011=0x62 etc
    # This code tries them all, and if one is found, it is appended to the list of valid Hats
    hat_stack = []
    for Hat_address in range(0x60, 0x70):
        try:
            temp_hat = Adafruit_MotorHAT(Hat_address)
        except IOError as error_msg:
            #raise IOError (error_msg.message + ' happens at % Motors.py')
            #print "No Hat at address: ", Hat_address
            pass
        else:
            # print "Found Hat_address: 0x{0:x}".format(temp_hat._i2caddr)
            hat_stack.append(temp_hat)
    ############################################
    # Sequential initializing of all the motors on all valid Hats
    next_motor_number = 0 # Note: this is incremented before using
    motors_on_each_Hat = 4 # Number of simple motors on each Hat
    # Start with the bottom most Hat
    hat_cycle = iter(hat_stack)
    current_hat = hat_cycle.next()
    all_hats = Adafruit_MotorHAT(addr=0x70)  # Not used, but should address all hats at once

    ############################################
    # Pump calibration constants
    # We assume these are pumps that dispense about 2oz every 60 seconds.
    # calibration_default = 2.0
    # calibration_seconds = 60.0
    # This is how long it should take to fill the pump tubing to dispense -- no longer, so none is wasted
    # prime_ounces_default = 0.40
    # The motors spike in current for about this amount of time -- don't start all motors at the same time
    current_spike_stabilze = 0.1

    my_yesno = yesno() # Handy little class for user input


    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # This gives each motor a name, and a calibration value, and initializes a member for the thread
    # This gets the next motor in line of all the Hats
    def __init__(self, name, force_motor_number = 0, force_next_Hat = False): #, calibration_oz = calibration_default):
        self.name = name
        self.thread = None
        self.motor = self.get_next_motor(force_motor_number, force_next_Hat)

        # recommended for auto-disabling motors on shutdown
        # Note: does not work if there's a segfault
        atexit.register(self.turnOffMotors)

    ############################################
    # Cycle through all available motors
    ############################################
    # Go through all motors, then switch to the next Hat, in order
    # Note: override this for other classes of motors, eg Stepper Motors
    def get_next_motor(self, force_motor_number = 0, force_next_Hat = False):
        if force_motor_number > 0 and force_motor_number <= Motors.motors_on_each_Hat:
            print "FORCED MOTOR: ", force_motor_number
            if force_next_Hat:
                print "FORCED NEW HAT: ", force_next_Hat
                Motors.current_hat = Motors.hat_cycle.next()
            return Motors.current_hat.getMotor(force_motor_number)
        else:
            Motors.next_motor_number += 1
            if Motors.next_motor_number > Motors.motors_on_each_Hat:
                # Reset the motor number
                Motors.next_motor_number = 1
                # Move to the next Hat
                try:
                    Motors.current_hat = Motors.hat_cycle.next()
                    # print "i2caddr: {} motor#: {}".format(Motors.current_hat._i2caddr, Motors.next_motor_number)
                except:
                    raise HatNotConnected("Attempt to address more Hats than exist with name {}".format(self.name))
                    return None
            return Motors.current_hat.getMotor(Motors.next_motor_number)

    #############################################
    # Run each motor for 1sec for testing
    #############################################
    def test_all_motors(self):
        # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
        for each_hat in Motors.hat_stack:
            for each_motor in range(1, Motors.motors_on_each_Hat):
                try:
                    Motors.hat_stack[each_hat].getMotor(each_motor).run(Adafruit_MotorHAT.FORWARD)
                    print "Testing Hat: ", each_hat._i2caddr, " and Motor: ", each_motor
                    time.sleep(1)
                    Motors.hat_stack[each_hat].getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
                except:  # Not all motors in all Hats will be available
                    print "Nonexistant motor: #{} in HAT: {}".format(each_motor, each_hat._i2caddr)

    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # Turn off all motors -- this is registered to run at program exit: atexit.register(turnOffMotors)
    # recommended for auto-disabling motors on shutdown!
    def turnOffMotors(self):
        # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
        for each_Hat in Motors.hat_stack:
            for each_motor in range(1, Motors.motors_on_each_Hat):
                try:
                    each_Hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
                except:  # Not all motors in all Hats will be available
                    print "Nonexistant motor: #", each_motor

    ############################################
    # Turn effect on and leave it on           #
    ############################################
    # Treat motor as output
    def turn_on_effect(self, forwards = True):
        self.motor.setSpeed(255)
        # print "Effect turned on: {} going: {}".format(self.name, "forwards" if forwards else "backwards")
        if forwards:
            self.motor.run(Adafruit_MotorHAT.FORWARD)
        else:
            self.motor.run(Adafruit_MotorHAT.BACKWARD)

    ############################################
    # Turn effect off                          #
    ############################################
    # Treat motor as output
    def turn_off_effect(self):
        # print "Effect turned off: {}".format(self.name)
        self.motor.run(Adafruit_MotorHAT.RELEASE)

    ######################################################
    # Thread: Run effect for a certain amount of seconds #
    ######################################################
    # Treat motor as output
    def thread_effect_for_time(self, time = 5, forwards = True):
        self.thread = Motors.ThreadMotor(self.thread_for_time_run, self.motor, time, forwards)

    ####################################################
    # Thread: Ramp the effect up or down using PWM     #
    ####################################################
    # Treat motor as output
    def thread_effect_ramp(self, ramp_up = True, forwards = True, step = 2):
        self.thread = Motors.ThreadMotor(self.thread_ramp_run, self.motor, self.name, ramp_up, forwards, step)

    ############################################
    # Wait until threading is done             #
    ############################################
    # This is important: .join() attaches the thread back to the main thread -- essentally un-threading it.
    # It causes the main program to wait until the motor has completed before it moves on to the next drink.
    # The upshot is that you have to separate the .join() function from the .start() function, so all
    # motors get started first. If you .start() then immediately .join(), then the motors will run one after the other
    # instead of all at once.  .join() must be run for every motor *after* all the motors have started.
    def wait_until_done(self):
        self.thread.join()

    ############################################
    # Run the motor for a certain time         #
    ############################################
    # Function to be used with threading
    def thread_for_time_run(self, motor, run_time, forwards = True):
        motor.setSpeed(255)
        if forwards:
            motor.run(Adafruit_MotorHAT.FORWARD)
        else:
            motor.run(Adafruit_MotorHAT.BACKWARD)
        time.sleep(run_time)
        motor.run(Adafruit_MotorHAT.RELEASE)

    ############################################
    # Ramp the motor speed up -- like a fade   #
    ############################################
    # Function to be used with threading
    def thread_ramp_run(self, motor, name, ramp_up = True, forwards = True, step = 2):
        # Slowly raise or lower the speed of the motor.
        # The wait is simply how long the loop takes.
        for i in range(0 if ramp_up else 255, 255 if ramp_up else -1, step if ramp_up else (-step)):
            motor.setSpeed(i)
            motor.run(Adafruit_MotorHAT.FORWARD if forwards else Adafruit_MotorHAT.BACKWARD)
        if not ramp_up:
            motor.run(Adafruit_MotorHAT.RELEASE)

    #############################################
    # ThreadMotor class:                        #
    #############################################
    # This class allows the motors to all run at the same time.
    # If we didn't, it would take a very long time to make one cocktail!
    #############################################
    class ThreadMotor(threading.Thread):
        # motor = which motor by ref; time = actual time to run; name = name assigned to motor
        def __init__(self, my_function, *my_args):
            # I need only the motor, not the whole list for this.
            # Passing the name, though, assures the key and name match
            super(Motors.ThreadMotor, self).__init__()
            self.thread_function = my_function
            self.function_args = my_args
            self.start()

        # Run the assigned function in a thread
        def run(self):
            self.thread_function(*self.function_args)


