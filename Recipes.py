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

import time
import csv
import sys
sys.path.insert(0, 'pynfc/src')
import logging
from SoundEffects import SoundEffects

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors
from Pumps import Pumps
from yesno import yesno
from oz_gal_ml import oz_gal_ml

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
# >>> Make checklist of things for setup -- including making sure the bottle sizes are entered!
#   Note: print the total amounts dispensed into the log.  Compare to size of bottle.
#   Possibly keep track of amounts dispensed and add those on each time the program runs.
# (Make up a poster for Kiki describing the technical details of what she did)
# DONE -- Make a shell script that sets up everything:
#   DEFERRED -- Move log files so new log files are fresh
#       Not needed: just let logs accumulate and pick events out by hand.  No big deal.
#   DONE -- DrinkBot is now a script "db"
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

    calibration_key = "Calibration"
    prime_key = "Prime"
    prime_percent = 90.0
    inventory_filename = "TikiBottleInventory.csv"

    # Initialization  sounds
    # Since the text is so hard to read, this prompts you in audio
    #my_sound_init_cup = SoundEffects(sound_name="sounds/init/init_cup_size.wav", channel=1)
    my_sound_init_cup = SoundEffects(sound_name="sounds/init_q/init_cup_sizeQ.wav", channel=1)
    #my_sound_init_event_name = SoundEffects(sound_name="sounds/init/init_event_name.wav", channel=1)
    my_sound_init_event_name = SoundEffects(sound_name="sounds/init_q/init_event_nameQ.wav", channel=1)

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
        self.my_oz = oz_gal_ml()    # Used for inventory stuff

        self.dispensed = {}         # This is how much has been dispensed since start
        self.inventory = {}         # Size of the current bottle
        self.maxdisp = {}           # We don't dispense if a bottle doesn't hve this much
        self.buffer = 3             # 3oz buffer to cover the tube
        self.bottle_sounds = {}     # audio prompts for which bottle to replace

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

        DrinkRecipes.my_sound_init_event_name.play_sound()
        event_name = raw_input("Please enter the Event Name: ")
        DrinkRecipes.my_sound_init_event_name.join()

        self.command_log.info("Starting up: {}".format(event_name))
        self.dispense_log.info("Starting up: {}".format(event_name))

        self.max_cocktail_volume = 0.0
        self.max_cocktail_volume = self.get_cup_size()

    def test_lights(self):
        while True:
#            self.smoke_fan.turn_on()
#            self.LED_eyes.thread_motor_ramp(ramp_up=True)
#            self.LED_dispense.thread_motor_ramp(ramp_up=True)
#            self.LED_eyes.thread_motor_flash_randomly(shortest=0.1, longest=0.5)
            print("Testing lights: FAN")
            self.smoke_fan.thread_motor_ramp()  # Turn on the red LEDs: "ready to dispense"
            self.smoke_fan.wait_until_done()
