#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# Pumps class:                              #
#############################################
# This class extends Motors to handle a lot of pump specific needs:
#   It calibrates the pump
#   It primes the pumps
#   It dispenses according to the calibration
#############################################

# Needed to sleep-wait for motor to finish running.
from Motors import Motors
import time

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

############################################################################
# Generalized Motors class for using Adafruit Motor Hats on a Raspberry Pi #
############################################################################
# This class is for simple output controlling for Motor Hats
# This ignores the center pin, and assumes 4 simple motors
class Pumps(Motors):

    ############################################
    # Pump calibration constants
    # We assume these are pumps that dispense about 2oz every 60 seconds.
    calibration_default = 2.0
    calibration_seconds = 60.0
    # This is how long it should take to fill the pump tubing to dispense -- no longer, so none is wasted
    prime_ounces_default = 0.40

    ############################################
    # Initialize the motors on the Bot         #
    ############################################
    # This gives each motor a name, and a calibration value, and initializes a member for the thread
    # This gets the next motor in line of all the Hats
    def __init__(self, name, force_motor_number = 0, force_next_Hat = False, calibration_oz = calibration_default):
        Motors.__init__(self, name, force_motor_number, force_next_Hat)
        # Each motor should dispense 2oz in 60 seconds (is should dispense calibration_default in calibration_seconds)
        # But, of course, they vary.
        # This is the actual amount in ounces that this particular motor dispenses in calibration_seconds
        #   See .dispense for the Magic of Math for how it uses this numbers to calibrate the motor
        self.calibration_oz = calibration_oz


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
        Motors.time.sleep(Motors.current_spike_stabilze)
        self.thread = Motors.ThreadMotor(self.motor, prime_value, self.name)

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
        calibrated_time = float(float(ounces) / self.calibration_oz * Pumps.calibration_seconds)
        # Note: this should always be true, but being safe here!
        if calibrated_time <= 0.0:
            raise Motors.LessThanZeroException(
                self.name + ' - calibration:' + str(self.calibration_oz) + ' Must be >0 for motors to run!')
        # Delay to stabilize the current spike on motor startup.
        time.sleep(Motors.current_spike_stabilze)
        # The pumps are run as processor threads, so all pumps can run concurrently.
        self.thread = Motors.ThreadMotor(self.thread_for_time_run, self.motor, calibrated_time, forwards)
        # print "Finished dispensing ", ounces, " of ", self.name, "."
