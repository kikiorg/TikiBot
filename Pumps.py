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
    # It then adjusts the calibration for a normalized 1oz dispense rate.
    #
    # We're looking for the factor of how much this is off by.
    # We dispense what we think should be 2oz (calibrated) then use that to adjust the calibration
    #   eg if it's more, the factor is smaller, and the calibration value gets smaller
    # 2oz theory / 2oz actual = X
    def force_calibrate_pump(self):
        print "Old calibration ounces: ", self.calibration_oz
        self.dispense(Pumps.calibration_default)  # Dispense a calibrated 2.0oz and see if it's correct.
        self.wait_until_done()
        amount_dispensed = self.my_yesno.get_number(
            message="How much liquid was delivered [press Enter if exactly 2.0]? : ", default_val=2.0)

        self.calibration_oz *= (float(amount_dispensed) / Pumps.calibration_default)
        print "Adjusted amount for " + self.name + ":" + str(self.calibration_oz)
        print "Factor: " + str(float(amount_dispensed) / Pumps.calibration_default)
        # Note: it's more useful to return the actual amount dispensed, not the calibration number, because
        #   the parent can find that here: self.calibration_oz
        return amount_dispensed

    ############################################
    # Prime pump                               #
    ############################################
    # This primes the pump.  It assumes the tubing is totally empty, but also allows the user to
    # kick the pump by 1/10ths too.
    def prime(self, prime_ounces=0.0):
        if prime_ounces == 0.0:
            prime_ounces = Pumps.prime_ounces_default
        elif prime_ounces < 0.0:
            print "Invalid prime value!  Less than zero!  Using default: ", Pumps.prime_ounces_default
            prime_ounces = Pumps.prime_ounces_default
        # The pump will have a current spike when it first starts up.
        # This delay allows that current spike to settle to operating current.
        # That way when multiple pumps start at once, there's not a massive current spike from them all.
        time.sleep(Pumps.current_spike_stabilize)
        self.dispense(prime_ounces)

    ############################################
    # Dispense calibrated ounces               #
    ############################################
    # Dispense the ingredients!  ounces is in ounces, multiplied by the calibration time for 1oz
    def dispense(self, ounces, forwards=True):
        # Formala:       1oz / actual oz dispensed in 60 seconds = time for 1oz / 60 seconds
        #                1oz / calibration_oz = X / Pumps.calibration_seconds
        # Solve for X:   time for one ounce = 1oz / actual oz dispensed in 60 seconds * 60 seconds
        #                calibrated_time = 1oz / calibration_oz * Pumps.calibration_seconds
        # Multiply X times ounces for the actual time for those calibrated ounces
        calibrated_time = float(float(ounces) / self.calibration_oz * Pumps.calibration_seconds)
        # Note: this should always be true, but being safe here!
        if calibrated_time <= 0.0:
            raise Motors.LessThanZeroException(
                self.name + ' - calibration:' + str(self.calibration_oz) + ' Must be >0 for motors to run!')
        # Delay to stabilize the current spike on motor startup.
        time.sleep(Motors.current_spike_stabilize)
        # The pumps are run as processor threads, so all pumps can run concurrently.
        print "{} {} of {}.".format("Dispensing" if forwards else "REVERSING", ounces, self.name)
        self.thread = Motors.ThreadMotor(self._thread_duration, calibrated_time, forwards)
