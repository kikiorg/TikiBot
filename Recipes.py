#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv
import sys
sys.path.insert(0, 'pynfc/src')
import logging

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors
from yesno import yesno

#############################################
# To Do List for this file:                 #
#############################################
# Blurb of documentation at the top of each file saying what each one does
# Documentation pass -- make it really pretty, claen up stuff, be succint
# Change the tubing for pineapple juice
# Change out pump#1/Dark Rum -- running rough
# Remove hard coded RFIDs
#   add a column to the TikiDrinks.csv file for the RFID tags
# Prime/Purge/Forward Purge/Reverse Purge -- consolidate these! Refactor
# Convert Prime values to ounces needed to prime each pump -- this is useful info to have anyway!
# Constants: change any hard coded constants to global named constants
# Look into Jira and Confluence
# ---------- Issues found during Bob benefit
# DONE -- Tiny Prime needs log line telling which ingredients were primed
# Tiny Prime becomes Calibrate Prime -- prime by 90% then Tiny Prime
# Reprime for ingredients that have run out
# Pulse the pump when the ingredient might run out
#   Alternately, pulse the mouth lights when ingredients might run out
# Combine DrinkLog.txt and CommandLog.txt -- make DrinkLog.csv not .txt -- maybe DispenseLog.csv
# Make a shell script that sets up everything:
#   Setup
#   Move log files so new log files are fresh
#   DrinkBot
#   Note: possibly use white card for setup/manual override
#       Make SetUp a class
# Manual dispensing of drinks allows for typing drink number from the menu -- easier
#   Allow pressing [Enter} to go back to scanning
#   Note above: running setup, then repriming the pump cancels the light pulsing to check ingredients.
#   Note: acquire the amounts for each bottle from Sam/Katherine
# Make checklist of things for setup -- including making sure the bottle sizes are entered!
#   Note: print the total amounts dispensed into the log.  Compare to size of bottle.
#   Possibly keep track of amounts dispensed and add those on each time the program runs.
# (Make up a poster for Kiki describing the technical details of what she did)
# DONE -- round the numbers to 2 decimal places, egads!
# DONE -- Separate log file for all the drinks, separate from the command file, logging all commands executed
# DONE -- Log File did not include 0.0 ingredients
# DONE -- weird bug with Mai Tai -- answer: the ingredients were dispensed out of order.
#   Bug is fixed for the future, but old log file still has error (I'm not going to bother telling anyone :) )
# DONE -- Comma after each entry in the log file, so the CSV formats nicely in a spreadsheet


