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
    calibration_default = 2.0
    calibration_seconds = 60.0
    # This is how long it should take to fill the pump tubing to dispense -- no longer, so none is wasted
    prime_ounces_default = 0.40
    # The motors spike in current for about this amount of time -- don't start all motors at the same time
    current_spike_stabilze = 0.1

    my_yesno = yesno() # Handy little class for user input


    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # This gives each motor a name, and a calibration value, and initializes a member for the thread
    # This gets the next motor in line of all the Hats
    def __init__(self, name, calibration_oz = calibration_default):
        self.name = name
        self.thread = None
        self.motor = self.get_next_motor()
        # Each motor should dispense 2oz in 60 seconds (is should dispense calibration_default in calibration_seconds)
        # But, of course, they vary.
        # This is the actual amount this particular motor dispenses in calibration_seconds
        #   See .dispense for the Magic of Math for how it uses this numbers to calibrate the motor
        self.calibration_oz = calibration_oz

        # recommended for auto-disabling motors on shutdown
        # Note: does not work if there's a segfault
        atexit.register(self.turnOffMotors)

    ############################################
    # Cycle through all available motors
    ############################################
    # Go through all motors, then switch to the next Hat, in order
    # Note: override this for other classes of motors, eg Stepper Motors
    def get_next_motor(self):
        Motors.next_motor_number += 1
        if Motors.next_motor_number > Motors.motors_on_each_Hat:
            # Reset the motor number
            Motors.next_motor_number = 1
            # Move to the next Hat
            try:
                Motors.current_hat = Motors.hat_cycle.next()
                # print "i2caddr: {0:0x}".format(Motors.current_hat._i2caddr)
            except:
                raise HatNotConnected("Attempt to address more Hats than exist")
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
    # Calibrate pump                           #
    ############################################
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
        print "Factor: " + str(float(amount_dispensed) / Motors.calibration_default)
        # Note: it's more useful to return the actual amount dispensed, not the calibration number, because
        #   the parent can find that here: self.calibration_oz
        return amount_dispensed

    ############################################
    # Prime pump                               #
    ############################################
    # This primes the pump.  It assumes the tubing is totally empty, but also allows the user to
    # kick the pump by 1/10ths too.
    def prime(self, prime_value=0.0):
        if prime_value == 0.0:
            prime_value = Motors.prime_ounces_default
        elif prime_value < 0.0:
            print "Invalid prime value!  Less than zero!  Using default: ", Motors.prime_ounces_default
            prime_value = Motors.prime_ounces_default
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Motors.current_spike_stabilze)
        self.thread = ThreadMotor(self.motor, prime_value, self.name)

    ############################################
    # Dispense calibrated ounces               #
    ############################################
    # Dispense the ingredients!  ounces is in ounces, multiplied by the calibration time for 1oz
    def dispense(self, ounces, forwards = True):
        # Formala:       1oz / actual oz dispensed in 60 seconds = time for 1oz / 60 seconds
        #                1oz / calibration_oz = X / Motors.calibration_seconds
        # Solve for X:   time for one ounce = 1oz / actual oz dispensed in 60 seconds * 60 seconds
        #                calibrated_time = 1oz / calibration_oz * Motors.calibration_seconds
        # Multiply X times ounces for the actual time for those calibrated ounces
        calibrated_time = float(float(ounces) / self.calibration_oz * Motors.calibration_seconds)
        # Note: this should always be true, but being safe here!
        if calibrated_time <= 0.0:
            raise LessThanZeroException(
                self.name + ' - calibration:' + str(self.calibration_oz) + ' Must be >0 for motors to run!')
        # Delay to stabilize the current spike on motor startup.
        time.sleep(Motors.current_spike_stabilze)
        # The pumps are run as processor threads, so all pumps can run concurrently.
        self.thread = Motors.ThreadMotor(self.thread_for_time_run, self.motor, calibrated_time, forwards)
        # print "Finished dispensing ", ounces, " of ", self.name, "."

    ############################################
    # Turn effect on and leave it on           #
    ############################################
    # Treat motor as output
    def turn_on_effect(self, forwards = True):
        self.motor.setSpeed(255)
        if forwards:
            self.motor.run(Adafruit_MotorHAT.FORWARD)
        else:
            self.motor.run(Adafruit_MotorHAT.BACKWARD)

    ############################################
    # Turn effect off                          #
    ############################################
    # Treat motor as output
    def turn_off_effect(self):
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


