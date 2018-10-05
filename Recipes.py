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
# It does include all the lighting special effects.
#   This should be moved to another class
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
# List ingredients after drink name -- cheat sheet!
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
# >>> Check for ingredients to run out -- PRIORITY
#   New file for ingredient backstock
#   Build this file in Setup Mode -- ask user for each bottle, and partial bottle
#       Ask user for height of fluid when full, then height where fluid is now, and size of bottle -- use math
#   Rewrite this file each drink to drain the ingredients -- each time, so crashing doesn't require flush of this file
#   When ingredient gets low, flash the pump by running it backwards then forwards a few times
#       Assume the user changes the bottle.
#       Note: consolidate bottles only at end of event -- less headaches that way!
# >>> Fix segfault in libnfc -- PRIORITY
# >>> Remove hard coded RFIDs -- PRIORITY
# >>> Make checklist of things for setup -- including making sure the bottle sizes are entered!
#   Note: print the total amounts dispensed into the log.  Compare to size of bottle.
#   Possibly keep track of amounts dispensed and add those on each time the program runs.
# (Make up a poster for Kiki describing the technical details of what she did)
# DONE 3 -- 1 more: Install the USB ports
# Look into Jira and Confluence


#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
class DrinkRecipes:
    # Wiring for the broken Hat:
    #   Red LEDs to the power in
    #   White LEDs (white) Fan (blue) eyes LEDs (clear) to #3
    BACKUP_HAT = False  # Use the broken backup hat that has only one motor switch
    NO_EFFECTS_HAT = False  # Did you break the extra Motor HAT??

    recipe_file_name = None
    calibration_key = "Calibration"
    prime_key = "Prime"
    bottle_size_key = "Bottle_Size"
    bottle_left_key = "Bottle_Left"
    prime_percent = 90.0
    almost_out = 10.0

    def __init__(self, parent_name=""):
        # Initialize all member variables:
        self.drinks = {}             # This is a list of all drinks -- key:value pairs of all the ingredient amounts
        self.drink_names = []        # This is simply a list of all the drink names -- the "menu" as it were
        self.ingr_list = []          # List of all ingredients and their link to their respective pumps -- by csv column
        self.recipe_name = "Recipe"  # Eventually the upper left cell -- the column name, and key for all drink names
        self.total_vol_key = "Total" # The key to the total volume of each cocktail
        self.ingr_pumps = {}         # List of the pumps themselves
        self.valid_ingr_list = []    # List of all the real ingredients that may be used
        self.calibration_values = {} # These are the factors to multiply to make a perfect 1oz
        self.prime_values = {}       # This is how much fluid is needed to exactly fill the tubing
        self.bottle_size = {}        # This is how much fluid is in each bottle
        self.bottle_left = {}        # This is how much fluid is left in each bottle
        self.primeOz_values = {}     # This is how much fluid is needed to exactly fill the tubing
        self.my_yesno = yesno()      # Used to ask the user yes/no questions

        ############ LED effects
        if not DrinkRecipes.NO_EFFECTS_HAT:
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
        cup_size = self.my_yesno.get_number("What cup size is provided? [default 9.0 oz] ", default_val= 9.0)
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
    def get_recipes_from_file(self, recipe_file_name=None):
        if recipe_file_name != None:
            self.recipe_file_name = recipe_file_name
        # Open the spreadsheet.
        try:
            my_file = open(self.recipe_file_name, 'r')
        except IOError as my_error:
            raise IOError("%s: %s" % (self.recipe_file_name, my_error.strerror))

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
                self.calibration_values = []  # Note, override any previous Calibration lines
                temp_list = self.calibration_values
            elif each_drink[self.recipe_name] in [DrinkRecipes.prime_key]:  # Pull out the Prime list separately
                self.prime_values = []  # Note, override any previous Prime lines
                temp_list = self.prime_values
            elif each_drink[self.recipe_name] in [DrinkRecipes.bottle_size_key]:  # Pull out the Inventory list separately
                self.bottle_size = []  # Note, override any previous Inventory lines
                temp_list = self.bottle_size
            elif each_drink[self.recipe_name] in [DrinkRecipes.bottle_left_key]:  # Pull out the Inventory list separately
                self.bottle_left = []  # Note, override any previous Inventory lines
                temp_list = self.bottle_left
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
                    except TypeError:
                        print "float() error -- is it possible you are missing ingredients in the csv file?"
                        raise
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

    #####################################
    # Create the list of drink recipes  #
    #####################################
    # This opens the file and snarfs it into a list drinks with a list of ingredients
    def put_recipes_into_file(self, new_recipe_file_name=None):
        # Open the spreadsheet.
        temp_recipe_file_name = new_recipe_file_name + '.tmp'

        original_recipe_file = open(self.recipe_file_name, 'r')
        temp_recipe_file = open(temp_recipe_file_name, 'w')

        reader = csv.reader(original_recipe_file)
        for row in reader:
            if (row[0] is self.bottle_size_key):
                temp_recipe_file.write(self.bottle_size_key)
                for size in self.bottle_size:
                    temp_recipe_file.write(',')
                    temp_recipe_file.write(size)
            elif (row[0] is not self.bottle_left_key):
                temp_recipe_file.write(self.bottle_left_key)
                for left in self.bottle_left:
                    temp_recipe_file.write(',')
                    temp_recipe_file.write(left)
            else:
                temp_recipe_file.write(row)

        # Done getting the info from the file.
        original_recipe_file.close()
        temp_recipe_file.close()
        # Rename the file -- test first

        return self

    ###############################################################################
    #     Create pumps linked to ingredients and special effects (LEDs, smoke)    #
    ###############################################################################
    # This goes through all the ingredients and attaches then to a motor/pump
    def link_to_pumps(self):
        temp_ingr_list = iter(self.ingr_list)
        # We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
        for each_motor in range(1, 13):
            each_ingredient = temp_ingr_list.next() # Go through all the ingredients by name
            # This is a calibration factor -- more info in Pumps.dispense()
            calibration_oz = float(self.calibration_values[each_ingredient])
            self.ingr_pumps[each_ingredient] = Pumps( name=each_ingredient, calibration_oz=calibration_oz ) # Create the pump
            self.valid_ingr_list.append(each_ingredient) # Add the pump to the list of valid ingredients

        if DrinkRecipes.BACKUP_HAT:
            # The backup Hat has only one motor switch -- connect the fan and the white LEDs
            self.LED_dispense = Motors(name="LED dispense", force_motor_number=3, force_next_Hat=True)
            self.LED_dispense.turn_off()  # Make sure the white light is off
        elif DrinkRecipes.NO_EFFECTS_HAT:
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

            # Make sure everything begins in OFF position
            self.smoke_fan.turn_off()
            self.LED_dispense.turn_off()
            self.LED_eyes.turn_off()
            self.LED_red.turn_off()

    ##############################################################################
    # This prints all the drinks and their ingredients, not including 'Recipe'   #
    ##############################################################################
    # Print the Calibration and Prime lines, then all the drinks
    def print_full_recipes(self):
        print ">>> Calibration <<<"
        self.print_ingredients(self.calibration_values)
        print ">>> Prime <<<"
        self.print_ingredients(self.prime_values)
        print ">>> Inventory <<<"
        self.print_ingredients(self.bottle_left)
        for each_drink in self.drink_names:
            print "*** ", each_drink, " ***"
            self.print_ingredients(self.drinks[each_drink])

    ############################################
    #             Print ingredients            #
    ############################################
    # print out all the ingredients and amounts used to the srceen
    def print_ingredients(self, my_recipe):
        for each_ingredient in my_recipe:
            # Skip the ingredients that are not used in this recipe
            if my_recipe[each_ingredient] is not '' and my_recipe[each_ingredient] != 0.0:
                print each_ingredient + ': ', my_recipe[each_ingredient]

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
            print "Priming all pumps."
            self.command_log.info('Prime all ' + ("forwards" if forwards else "reverse"))
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].dispense(self.prime_values[each_ingr] * percent/100.0, forwards)
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].wait_until_done()
        else:
            print "Pump {} is invalid for priming.".format(one_pump)

    #############################################
    #                Prime pumps                #
    #############################################
    # This primes every pump al at once.
    def inventory_reset(self, one_pump=None, fluid_oz=25.3605): # 25.3605oz is 750ml, common alcohol bottle size
        if one_pump is not None:
            if one_pump in self.valid_ingr_list:
                print "Priming: {}".format(one_pump)
            else:
                try:
                    pump_num = int(one_pump)
                    one_pump = self.valid_ingr_list[pump_num - 1]
                    print "Inventory reset by number: {}".format(one_pump)
                except:
                    print "Invalid pump: {}".format(one_pump)
                    return
            self.bottle_left[one_pump] = fluid_oz
            # Write out the recipe file
        else:
            print "Pump {} is invalid for inventory reset.".format(one_pump)

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
    #     kid_drink: copied from tiny_prime     #
    #############################################
    # For creating new drinks quickly by dispensing tiny squirts of ingredients
    #
    # The new drink will be printed to the screen (and log) when you're done and satisfied
    def kid_drink(self):
        squirt = 0.1 # Increment by 0.1oz

        my_new_drink = raw_input("Name of your new drink:")
        while my_new_drink is not "":
            # Create an empty set of ingredients
            new_drink = {}
            for each_ingr in self.valid_ingr_list:
                new_drink[each_ingr] = 0.0

            user_still_making_this_drink = True
            while user_still_making_this_drink:
                # print the names of all the ingredients
                pump_num = 0
                for each_ingr in self.valid_ingr_list:
                    pump_num += 1
                    print "{} - {}".format(pump_num, each_ingr)
                my_pump = raw_input("Please enter pump number to dispense [minus to take away, eg: -10]:")
                my_pump = int(my_pump)
                if my_pump > 0:
                    my_pump -= 1  # Zero index
                    self.ingr_pumps[self.valid_ingr_list[int(my_pump)]].dispense(squirt)
                    self.ingr_pumps[self.valid_ingr_list[int(my_pump)]].wait_until_done()
                    new_drink[self.valid_ingr_list[int(my_pump)]] += squirt
                elif my_pump < 0:
                    my_pump -= 1  # Zero index
                    new_drink[self.valid_ingr_list[int(my_pump)]] -= squirt
                    if self.my_yesno.is_yes("Would you like to redispense the entire drink to taste it? [Y/n]"):
                        for dispense_ingr in new_drink:
                            if float(new_drink[dispense_ingr]) > 0.0:
                                print dispense_ingr + ":{0:.2f}".format(new_drink[dispense_ingr])
                                self.ingr_pumps[dispense_ingr].dispense(new_drink[dispense_ingr])
                        for dispense_ingr in new_drink:
                            if float(new_drink[dispense_ingr]) > 0.0:
                                self.ingr_pumps[dispense_ingr].wait_until_done()
                else:  # Assert: my_pump == 0:
                    user_still_making_this_drink = False # Stop making this drink
                    if self.my_yesno.is_yes("Would you like to redispense the entire drink to taste it? [Y/n]"):
                        for ingr_num in range(0,11):
                            dispense_ingr = self.valid_ingr_list[int(ingr_num)]
                            if float(new_drink[dispense_ingr]) > 0.0:
                                print dispense_ingr + ":{0:.2f}".format(new_drink[dispense_ingr])
                                self.ingr_pumps[dispense_ingr].dispense(new_drink[dispense_ingr])
                    if self.my_yesno.is_yes("Do you want to record this drink recipe? [Y/n]"):
                        new_drink_str = "{}, ".format(my_new_drink)  # Start with the new drink name
                        # Append all the ingrdient amounts
                        for each_new_ingr in range(len(new_drink)):
                            new_drink_str += "{},".format(new_drink[self.valid_ingr_list[int(each_new_ingr)]])  # Show which ingredients needed kid priming
                        print new_drink_str  # Print to the sreen
                        self.command_log.info(new_drink_str)  # Print to the Command Log
            # Lather, rinse, repeat
            my_new_drink = raw_input("Name of your new drink: ")

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
    def ready_to_dispense(self, cancel=False):
        if DrinkRecipes.BACKUP_HAT:  # This was the fix for the broken Hat at the DNA DrinkBot Challenge 2016
            pass  # Leaving these here, in case things change -- again!
        elif DrinkRecipes.NO_EFFECTS_HAT:
            pass  # Leaving these here, in case things change -- again!
        else:
            if cancel:
                self.LED_red.thread_motor_ramp(ramp_up=False)  # Ramp down the red LEDs: "ready to dispense"
                self.LED_red.wait_until_done()
            else:
                self.LED_red.thread_motor_ramp()  # Turn on the red LEDs: "ready to dispense"
                self.LED_red.wait_until_done()


    #############################################################
    #                  Hard off the effects                     #
    #############################################################
    # This shuts everything off, without fanfair
    def hard_off_effects(self):
        if DrinkRecipes.BACKUP_HAT:
            # The backup Hat has only one motor switch -- connect the fan and the white LEDs
            self.LED_dispense.turn_off()  # Make sure the white light is off
        elif DrinkRecipes.NO_EFFECTS_HAT:
            pass
        else:
            self.smoke_fan.turn_off()  # Make sure the fan is off
            self.LED_dispense.turn_off()  # Make sure the white light is off
            self.LED_eyes.turn_off()  # Make sure the eyes are off
            self.LED_red.turn_off()  # Turn on the red LEDs: "ready to dispense"

    #############################################################
    #                  Startup the effects                      #
    #############################################################
    # For starting up the effects for when a drink begins dispensing
    def startup_effects(self):
        if DrinkRecipes.BACKUP_HAT:  # This was the fix for the broken Hat at the DNA DrinkBot Challenge 2016
            # Because the fan and white LEDs are tied together, can't ramp up the fan
            self.LED_dispense.turn_on()
        elif DrinkRecipes.NO_EFFECTS_HAT:
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
    # For shutting down the effects when a drink is finished dispensing
    def shutdown_effects(self):
        if DrinkRecipes.BACKUP_HAT:  # In case we need to use the broken Hat from teh DNA DrinkBot challenge 2016
            self.LED_dispense.turn_off()  # The fan takes a long time to stop, so turn off right away
        elif DrinkRecipes.NO_EFFECTS_HAT:
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
            self.ready_to_dispense(cancel=True)

    #############################################################
    #                  Startup the effects                      #
    #############################################################
    # Turn on all the lights when in setup mode -- this also tests the lights
    def setup_effects(self):
        if DrinkRecipes.BACKUP_HAT:
            # The backup Hat has only one motor switch -- connect the fan and the white LEDs
            self.LED_dispense.turn_off()  # Make sure the white light is off
        elif DrinkRecipes.NO_EFFECTS_HAT:
            pass
        else:
            self.smoke_fan.turn_off()  # Make sure the fan is off
            self.LED_dispense.turn_on()  # Make sure the white light is off
            self.LED_eyes.turn_on()  # Make sure the eyes are off
            self.LED_red.turn_on()  # Turn on the red LEDs: "ready to dispense"

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
                if self.bottle_left != 0: # There's a zero if we don't know how much is in this bottle
                    self.bottle_left -= ounces_to_dispense / self.bottle_size
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

        ##### Check that nothing has run out
        # Right now, this checks for a simple percent.
        # Better would be to check that it can make the next maximum drink
        for each_ingr in self.valid_ingr_list:
            if self.bottle_left[each_ingr] < self.almost_out:
                print("Almost out:", each_ingr) # Print this out in case the performer is still interacting with the customer
                # (run pump back and forth)
                self.prime(percent=1.0, forwards=False, one_pump=each_ingr)
                self.prime(percent=1.0, forwards=True, one_pump=each_ingr)
                self.prime(percent=1.0, forwards=False, one_pump=each_ingr)
                self.prime(percent=1.0, forwards=True, one_pump=each_ingr)

        ## Write out the recipe file, including updated bottle left amounts -- in case the program crashes