#            self.smoke_fan.turn_on()
            time.sleep(5)
            self.smoke_fan.turn_off()

            print("Testing lights: RED LAVA")
            self.LED_red.thread_motor_ramp(ramp_up=True)
            self.LED_red.wait_until_done()
            self.LED_red.turn_on()
            time.sleep(5)
            self.LED_red.turn_off()

            print("Testing lights: WHITE")
            self.LED_dispense.turn_on()
            time.sleep(5)
            self.LED_dispense.turn_off()

            print("Testing lights: DEVIL EYES")
            self.LED_eyes.turn_on()
            time.sleep(5)
            self.LED_eyes.turn_off()

            time.sleep(8)




    ########################################################################################
    # Ask the user what cup size -- NOTE: ACTUAL VOLUME eg 16oz cups hold 18oz to the top  #
    ########################################################################################
    def get_cup_size(self, percent_ice=55.0):
        DrinkRecipes.my_sound_init_cup.play_sound()
        cup_size = self.my_yesno.get_number("What cup size is provided? [default 9.0 oz] ", default_val= 9.0)
        DrinkRecipes.my_sound_init_cup.join()

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
            temp_sound_file = each_ingredient.replace(" ", "_")
            temp_sound_file = "sounds/bottles_q/low_{}Q.wav".format(temp_sound_file)
            self.bottle_sounds[each_ingredient] = SoundEffects(sound_name=temp_sound_file, channel=1)

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
            temp_oz = 0.0
            for each_ingredient in self.ingr_list:
                # Append the ingredient amount to the recipe list
                if each_drink[each_ingredient] is not '':
                    # Example: drinks["Mai Tai]["Orgeat"] = ".25oz"
                    # "Mai Tai" = each_drink[recipe_name] -- goes through every drink
                    # "Orgeat" = each_ingredient -- goes through all ingredients
                    # ".25oz" = each_drink[each_ingredient] -- goes through every amount for that drink
                    try:
                        temp_oz = float(each_drink[each_ingredient])
                        temp_list[each_ingredient] = temp_oz
                        total_volume += temp_oz
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

        # Set up for empty bottle detection
        # This kinda sucks.
        # First, initialize the sets

        for each_ingredient in self.ingr_list:
            # Initialize the maximum that can be dispensed to 0
            self.maxdisp[each_ingredient] = 0.0

        # Second, go through every dang drink yet again
        # to find the maximum that any ingredient could dispense
        for each_drink_key in self.drinks:
            # Scale the max dispensed for each ingredient
            scaled_to_fit = self.max_cocktail_volume
            scaled_to_fit /= self.drinks[each_drink_key][self.total_vol_key]
            for each_ingredient in self.ingr_list:
                # Find the max that can be dispensed in one drink
                # (The bottle will have to have at least this in it plus a buffer)
                scaled_ingr = self.drinks[each_drink_key][each_ingredient]
                scaled_ingr *= scaled_to_fit # Scale the ingredient for this drink
                self.maxdisp[each_ingredient] = scaled_ingr if scaled_ingr > self.maxdisp[each_ingredient] else self.maxdisp[each_ingredient]
                # FIXX!!!!  I could put back scaled ingredients at this point!
                # each_drink[each_ingredient] = scaled_ingr

        # Third: Read the dang inventory file
        with open(DrinkRecipes.inventory_filename, "r") as inventory_f:
            temp_line = inventory_f.readline().strip() # strip() means remove /r/n
            temp_ingr = temp_line.split(", ")[1:] # [1:] means take off title
            temp_line = inventory_f.readline().strip()
            temp_invn = [float(x) for x in temp_line.split(", ")[1:]]
            temp_line = inventory_f.readline().strip()
            temp_disp = [float(x) for x in temp_line.split(", ")[1:]]
        # I should change the mess above to do it so nicely like this
        self.inventory = dict(zip(temp_ingr,temp_invn))
        self.dispensed = dict(zip(temp_ingr,temp_disp))

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
            if (num_of_primes != number_extra_primes) and (num_of_primes != 0):  # If this particular pump needed more or less calibration
                calibration_was_needed = True
                # Adjust the old prime value
                self.prime_values[each_ingr] *= percent/100.0
                self.prime_values[each_ingr] += total_tiny
            print "num_of_primes: ", num_of_primes
            if num_of_primes == 0:
                # If this pump didn't need calibration, then put the original number back
                total_string += "{0:.2f},".format(self.prime_values[each_ingr])
            else:
                total_string += "{0:.2f},".format(total_tiny + self.prime_values[each_ingr] * percent/100.0)

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
        new_calibration_string += ","
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
        log_dsp = ""
        for each_ingredient in self.valid_ingr_list:
            if float(self.drinks[my_drink][each_ingredient]) > 0.0:
                ounces_to_dispense = float(self.drinks[my_drink][each_ingredient])
                ounces_to_dispense *= scaled_to_fit_glass
                print each_ingredient + ":{0:.2f}".format(ounces_to_dispense)
                self.ingr_pumps[each_ingredient].dispense(ounces_to_dispense)
                self.dispensed[each_ingredient] += ounces_to_dispense
            else:
                ounces_to_dispense = 0.0
            log_str += ",{0:.2f}".format(ounces_to_dispense)
            log_dsp += ",{0:.2f}".format(self.dispensed[each_ingredient])

        ##### Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in self.valid_ingr_list:
            if float(self.drinks[my_drink][each_ingredient]) > 0.0:
                self.ingr_pumps[each_ingredient].wait_until_done()

        ##### End the special effects
        self.shutdown_effects()

        ##### Write out to the logs
        self.command_log.info("{}{}".format(my_drink, log_str))
        self.command_log.info("Dispensed so far: {}".format(log_dsp))
        self.dispense_log.info("{}{}".format(my_drink, log_str))

    #############################################################
    #                       Check bottles                       #
    #############################################################
    def check_inventory(self):
        # Make sure all the bottle have enough for the next drink
        for each_ingredient in self.valid_ingr_list:
            # What we will have when the drink is dispensed
            temp_inv = self.inventory[each_ingredient] - self.dispensed[each_ingredient]
            # The largest amount we might dispense
            temp_leftover = self.maxdisp[each_ingredient]
            # Check what we have against what we might dispense, 
            # leaving a buffer to cover the end of the tube
            print "    {}:{:3.2f} > max:{:3.2f} + buf:{:3.2f}?".format(each_ingredient,temp_inv, temp_leftover, self.buffer)
            if temp_inv >= temp_leftover + self.buffer:
                print "    OK!"
            else:
                # Flash the lights!! WARNING!!  DANGER!!
