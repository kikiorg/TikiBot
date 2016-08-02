#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# Recipes class:                            #
#############################################
# This class handles everything having to do with the recipes:
#   Read the recipe file
#   Connect all the ingredients to motor controllers
#   Execute all the setup procedures, including priming and calibrating
#   Execute the making of drinks
# It does not include directly addressing the motors (Motors.py) nor the RFID reader (DrinkBot.py)
# It does not interact with the user (SetupBot.py/DrinkBot.py)
#############################################

import csv
import sys
sys.path.insert(0, 'pynfc/src')
import logging

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors
from Pumps import Pumps
from yesno import yesno

#############################################
# To Do List for this file:                 #
#############################################
# Critical path:
#   Remove hard coded RFIDs
#       add a column to the TikiDrinks.csv file for the RFID tags
# If the NFC reader is not plugged in, we get a segfault
# Calculate and store the actual calibration factor, not the ounces -- this is calculated each dispense! :-p
# Turn off the mouth lights in Manual Mode (or maybe switch on the white lights?)
# ---------
# Documentation pass -- make it really pretty, clean up stuff, be succinct
#   DrinkBot.py
#   SetupBot.py
#   SoundEffects.py
# *** Generalize the Motors class!
#   Suggest a subclass for Stepper Motors
#   Better logging
#       Debug levels and stuff
# *** Generalize the Recipes class!
#   Make this for anyone making a DrinkBot
#       This means that calibration stuff and prime stuff need to be generated within the code
#   Better logging
#       Debug levels and stuff
# Constants: change any hard coded constants to global named constants
# Refactor:
#   DrinkBot.py
#   Setup.py
#   SoundEffects.py
#   Recipes.py -- generalize this to open the recipes, not deal with RFID stuff
# Check again that the stabilizing current wait can't be put into Threading...
# ---------- Real world issues
# Change the tubing for pineapple juice
# DONE -- Change out pump#1/Dark Rum -- running rough
# DONE 1 -- 3 more: Install the USB ports
# Look into Jira and Confluence
# Make checklist of things for setup -- including making sure the bottle sizes are entered!
#   Note: print the total amounts dispensed into the log.  Compare to size of bottle.
#   Possibly keep track of amounts dispensed and add those on each time the program runs.
# (Make up a poster for Kiki describing the technical details of what she did)
# ---------- Issues found during Bob benefit
# Pulse the pump when the ingredient might run out
#   Alternately, pulse the mouth lights when ingredients might run out
#   Note: this could get quite complicated
#   Note above: running setup, then repriming the pump cancels the light pulsing to check ingredients.
#   Note: acquire the amounts for each bottle from Sam/Katherine
# Make a shell script that sets up everything:
#   Move log files so new log files are fresh
#   DONE -- DrinkBot is now a script "db"
# ---------- Issues found during DNA Competition
# Check for smoke effect in Setup -- don't run pumps or anything else
# Pulsing the light when the ingredient may run out could get complicated


