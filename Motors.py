#!/usr/bin/python

# Needed to sleep-wait for motor to finish running.
import time
# Needed to assure all motors have been turned off if the program ends.
# Motors have a state either on or off.
import atexit

# Allows motors to run concurrently
import threading
# For random flashing
from random import randint

from yesno import yesno
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


############################################################################
# Generalized Motors class for using Adafruit Motor Hats on a Raspberry Pi #
############################################################################
# This class is for simple output controlling for Motor Hats
# This ignores the center pin, and assumes 4 simple motors
class Motors:
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
            # This raise will happen for EVERY address with no Hat -- not needed unless you are full! :)
            # raise IOError (error_msg.message + ' happens at % Motors.py')
            pass
        else:
            # print "Found Hat_address: 0x{0:x}".format(temp_hat._i2caddr)
            hat_stack.append(temp_hat)
    ############################################
    # Sequential initializing of all the motors on all valid Hats
    next_motor_number = 0  # Note: this is incremented before using
    motors_on_each_Hat = 4  # Number of simple motors on each Hat
    # Start with the bottom most Hat
    hat_cycle = iter(hat_stack)
    current_hat = hat_cycle.next()
    all_hats = Adafruit_MotorHAT(addr=0x70)  # Not used, but should address all hats at once

    # The motors spike in current for about this amount of time -- don't start all motors at the same time
    current_spike_stabilize = 0.1

    my_yesno = yesno()  # Handy little class for user input

    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # This gives each motor a name, and a calibration value, and initializes a member for the thread
    # This gets the next motor in line of all the Hats
    def __init__(self, name, force_motor_number=0, force_next_Hat=False, force_Hat_address=0x0): #, calibration_oz = calibration_default):
        self.name = name
        self.thread = None
        if force_motor_number == 0 and force_next_Hat is False and force_Hat_address == 0x0:
            self.motor = self.get_next_motor()
        else:
            self.motor = self.get_motor_manual_override(force_motor_number, force_next_Hat, force_Hat_address)

        # recommended for auto-disabling motors on shutdown
        # Note: does not work if there's a segfault
        atexit.register(self.turn_off_motors)

    ############################################
    # Cycle through all available motors
    ############################################
    # Go through all motors, then switch to the next Hat, in order
    # Note: override this for other classes of motors, eg Stepper Motors
    def get_next_motor(self):
        # Move along the motors
        Motors.next_motor_number += 1
        if Motors.next_motor_number > Motors.motors_on_each_Hat:
            # Reset the motor number
            Motors.next_motor_number = 1
            # Move to the next Hat
            try:
                Motors.current_hat = Motors.hat_cycle.next()
            except:
                raise Motors.HatNotConnected("Attempt to address more Hats than exist with name {}".format(self.name))
        return Motors.current_hat.getMotor(Motors.next_motor_number)

    ############################################
    # Allow override of Hat and/or Motor number
    ############################################
    # This allows the developer >>>> who knows what they're actually doing <<<<
    # To choose a motor or Hat directly, bypassing the cycling of the motors
    #
    # get_next_motor, however, is one heck of a lot easier:
    #   just hook up your motors physically in the order you initialize them in code -- easy!!
    def get_motor_manual_override(self, force_motor_number, force_next_Hat=False, force_Hat_address=0x0):
        # Change Hats if the user forced a Hat change
        if force_next_Hat and not force_Hat_address == 0x0:
            raise "Forced a Hat skip AND a Hat address -- can't do both."
        if force_next_Hat:
            try:
                Motors.current_hat = Motors.hat_cycle.next()
                print "FORCED NEW HAT: ", force_next_Hat
            except:
                raise Motors.HatNotConnected("Attempt to address more Hats than exist with name {}".format(self.name))
        elif 0x60 <= force_Hat_address <= 0x70:
            try:
                Motors.current_hat = Adafruit_MotorHAT(force_Hat_address)
            except IOError as error_msg:
                # This raise will happen for EVERY address with no Hat -- not needed unless you are full! :)
                raise IOError(error_msg.message + ' happens at % Motors.py')
        else:
            raise ("Invalid forced Hat address {} -- must be in the range of 0x60 and 0x70".format(force_Hat_address))

        if 1 > force_motor_number > Motors.motors_on_each_Hat:
            raise ("Invalid forced motor number {}!".format(force_motor_number))

        print "FORCED MOTOR: ", force_motor_number
        return Motors.current_hat.getMotor(force_motor_number)

    #############################################
    # Run each motor for 1sec for testing
    #############################################
    @classmethod
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
                    print "Nonexistent motor: #{} in HAT: {}".format(each_motor, each_hat._i2caddr)

    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # Turn off all motors -- this is registered to run at program exit: atexit.register(turn_off_motors)
    # recommended for auto-disabling motors on shutdown!
    @classmethod
    def turn_off_motors(self):
        # Note: motors are 1-indexed, range is 0-indexed, begin at 1, goes to 4
        for each_Hat in Motors.hat_stack:
            for each_motor in range(1, Motors.motors_on_each_Hat):
                try:
                    each_Hat.getMotor(each_motor).run(Adafruit_MotorHAT.RELEASE)
                except:  # Not all motors in all Hats will be available, but let's shut them all down anyway
                    print "Nonexistent motor: #", each_motor

    ############################################
    # Turn motor on and leave it on            #
    ############################################
    # Treat motor as output
    def turn_on(self, speed=255, forwards=True):
        self.motor.setSpeed(speed)
        # print "Effect turned on: {} going: {}".format(self.name, "forwards" if forwards else "backwards")
        self.motor.run(Adafruit_MotorHAT.FORWARD if forwards else Adafruit_MotorHAT.BACKWARD)

    ############################################
    # Turn motor off                           #
    ############################################
    # Treat motor as output
    def turn_off(self):
        # print "Effect turned off: {}".format(self.name)
        self.motor.run(Adafruit_MotorHAT.RELEASE)



    ###########################################################################################################
    # Thread functions: these are the interface for threaded functions -- just use these
    ###########################################################################################################

    #####################################################
    # Thread: Turn on the motor for a specific time     #
    #####################################################
    def thread_motor_duration(self, duration=5, forwards=True):
        self.thread = Motors.ThreadMotor(self._thread_duration, duration, forwards)

    ####################################################
    # Thread: Ramp the effect up or down using PWM     #
    ####################################################
    # This ramps up (or down if false) the motor, going forwards (or backwards if false), skipping by step
    def thread_motor_ramp(self, ramp_up=True, forwards=True, step=2):
        self.thread = Motors.ThreadMotor(self._thread_ramp, ramp_up, forwards, step)

    ####################################################
    # Thread: Flash randomly                           #
    ####################################################
    # This flashes randomly for duration amount of time.
    # shortest and longest are the duration of the types of flashing
    def thread_motor_flash_randomly(self, duration=5, shortest=0.1, longest=0.5):
        self.thread = Motors.ThreadMotor(self._thread_flash_randomly, duration, shortest, longest)


    ############################################
    # Wait until threading is done             #
    ############################################
    # This is important: .join() attaches the thread back to the main thread -- essentally un-threading it.
    # It causes the main program to wait until the motor has completed before it moves on.
    # How to use it: start all the threading first, then call where you want to wait until threading is done
    # For instance, a robot with two arms that flail before walking.  Run the flailing arms as threads,
    #   then call this before walking.
    def wait_until_done(self):
        self.thread.join()

    ###########################################################################################################
    # Threadme functions: these are not meant to be called, but used with threading.
    # You pass a pointer to these functions plus their arguments when initializing the thread
    ###########################################################################################################

    ############################################
    # Run the motor for a certain time         #
    ############################################
    # Simply thread the motor on for duration amount of time, then turn it off
    def _thread_duration(self, duration, forwards=True):
        self.motor.setSpeed(255)
        self.motor.run(Adafruit_MotorHAT.FORWARD if forwards else Adafruit_MotorHAT.BACKWARD)
        time.sleep(duration)
        self.motor.run(Adafruit_MotorHAT.RELEASE)

    ############################################
    # Ramp the motor speed up -- like a fade   #
    ############################################
    # Slowly raise or lower the speed of the motor.
    # The wait is simply how long the loop takes.
    def _thread_ramp(self, ramp_up=True, forwards=True, step=2):
        for i in range(0 if ramp_up else 255, 255 if ramp_up else -1, step if ramp_up else (-step)):
            self.motor.setSpeed(i)
            self.motor.run(Adafruit_MotorHAT.FORWARD if forwards else Adafruit_MotorHAT.BACKWARD)
        if not ramp_up:
            self.motor.run(Adafruit_MotorHAT.RELEASE)
        print "Ramp: {} {}".format(self.name, "forwards" if forwards else "reverse")

    ############################################
    # Flash the motor randomly                 #
    ############################################
    # Pick random delay times until it exceeds duration
    # Note: I cheated - the last flash rounds up to duration
    def _thread_flash_randomly(self, duration=5.0, shortest=0.1, longest=0.5):
        if shortest > longest:
            temp_num = longest
            longest = shortest
            shortest = temp_num
        if shortest > duration or longest > duration or duration <=0.0:
            raise "To thread randomly, shortest and longest must be less than the duration and duration must be > 0!"
        total_duration = 0.0
        while duration > total_duration + 2 * longest:
            # Flash dim
            self.motor.setSpeed(255)
            self.motor.run(Adafruit_MotorHAT.FORWARD)
            percent = randint(0, 100)
            my_duration = (longest - shortest) * percent/100 + shortest
            print "on: {}".format(my_duration)
            time.sleep(my_duration)
            total_duration += my_duration

            # Flash bright
            self.motor.setSpeed(0)  # 255/4)
            self.motor.run(Adafruit_MotorHAT.FORWARD)
            percent = randint(0, 100)
            my_duration = (longest - shortest) * percent/100 + shortest
            print "off: {}".format(my_duration)
            time.sleep(my_duration)
            total_duration += my_duration

        self.motor.setSpeed(255)
        self.motor.run(Adafruit_MotorHAT.FORWARD)
        my_duration = duration - total_duration
        print "on: {}".format(my_duration)
        time.sleep(my_duration)

    #############################################
    # ThreadMotor class:                        #
    #############################################
    # This class allows the motors to all run at the same time.
    # Note that it takes the function that you want to thread, plus the function's arguments
    # This allows this class to be generalized to run any function as a thread.
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

    class LessThanZeroException(Exception):
        pass

    class HatNotConnected(Exception):
        pass