#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
class Drink_Recipes():
    def __init__(self, parent_name = ""):
        # Initialize all member variables:
        self.drinks = {}  # This is a list of all drinks -- key:value pairs of all the ingredient amounts
        self.drink_names = []  # This is simply a list of all the drink names -- the "menu" as it were
        self.ingr_list = []  # List of all ingredients and their link to their respective pumps -- by csv column
        self.recipe_name = "Recipe" # Eventually the upper left cell -- the column name, and key for all drink names
        self.total_vol_key = "Total" # The key to the total volume of each cocktail
        self.ingr_pumps = {} # List of the pumps themselves
        self.valid_ingr_list = [] # List of all the real ingredients that may be used
        self.calibration_values = {}
        self.prime_values = {}
        self.my_yesno = yesno()
        self.command_log = None
        self.drink_log = None
        self.setup_loggers("Recipes.py:" + parent_name + " ")

        self.command_log.info('Starting up.')

    #############################################
    # Setup log file to log all drinks served   #
    #############################################

    def setup_loggers(self, name):
        file_handler = logging.FileHandler('CommandLog.txt')
        formatter = logging.Formatter(fmt='%(asctime)s, %(name)s, %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.command_log = logging.getLogger(name)
        self.command_log.setLevel(logging.INFO)
        self.command_log.addHandler(file_handler)

        # Uncomment if you want all logs also to go to stdout
        # screen_handler = logging.StreamHandler(stream=sys.stdout)
        # screen_handler.setFormatter(formatter)
        # command_log.addHandler(screen_handler)


        file_handler = logging.FileHandler('DrinkLog.txt')
        formatter = logging.Formatter(fmt='%(asctime)s, %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.drink_log = logging.getLogger(name)
        self.drink_log.setLevel(logging.INFO)
        self.drink_log.addHandler(file_handler)


        # Uncomment if you want all logs also to go to stdout
        # screen_handler = logging.StreamHandler(stream=sys.stdout)
        # screen_handler.setFormatter(formatter)
        # drink_log.addHandler(screen_handler)

    def get_recipes_from_file(self, recipe_file_name):
        # Open the spreadsheet.
        try:
            myFile = open(recipe_file_name, 'r')
        except IOError as my_error:
            raise IOError("%s: %s" % (recipe_file_name, my_error.strerror))

        # Read the file into a Dictionary type -- this is useful for spreadsheet configurations of CSV data
        recipe_book = csv.DictReader(myFile)

        # Grab a copy of all the ingredient names (aka the fieldnames)
        for each_ingredient in recipe_book.fieldnames:
            self.ingr_list.append(each_ingredient)
        # This is the upper left entry, the column title for all drink names, and the key for each drink name
        self.recipe_name = self.ingr_list[0]
        # The first row is all the ingredients, not a drink recipe.
        self.ingr_list.remove(self.recipe_name)

        #####################################
        # Create the list of drink recipes  #
        #####################################
        # This is a list of drinks and each drink has a list of Key:Value pairs that are the ingredient:amount
        for each_drink in recipe_book:
            # Now go through all the ingredients for this drink, and append the amounts into the drink
            if each_drink[self.recipe_name] in ["Calibration"]: # Pull out the Calibration list separately
                self.calibration_values = {} # Note, override any previous Calibration lines
                temp_list = self.calibration_values
            elif each_drink[self.recipe_name] in ["Prime"]: # Pull out the Prime list separately
                self.prime_values = {} # Note, override any previous Calibration lines
                temp_list = self.prime_values
            else:
                self.drinks[each_drink[self.recipe_name]] = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair
                self.drink_names.append(each_drink[self.recipe_name])  # Keep a list of all the drink names
                temp_list = self.drinks[each_drink[self.recipe_name]]
            total_volume = 0.0
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
        myFile.close()

        return self

    #############################################
    #     Create pumps linked to ingredients    #
    #############################################
    def link_to_motors(self):
        temp_ingr_list = iter(self.ingr_list)
        # We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
        for each_motor in range(1, 13):
            each_ingredient = temp_ingr_list.next() # Go through all the ingredients by name
            # This is a calibration factor -- more info in Motors.dispense()
            calibration_oz = float(self.calibration_values[each_ingredient])
            self.ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_oz ) # Create the pump
            self.valid_ingr_list.append(each_ingredient) # Add the pump to the list of valid ingredients

    #############################################################
    # This prints all the ingredients, not including 'Recipe'   #
    #############################################################
    # Note: since the Calibration and Prime lines are not actually removed, these will also print
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

    def log(self, message ):
        self.command_log.info( message )

    # This primes every pump al at once.
    def prime_all(self, percent = 100):
        self.command_log.info('Prime all')
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].prime(self.prime_values[each_ingr] * percent/100)
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].wait_until_done()

    def purge_all(self, direction="forward"):
        self.command_log.info("Purge all {}".format(direction))
        if direction in ["forward"]:
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].forward_purge(self.prime_values[each_ingr])
        else:
            for each_ingr in self.valid_ingr_list:
                self.ingr_pumps[each_ingr].reverse_purge(self.prime_values[each_ingr] * 1.25)
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].wait_until_done()

    # This dispenses 1.0oz for every pump -- should come out to 12oz or 1.5C
    def checksum_calibration(self):
        log_str = "" # Keep track of all liquids dispensed in the log
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].dispense(1.0)
            # log_str += "," + str(1.0) # Add to the old prime value
            log_str += ",{0:.2f}".format(1.0)
        for each_ingr in self.valid_ingr_list:
            self.ingr_pumps[each_ingr].wait_until_done()
        self.command_log.info("Executing Checksum,{}".format( log_str ))
        self.drink_log.info("Checksum,{}".format( log_str ))

    # This is for calibrating the prime sequence
    #   it prints out a new line that can be copy and pasted into the .csv file
    def tiny_prime(self):
        percent = 90
        if self.my_yesno.is_yes("Prime the pumps at {} percent?".format(percent)):
            self.my_yesno.is_yes("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            self.prime_all(percent)
        pump_number = 0 # Use this to print the pump number
        # Creat a handy new line for the .csv file to paste in
        total_string = "Prime,"
        tiny_str = "Tiny prime, "
        # Go through all the pumps
        for each_ingr in self.valid_ingr_list:
            pump_number += 1 # Number the pumps for convenience
            total_tiny = 0 # Total extra priming added
            # While the user wants more time priming
            while self.my_yesno.is_yes("More for Pump #" + str(pump_number) + " Name: " + str(each_ingr) + "?" ):
                # Add this amount to the prime time
                self.ingr_pumps[each_ingr].prime(0.1)
                total_tiny = total_tiny + 0.1 # Keep track of all added
            # total_string += str(total_tiny + self.prime_values[each_ingr]) + "," # Add to the old prime value
            total_string += "{0:.2f},".format((total_tiny + self.prime_values[each_ingr]))  # Add to the old prime value
            if total_tiny == 0.0:
                tiny_str += "{},".format(int(total_tiny))  # Show which ingredients needed tiny priming
            else:
                tiny_str += "{0:.2f},".format(total_tiny)  # Show which ingredients needed tiny priming
        print total_string # Print the handy string so it can be copy and pasted into the .csv file
        self.command_log.info("Tiny prime: {}".format(total_string))
        self.command_log.info("Tiny prime (pumps): {}".format(tiny_str))

    def calibrate(self):
        new_calibration_string = "Calibration"
        if not self.my_yesno.is_yes("Have all the pumps been primed?"):
            self.my_yesno.is_yes("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            self.prime_all()

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
        self.drink_log.info("Calibrated{}".format(log_str))

    #############################################################
    # Print the menu                                            #
    #############################################################
    def print_menu(self):
        print "********************   Menu of drinks   ********************"
        for each_drink in self.drink_names:
            print each_drink


    #############################################################
    # Make the drink!                                           #
    #############################################################
    def make_drink(self, my_drink, max_cocktail_volume = 4.0):
        scaled_to_fit_glass = max_cocktail_volume / self.drinks[my_drink][self.total_vol_key]
        print "********************   Making: ", my_drink, " scaled by {0:.2f}".format(scaled_to_fit_glass), "  ********************"
        print "Stats: total original volume: ", self.drinks[my_drink][self.total_vol_key], \
                " scaled by {0:.2f}".format(scaled_to_fit_glass), \
                " max cocktail volume ", max_cocktail_volume
                # " scaled by ", scaled_to_fit_glass, \
        # Start all the pumps going
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
        # Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in self.valid_ingr_list:
            if float(self.drinks[my_drink][each_ingredient]) > 0.0:
                self.ingr_pumps[each_ingredient].wait_until_done()
        self.command_log.info("{}{}".format(my_drink, log_str))
        self.drink_log.info("{}{}".format(my_drink, log_str))