#                self.startup_effects()
#                self.shutdown_effects()
#                self.startup_effects()
#                self.shutdown_effects()
                print "Change: {}".format(each_ingredient)

                self.bottle_sounds[each_ingredient].play_sound()
                val = self.my_oz.get_oz(message="Bottle size for {} ".format(each_ingredient))
                self.bottle_sounds[each_ingredient].join()
                if val != 0.0:
                    self.inventory[each_ingredient] = val 
                # Reset how much dispensed from this bottle
                # Note: to find out how much was dispensed since running
                # You'll just have to calculate that from logs
                self.dispensed[each_ingredient] = 0.0 # Not dispensed anything from this bottle
                print "   CHANGED: {} SIZE: {}".format(each_ingredient, 
                                                    self.inventory[each_ingredient])
                self.command_log.info("CHANGED: {} SIZE: {}".format(each_ingredient,
                                                    self.inventory[each_ingredient]))

                # Overwrite the inventuroy file with new inventory
                names_line = "Ingredients"
                inventory_line = "BottleSize"
                dispensed_line = "Dispensed"

                for each_ingredient2 in self.valid_ingr_list:
                    names_line += ", {}".format(each_ingredient2)
                    inventory_line += ", {}".format(self.inventory[each_ingredient2])
                    dispensed_line += ", {}".format(self.dispensed[each_ingredient2])
                inventory_file = open(DrinkRecipes.inventory_filename, "w+")
                inventory_file.write(names_line + "\r\n")
                inventory_file.write(inventory_line + "\r\n")
                inventory_file.write(dispensed_line + "\r\n")
                inventory_file.close()

    #############################################################
    #                   Take bottle inventory                   #
    #############################################################
    def take_inventory(self):
        # Make sure all the bottle have enough for the next drink
        print
        print
        print ("     **** Key: 25.36oz = 750ml  33.80oz = 1L  59.17oz = 1.75L  64oz = 1gal")
        print
        for each_ingredient in self.valid_ingr_list:
            print("{:20} bottle size: {:6.2f}oz   amount left: {:6.2f}oz".format(
                                  each_ingredient, 
                                  self.inventory[each_ingredient],
                                  self.inventory[each_ingredient] -
                                  self.dispensed[each_ingredient]))

        print
        for each_ingredient in self.valid_ingr_list:
            # Ask user for the size of the bottle -- allow [Enter] for last bottle size
#            self.bottle_sounds[each_ingredient].play_sound()
            message = "{}: [press enter for {:3.0f}% of {:3.2f}oz] ".format(
                                  each_ingredient, 
                                  100 - (self.dispensed[each_ingredient] /
                                  self.inventory[each_ingredient]) * 100,
                                  self.inventory[each_ingredient])
            temp_inv = self.my_oz.get_oz(message=message)
#            self.bottle_sounds[each_ingredient].join()

            # (else) If user pressed [ENTER] or entered a 0, then skip this bottle
            if (temp_inv == 0.0):
                pass # If the user enters zero, then skip this bottle
            else:
                self.inventory[each_ingredient] = temp_inv
                # Ask user how much is left -- allow [Enter] for last value
                temp_left = self.my_oz.get_portion(message="How much of the {} bottle is left [Enter for full] ".format(each_ingredient))
                if (temp_left != 0.0):
                    # We want how much has been dispensed, not how much is left
                    temp_disp = temp_inv * (1.0 - temp_left)
                    self.dispensed[each_ingredient] = temp_disp
                else:
                    self.dispensed[each_ingredient] = 0.0

                # Overwrite the inventuroy file with new inventory
                # FOR EVERY FRIKKIN INVENTORY BOTTLE ENTRY!!!
                names_line = "Ingredients"
                inventory_line = "BottleSize"
                dispensed_line = "Dispensed"

                print "  TAKE INVENTORY: {} {:3.0f}% of {:3.2f}oz".format(
                                  each_ingredient, 
                                  100 - (self.dispensed[each_ingredient] /
                                  self.inventory[each_ingredient]) * 100,
                                  self.inventory[each_ingredient])
                self.command_log.info("TAKE INVENTORY: {} {:3.2f}% of {:3.2f}oz".format(
                                  each_ingredient, 
                                  self.dispensed[each_ingredient],
                                  self.inventory[each_ingredient]))

                for each_ingredient2 in self.valid_ingr_list:
                    names_line += ", {}".format(each_ingredient2)
                    inventory_line += ", {}".format(self.inventory[each_ingredient2])
                    dispensed_line += ", {}".format(self.dispensed[each_ingredient2])
                inventory_file = open(DrinkRecipes.inventory_filename, "w+")
                inventory_file.write(names_line + "\r\n")
                inventory_file.write(inventory_line + "\r\n")
                inventory_file.write(dispensed_line + "\r\n")
                inventory_file.close()