#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
class DrinkRecipes:
    number_of_pumps = 12
    # Wiring for the broken Hat:
    #   Red LEDs to the power in
    #   White LEDs (white) Fan (blue) eyes LEDs (clear) to #3
    BACKUP_HAT = False  # Use the broken backup hat that has only one motor switch
    NO_EFFECTS = True # Turn off all effcts
    calibration_key = "Calibration"
    prime_key = "Prime"
    prime_percent = 90.0

    def __init__(self, parent_name=""):
        # Initialize all member variables:
        self.drinks = {}            # This is a list of all drinks -- key:value pairs of all the ingredient amounts
        self.drink_names = []       # This is simply a list of all the drink names -- the "menu" as it were
        self.ingr_list = []         # List of all ingredients and their link to their respective pumps -- by csv column
        self.recipe_name = "Recipe"  # Eventually the upper left cell -- the column name, and key for all drink names
        self.total_vol_key = "Total"  # The key to the total volume of each cocktail
        self.ingr_pumps = {}        # List of the pumps themselves
        self.valid_ingr_list = []   # List of all the real ingredients that may be used
        self.calibration_values = {}  # These are the factors to multiply to make a perfect 1oz
        self.prime_values = {}      # This is how much fluid is needed to exactly fill the tubing
        self.primeOz_values = {}    # This is how much fluid is needed to exactly fill the tubing
        self.my_yesno = yesno()     # Used to ask the user yes/no questions

        ############ LED effects
        self.LED_red = None
        self.smoke_fan = None
        self.LED_dispense = None
        self.LED_eyes = None

        # These two are loggers, logging all the infos
        # command_log logs all the commands that are executed -- it's comprehensive.
        # It's test so you can just admire it in a ext editor.
        self.command_log = self.setup_each_loggers(("Recipes.py:" + parent_name + " "),
                                                   filename="CommandLog.txt",
                                                   fmt='%(asctime)s, %(name)s, %(message)s')
        # dispense_log logs all events that actually dispense liquids
        #   This log is meant for things like producing graphs, watching for ingredients running low,
        #   and general data geeking.  This is why it is a .csv file -- to be used in a spreadsheet
        self.dispense_log = self.setup_each_loggers("DispenseLog file",
                                                    filename="DispenseLog.csv",
                                                    fmt='%(asctime)s, %(message)s')
        self.command_log.info('Starting up.')
        self.dispense_log.info('Starting up.')

        self.max_cocktail_volume = self.get_cup_size()

    ########################################################################################
    # Ask the user what cup size -- NOTE: ACTUAL VOLUME eg 16oz cups hold 18oz to the top  #
    ########################################################################################
    def get_cup_size(self, percent_ice=55.0):
        cup_size = self.my_yesno.get_number("What cup size (in ounces) is provided? ")
        self.max_cocktail_volume = cup_size * ((100.0 - percent_ice) / 100.0)  # Subtract out the ice
        # Report to the operator -- to the screen, and to both log files
        format_str = "Cup: {f[0]} - max cocktail volume: {f[1]} - percent cocktail: {f[2]}% - percent ice: {f[3]}%"
        format_list = [cup_size, self.max_cocktail_volume, (100.0 - percent_ice), percent_ice]
        print format_str.format(f=format_list)
        self.command_log.info(format_str.format(f=format_list))
        format_str = format_str.replace(":", ",")
        format_str = format_str.replace(" -", ",")
        self.dispense_log.info(format_str.format(f=format_list))
        # self.dispense_log.info("Cup,{f[0]}, max cocktail volume, {f[1]}, percent cocktail, {f[2]}%,
        # percent ice, {f[2]}".format(f=format_list))

        return self.max_cocktail_volume

    #############################################
    # Setup log file to log all drinks served   #
    #############################################
    def setup_each_loggers(self, name, filename="CommandLog.txt",
                           fmt='%(asctime)s, %(name)s, %(message)s', datefmt='%Y-%m-%d %H:%M:%S'):
        file_handler = logging.FileHandler(filename)
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        file_handler.setFormatter(formatter)
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.INFO)
        new_logger.addHandler(file_handler)

        # Uncomment if you want all logs also to go to stdout
        # screen_handler = logging.StreamHandler(stream=sys.stdout)
        # screen_handler.setFormatter(formatter)
        # new_logger.addHandler(screen_handler)

        return new_logger

    #####################################
    # Create the list of drink recipes  #
    #####################################
    # This opens the file and snarfs it into a list drinks with a list of ingredients
    def get_recipes_from_file(self, recipe_file_name):
        # Open the spreadsheet.
        try:
            my_file = open(recipe_file_name, 'r')
        except IOError as my_error:
            raise IOError("%s: %s" % (recipe_file_name, my_error.strerror))

        # Read the file into a Dictionary type -- this is useful for spreadsheet configurations of CSV data
        recipe_book = csv.DictReader(my_file)

        # Grab a copy of all the ingredient names (aka the fieldnames)
        for each_ingredient in recipe_book.fieldnames:
            self.ingr_list.append(each_ingredient)
        # This is the upper left entry, the column title for all drink names, and the key for each drink name
        self.recipe_name = self.ingr_list[0]
        # The first row is all the ingredients, not a drink recipe.
        self.ingr_list.remove(self.recipe_name)

        ### List of drinks ###
        # Each drink has a list of Key:Value pairs that are the ingredient:amount
        for each_drink in recipe_book:
            # Now go through all the ingredients for this drink, and append the amounts into the drink
            if each_drink[self.recipe_name] in [DrinkRecipes.calibration_key]:  # Pull out the Calibration list separately
                self.calibration_values = {}  # Note, override any previous Calibration lines
                temp_list = self.calibration_values
            elif each_drink[self.recipe_name] in [DrinkRecipes.prime_key]:  # Pull out the Prime list separately
                self.prime_values = {}  # Note, override any previous Calibration lines
                temp_list = self.prime_values
            else:
                # Start with an empty recipe, so we can append each ingredient Key:Value pair
                self.drinks[each_drink[self.recipe_name]] = {}
                self.drink_names.append(each_drink[self.recipe_name])  # Keep a list of all the drink names
                temp_list = self.drinks[each_drink[self.recipe_name]]
            total_volume = 0.0

            ### Go through every ingredient ###
            for each_ingredient in self.ingr_list:
                # Append the ingredient amount to the recipe list
                if each_drink[each_ingredient] is not '':
                    # Example: drinks["Mai Tai]["Orgeat"] = ".25oz"
                    # "Mai Tai" = each_drink[recipe_name] -- goes through every drink
                    # "Orgeat" = each_ingredient -- goes through all ingredients
                    # ".25oz" = each_drink[each_ingredient] -- goes through every amount for that drink
                    try:
                        temp_list[each_ingredient] = float(each_drink[each_ingredient])
                        total_volume += float(each_drink[each_ingredient])
                    except ValueError:
                        print each_drink[each_ingredient], " is not an amount in ounces! Please fix.  Setting to zero."
                        temp_list[each_ingredient] = 0.0
                else:
                    # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
                    temp_list[each_ingredient] = 0.0
                temp_list[self.total_vol_key] = total_volume

        # Done getting the info from the file.
        my_file.close()

        return self

    ###############################################################################
    #     Create pumps linked to ingredients and special effects (LEDs, smoke)    #
    ###############################################################################
    # This goes through all the ingredients and attaches then to a motor/pump
    def link_to_pumps(self):
        temp_ingr_list = iter(self.ingr_list)
        # We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
        for each_motor in range(1, DrinkRecipes.number_of_pumps + 1):
            each_ingredient = temp_ingr_list.next() # Go through all the ingredients by name
            # This is a calibration factor -- more info in Pumps.dispense()
            calibration_oz = float(self.calibration_values[each_ingredient])
            self.ingr_pumps[each_ingredient] = Pumps( name=each_ingredient, calibration_oz=calibration_oz ) # Create the pump
            self.valid_ingr_list.append(each_ingredient) # Add the pump to the list of valid ingredients

        if DrinkRecipes.BACKUP_HAT:
            # The backup Hat has only one motor switch -- connect the fan and the white LEDs
            self.LED_dispense = Motors(name="LED dispense", force_motor_number=3, force_next_Hat=True)
            self.LED_dispense.turn_off()  # Make sure the white light is off
        elif DrinkRecipes.NO_EFFECTS:
            pass
        else:
            # Wires: clear, blue, white, red
            # Effects: eyes, fan, white, red LEDs
            # Create the LED effects -- the volcano eyes and upward shining red light on the smoke
            self.LED_eyes = Motors(name="LED eyes")
            # Create the smoke effects -- fan into the dry ice container
            self.smoke_fan = Motors(name="smoke fan")
            # Create the LED effects -- white LEDs in the mouth while drink is dispensing
            self.LED_dispense = Motors(name="LED dispense")
            # Create the LED effects -- white LEDs in the mouth while drink is dispensing
            self.LED_red = Motors(name="LED red")

            self.smoke_fan.turn_off()  # Make sure the fan is off
            self.LED_dispense.turn_off()  # Make sure the white light is off
            self.LED_eyes.turn_off()  # Make sure the eyes are off
            self.LED_red.thread_motor_ramp()  # Turn on the red LEDs: "ready to dispense"
            self.LED_red.wait_until_done()

    ##############################################################################
    # This prints all the drinks and their ingredients, not including 'Recipe'   #
    ##############################################################################
    # Print the Calibration and Prime lines, then all the drinks
    def print_full_recipes(self):
        print ">>> Calibration <<<"
        self.print_ingredients(self.calibration_values)
        print ">>> Prime <<<"
        self.print_ingredients(self.prime_values)
        for each_drink in self.drink_names:
            print "*** ", each_drink, " ***"
            self.print_ingredients(self.drinks[each_drink])

    def print_ingredients(self, my_list):
        for each_ingredient in my_list:
            # Skip the ingredients that are not used in this recipe
            if my_list[each_ingredient] is not '' and my_list[each_ingredient] != 0.0:
                print each_ingredient + ': ', my_list[each_ingredient]

    #############################################
    #                Prime pumps                #
    #############################################
    # This primes every pump al at once.
    def prime(self, percent=100.0, forwards=True, one_pump=None):
        if one_pump is not None:
            if one_pump in self.valid_ingr_list:
                print "Priming: {}".format(one_pump)
            else:
                try:
                    pump_num = int(one_pump)
                    one_pump = self.valid_ingr_list[pump_num - 1]
                    print "Priming by number: {}".format(one_pump)
                except:
                    print "Invalid pump: {}".format(one_pump)
                    return
            self.ingr_pumps[one_pump].dispense(self.prime_values[one_pump] * percent/100.0, forwards)
            self.ingr_pumps[one_pump].wait_until_done()
        elif one_pump is None:
            self.command_log.info('Prime all ' + ("forwards" if forwards else "reverse"))
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].dispense(self.prime_values[each_ingr] * percent/100.0, forwards)
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].wait_until_done()
        else:
            print "Pump {} is invalid for priming.".format(one_pump)

    #############################################
    #         Global Checksum prime test        #
    #############################################
    # This dispenses 1.0oz for every pump -- should come out to 12oz or 1.5 cups
    def checksum_calibration(self):
        log_str = "" # Keep track of all liquids dispensed in the log
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].dispense(1.0)
            log_str += ",{0:.2f}".format(1.0)
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].wait_until_done()
        self.command_log.info("Executing Checksum,{}".format( log_str ))
        self.dispense_log.info("Checksum,{}".format( log_str ))

    #############################################
    #       Tiny Prime: calibrate priming       #
    #############################################
    # This is for calibrating the prime sequence
    #   it prints out a new line that can be copy and pasted into the .csv file
    #
    # Note: changing the function of this:
    #   This will now overwrite the prime values it got from the file, locally only
    #   This can be written back out, but is not (yet)
    #   This is printed to the command_log as well as to stdout
    def tiny_prime(self):
        percent = DrinkRecipes.prime_percent
        increment = 1.0 # Increment by 1%
        if self.my_yesno.is_yes("Prime all pumps at {} percent?".format(percent)):
            self.my_yesno.is_yes("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            self.prime(percent)
            # Overwrite the prime_values
            for each_ingr in self.valid_ingr_list:
                self.prime_values[each_ingr] *= percent/100
        pump_number = 0 # Use this to print the pump number
        # Creat a handy new line for the .csv file to paste in
        total_string = "Prime,"
        tiny_str = "Tiny prime, "
        # Go through all the pumps
        for each_ingr in self.valid_ingr_list:
            pump_number += 1 # Number the pumps for convenience
            part_tiny = 0 # Total extra priming added
            total_tiny = self.prime_values[each_ingr]
            # While the user wants more ounces of priming
            while self.my_yesno.is_yes("More for Pump #" + str(pump_number) + " Name: " + str(each_ingr) + "?" ):
                # Add this amount to the prime ounces
                self.ingr_pumps[each_ingr].dispense(increment / 100 * self.prime_values[each_ingr])
                # Keep track of all added
                part_tiny +=  increment / 100 * self.prime_values[each_ingr]
                total_tiny += increment / 100 * self.prime_values[each_ingr]
            # Add to the old prime value
            total_string += "{0:.2f},".format(total_tiny)
            # Overwrite the old value needed to prime with the new value
            self.prime_values[each_ingr] += total_tiny
            if part_tiny == 0.0:
                tiny_str += "{},".format(int(part_tiny))  # Show which ingredients needed tiny priming
            else:
                tiny_str += "{0:.2f},".format(part_tiny)  # Show which ingredients needed tiny priming
        print total_string # Print the handy string so it can be copy and pasted into the .csv file
        self.command_log.info(total_string)
        # self.command_log.info("Tiny prime: {}".format(total_string))
        # self.command_log.info("Tiny prime (pumps): {}".format(tiny_str))


    #############################################
    #       Teeny Prime: calibrate priming       #
    #############################################
    # This is for calibrating the prime sequence
    #   it prints out a new line that can be copy and pasted into the .csv file
    #
    # Note: changing the function of this:
    #   This will now overwrite the prime values it got from the file, locally only
    #   This can be written back out, but is not (yet)
    #   This is printed to the command_log as well as to stdout
    def calibrate_prime(self):
        percent = self.prime_percent
        number_extra_primes = 10  # The number of teeny primes needed to make 100%
        increment_factor = (100.0 - percent)/100.0  # This is how much was held back
        increment_factor /= float(number_extra_primes)  # Divided into small portions

        print("Press enter to prime all the pumps to {}%.".format(percent))
        is_yes = self.my_yesno.is_yes("[CTRL-C to exit and not prime the pumps] ")
        if is_yes:
            self.prime(percent)
        calibration_was_needed = False  # Assume the prime values are already perfect
        total_string = "Prime,"  # Create a handy new line for the .csv file to paste in
        # Go through all the pumps
        for each_ingr in self.valid_ingr_list:
            num_of_primes = 0  # How many tiny primes did we have to do -- hopefully 10 (number_extra_primes)
            # print "More for: {}?".format(str(each_ingr))  # More ounces of priming needed
            while self.my_yesno.is_yes("More for: {}?".format(str(each_ingr))):  # More ounces of priming needed
                num_of_primes += 1
                self.ingr_pumps[each_ingr].dispense(increment_factor * self.prime_values[each_ingr])  # Dispense a little bit more...
                self.ingr_pumps[each_ingr].wait_until_done()
            total_tiny = increment_factor * self.prime_values[each_ingr] * num_of_primes
            # This is the Prime line for the .csv file
            total_string += "{0:.2f},".format(total_tiny + self.prime_values[each_ingr] * percent/100.0)
            if num_of_primes != number_extra_primes:  # If this particular pump needed more or less calibration
                calibration_was_needed = True
                # Adjust the old prime value
                self.prime_values[each_ingr] *= percent/100.0
                self.prime_values[each_ingr] += total_tiny

        if calibration_was_needed:
            print total_string # Print the handy string so it can be copy and pasted into the .csv file
            self.command_log.info(total_string)
        else:
            print "The prime values are already calibrated perfectly!"
            self.command_log.info("The prime values are already calibrated perfectly!")

    #############################################
    #              Calibrate pumps              #
    #############################################
    # The tedius process of calibrating every single dang pump by hand
    def calibrate(self):
        new_calibration_string = "Calibration"
        if not self.my_yesno.is_yes("Have all the pumps been primed?"):
            self.my_yesno.is_yes("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            self.prime()

        pump_number = 0
        log_str = ""
        for each_ingr in self.valid_ingr_list:
            pump_number += 1
            if self.my_yesno.is_yes(("Force calibrate Pump #" + str(pump_number) + " [" + each_ingr + "]?")):
                amount_dispensed = self.ingr_pumps[each_ingr].force_calibrate_pump()
                # log_str += "," + str(amount_dispensed)
                log_str += ",{0:.2f}".format(amount_dispensed)
            else:
                # The pump was not calibrated, and so did not dispense any liquids
                # log_str += "," + str(0.0)
                log_str += ",{0:.2f}".format(0.0)
            new_calibration_string += "," + str(self.ingr_pumps[each_ingr].calibration_oz)
        print new_calibration_string
        self.command_log.info("Calibration string: {}".format(new_calibration_string))
        self.command_log.info("Calibration dispensed{}".format(log_str))
        self.dispense_log.info("Calibrated{}".format(log_str))

    #############################################################
    #                     Print the menu                        #
    #############################################################
    def print_menu(self):
        print "********************   Menu of drinks   ********************"
        for each_drink in self.drink_names:
            print each_drink

    #############################################################
    #                  Startup the effects                      #
    #############################################################
    def startup_effects(self):
        if DrinkRecipes.BACKUP_HAT:  # This was the fix for the broken Hat at the DNA DrinkBot Challenge 2016
            # Because the fan and white LEDs are tied together, can't ramp up the fan
            self.LED_dispense.turn_on()
        elif DrinkRecipes.NO_EFFECTS:
            pass
        else:
            # Turn on LEDs and smoke before drink starts to dispense
            self.smoke_fan.turn_on()
            self.LED_eyes.thread_motor_ramp(ramp_up=True)
            self.LED_dispense.thread_motor_ramp(ramp_up=True)
            self.LED_eyes.wait_until_done()  # Ramp up until done, then start flashing
            self.LED_eyes.thread_motor_flash_randomly(shortest=0.1, longest=0.5)

    #############################################################
    #                  Shutdown the effects                     #
    #############################################################
    def shutdown_effects(self):
        if DrinkRecipes.BACKUP_HAT:  # In case we need to use the broken Hat from teh DNA DrinkBot challenge 2016
            self.LED_dispense.turn_off()  # The fan takes a long time to stop, so turn off right away
        elif DrinkRecipes.NO_EFFECTS:
            pass
        else:
            self.LED_eyes.stop_request.set()  # Stop the eyes from flashing
            # Close up the effects -- turn off the fan, ramp down the dispense light and also the eyes
            self.smoke_fan.turn_off()  # The fan takes a long time to stop, so turn off right away
            self.LED_dispense.wait_until_done()  # Unthread the white LEDs -- wait until they are done
            self.LED_eyes.wait_until_done()  # Wait for random flashing to stop
            self.LED_eyes.stop_request.clear()  # Reset the thread so this can be used again
            self.LED_dispense.thread_motor_ramp(ramp_up = False)
            self.LED_eyes.thread_motor_ramp(ramp_up=False)  # Ramp down the flashing eyes
            self.LED_dispense.wait_until_done()
            self.LED_eyes.wait_until_done()

    #############################################################
    #                       Make the drink!                     #
    #############################################################
    def make_drink(self, my_drink):
        ##### Start all the effects
        self.startup_effects()

        ##### Prepare to dispense drink
        scaled_to_fit_glass = self.max_cocktail_volume / self.drinks[my_drink][self.total_vol_key]
        print "********************   Making: ", my_drink, " scaled by {0:.2f}".format(scaled_to_fit_glass), \
            "  ********************"
        print "Stats: total original volume: ", self.drinks[my_drink][self.total_vol_key], \
            " scaled by {0:.2f}".format(scaled_to_fit_glass), \
            " max cocktail volume ", self.max_cocktail_volume

        ##### Start all the pumps going
        log_str = ""
        for each_ingredient in self.valid_ingr_list:
            if float(self.drinks[my_drink][each_ingredient]) > 0.0:
                ounces_to_dispense = float(self.drinks[my_drink][each_ingredient])
                ounces_to_dispense *= scaled_to_fit_glass
                print each_ingredient + ":{0:.2f}".format(ounces_to_dispense)
                self.ingr_pumps[each_ingredient].dispense(ounces_to_dispense)
            else:
                ounces_to_dispense = 0.0
            log_str += ",{0:.2f}".format(ounces_to_dispense)

        ##### Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in self.valid_ingr_list:
            if float(self.drinks[my_drink][each_ingredient]) > 0.0:
                self.ingr_pumps[each_ingredient].wait_until_done()

        ##### End the special effects
        self.shutdown_effects()

        ##### Write out to the logs
        self.command_log.info("{}{}".format(my_drink, log_str))
        self.dispense_log.info("{}{}".format(my_drink, log_str))
