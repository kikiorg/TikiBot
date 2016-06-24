#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv

import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader
import time

# The Motors Class that does threading and other cool stuff.
from Motors import Motors
from Recipes import Drink_Recipes

#############################################
# To Do List for this file:                 #
#############################################
# DONE -- Restructure Shutdown command:
#   Instead of a set routine, this should have a menu of steps
#   The user can press [Enter] to go ahead with the correct next step
#   Or the user can enter a number to repeat or skip to a step.
#   This will give a lot more control over shutdown, handling more contingencies
#
# Error checking:
#   NOT DONE -- Check for the existence of the Calibration line -- if it doesn't exist, then use defaults
#   NOT DONE -- Check for the existence of the Prime line -- if it doesn't exist, then use defaults
#   DONE -- Check for strings vs floats vs ints and handle the error
#   Standardize the above setting of the default -- make this a def
# Constants: change any hard coded constants to global named constants
# Integration: Possibly integrate this entire file into the original DrinkBot.py
# DONE -- Make yesno into its own function, maybe yesno("message", "no") for default no -- don't duplicate effort

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
my_recipes = Drink_Recipes()
my_recipes.get_recipes_from_file('TikiDrinks.csv')
my_recipes.link_to_motors()


"""
# Open the spreadsheet.
myFile = open('TikiDrinks.csv', 'r')

# Read the file into a Dictionary type -- this is useful for spreadsheet configurations of CSV data
recipe_book = csv.DictReader(myFile)

# We are appending to all of these lists, so we need to create them as empty to start
# We need only the ingredient list here -- a barebones list of everything
ingr_list = []  # This is a list of all ingredients that we have hooked up by name

# Grab a copy of all the ingredient names (which are the top row of the file, also known as the fieldnames in Dict land
for each_ingredient in recipe_book.fieldnames:
    ingr_list.append(each_ingredient)
# This is the upper left entry.  Meaning, this is the title of the first column -- which is the drink names
# If all goes well, this should be the word "Recipe"
# I'm not hard coding the word "Recipe" in case this name changes in the file
recipe_name = ingr_list[0]
# The first row is all the ingredients, but the first entry is the first column title "Recipes"
# This is a pesky exception, so to make it clean, we remove that column title 
ingr_list.remove(recipe_name)

calibration_list = recipe_book.next()
calibration_values = {}  # Start with an empty list, so we can append each ingredient Key:Value pair
# Create the prime list for all ingredients
prime_list = recipe_book.next()
prime_values = {}  # Start with an empty list, so we can append each ingredient Key:Value pair
# Create the calibration list for all ingredients
# CHECK ERROR: if this line is not the calibration line, then force the defaults
if calibration_list[recipe_name] not in ["Calibration"]:
    print "Error: no Calibration line found in the .csv file.  Substituting defaults for all calibration!"
    for each_value in ingr_list:
        calibration_values[each_value] = Motors.calibration_default
    # Since the Calibration line was not found, it might be the Prime line instead
    prime_list = calibration_list
else:
    for each_value in ingr_list:
        # Grab all the calibration values -- note, do not keep this as an actual recipe
        if calibration_list[each_value] is not '' or calibration_list[each_value] == 0.0:
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            calibration_values[each_value] = Motors.calibration_default
        elif calibration_list[each_value].isdigit():
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            calibration_values[each_value] = float(calibration_list[each_value])
        else:
            try:
                calibration_values[each_value] = float(calibration_list[each_value])
            except ValueError:
                print "Error: calibration_list[each_value] - ", each_value, " ", calibration_list[each_value], "is not a number.  Substituting default: ", Motors.calibration_default
                calibration_values[each_value] = Motors.calibration_default

# CHECK ERROR: if this line is not the prime line, then force the defaults
if prime_list[recipe_name] not in ["Prime"]:
    print "Error: no Prime line found in the .csv file.  Substituting defaults for all prime times!"
    for each_value in ingr_list:
        prime_values[each_value] = Motors.prime_seconds_default
else:
    for each_value in ingr_list:
        # Grab all the prime values -- note, do not keep this as an actual recipe
        if prime_list[each_value] is not '' or prime_list[each_value] == 0.0:
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            prime_values[each_value] = Motors.prime_seconds_default
        elif prime_list[each_value].isdigit():
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            prime_values[each_value] = float(prime_list[each_value])
        else:
            try:
                prime_values[each_value] = float(prime_list[each_value])
            except ValueError:
                print "Error: prime_list[each_value] - ", each_value, " ", prime_list[each_value], "is not a number.  Substituting default: ", Motors.prime_seconds_default
                prime_values[each_value] = Motors.prime_seconds_default
"""
"""
# KIKI CHECK FOR EXISTANCE OF THIS LINE!!!!  MAKE DEFAULTS!!!
prime_list = recipe_book.next()
prime_values = {}  # Start with an empty list, so we can append each ingredient Key:Value pair
for each_value in ingr_list:
    # Grab all the prime values -- note, do not keep this as an actual recipe
    if prime_list[each_value] is not '':
        # ASSERT: add assert that this is a value -- Kiki
        prime_values[each_value] = float(prime_list[each_value])
    else:
        # The .csv file has nothing for this cell, so use a default value
        prime_values[each_value] = Motors.prime_seconds_default
"""
"""
# Done getting the info from the file.
myFile.close()

def calibrate_pumps():
    for each_pump in ingr_list:
        # This will force each pump to be calibrated by the user
        each_pump = Motors.not_calibrated

def prime_all_pumps(direction = "forward"):
    if direction in ["forward"]:
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].forward_purge(prime_values[each_ingr])
    else:
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].reverse_purge(prime_values[each_ingr] * 1.25)
    for each_ingr in valid_ingr_list:
        ingr_pumps[each_ingredient].wait_until_done()


#######################
#     DRINK MAKER     #
#######################


ingr_pumps = {}
valid_ingr_list = []
temp_ingr_list = iter(ingr_list)
# This assigns pumps to Hat motors
# We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
for each_motor in range(1, 13):
    each_ingredient = temp_ingr_list.next()
    calibration_factor = my_recipes.calibration_values[each_ingredient]
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_factor )
    valid_ingr_list.append(each_ingredient)
"""

def is_yes(message):
    yesno = raw_input(message + " [Y/n] ")
    while yesno not in ["Y", "y", "YES", "yes", "Yes", "N", "n", "NO", "no", "No", ""]:
        yesno = raw_input(message)
    return yesno in ["Y", "y", "YES", "yes", "Yes", ""]

def is_no(message):
    yesno = raw_input(message + " [y/N] ")
    while yesno not in ["Y", "y", "YES", "yes", "Yes", "N", "n", "NO", "no", "No", ""]:
        yesno = raw_input(message)
    return yesno in ["N", "n", "NO", "no", "No", ""]

my_drink_ID = None
my_command = ""

while my_command not in ["end" "End", "e", "E", "exit", "Exit", "x", "X", "quit", "Quit", "q", "Q"]:

    logger = logging.getLogger("cardhandler").info

    print "List of commands: "
    print "[C]alibrate: "
    print "[G]lobal calibration check: "
    print "    This dispenses all pumps for 1oz -- more like a fast checksum"
    print "[P]rime -- prime all pumps"
    print "[T]iny Prime -- do small, incremental priming of each pump (tedius)"
    print "[S]hutdown full phase -- this includes these steps:"
    print "    Reverse liquids -- then wait"
    print "    Prime 2x with water -- then wait, purge with air, wait"
    print "    Prime with bleach -- then wait, purge with air, wait"
    print "    Prime 2x with water -- then wait, purge with air, DONE"
    print "E[X]it or [Q]uit"
    print
    my_command = raw_input("Please enter your command: ")

    # my_drink = raw_input("Enter Drink Name:  ")
    if my_command in ["P", "p", "prime", "Prime"]:
        my_recipes.prime_all()
    elif my_command in ["G", "g", "global", "Global"]:
        my_recipes.quick_check_calibration()
    elif my_command in ["T", "t", "tiny prime", "Tiny Prime"]:
        if True:
            my_recipes.tiny_prime()
        else:
            # Overview:
            # Go through all the pumps and make sure each is primed
            # Creat a handy new line for the .csv file to paste in
            # Go through all the pumps
                # Number the pumps for convenience; Total extra priming added
                # While the user wants more time priming
                    # Add this amount to the prime time; Keep track of all added
                # Add to the old prime value
            # Print the handy string so it can be copy and pasted into the .csv file

            i = 0
            # Creat a handy new line for the .csv file to paste in
            total_string = "Prime,"
            # Go through all the pumps
            for each_ingr in my_recipes.valid_ingr_list:
                i += 1 # Number the pumps for convenience
                total_tiny = 0 # Total extra priming added
                # While the user wants more time priming
                while is_yes("More for Pump #" + str(i) + " Name: " + str(each_ingr) + "?" ):
                    # Add this amount to the prime time
                    my_recipes.ingr_pumps[each_ingr].prime(0.1)
                    total_tiny = total_tiny + 0.1 # Keep track of all added
                total_string += str(total_tiny + my_recipes.prime_values[each_ingr]) + "," # Add to the old prime value
            print total_string # Print the handy string so it can be copy and pasted into the .csv file

    elif my_command in ["C", "c", "Calibrate", "calibrate"]:
        new_calibration_string = "Calibration,"
        if is_no(("Have all the pumps been primed?")):
            is_yes("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            my_recipes.prime_all_pumps()

        i = 0
        for each_ingr in my_recipes.valid_ingr_list:
            i = i + 1
            if is_yes(("Force calibrate Pump #" + str(i) + " [" + each_ingr + "]?")):
                my_recipes.ingr_pumps[each_ingr].force_calibrate_pump()
            new_calibration_string += str(ingr_pumps[each_ingr].calibration_oz) + ","
        print new_calibration_string

    elif my_command in ["S", "s", "Shutdown", "shutdown"]:
        not_done = True
        step = 0
        steps_list = ["Reverse liquids",
                      "Prime 2x with water",
                      "Purge with air",
                      "Prime with bleach",
                      "Purge with air",
                      "Prime 2x with water",
                      "Purge with air",
                      "DONE"]
        # Print the instructions
        i = 0
        for each_step in steps_list:
            print i, ")", each_step
            i += 1
        print "*** Executing:"

        while not_done:
            # Print the instructions
            #i = 0
            #for each_step in steps_list:
            #    if i != step:
            #        print i, ")", each_step
            #    else:
            #        print "X )", each_step
            #    i += 1
            print "***", step, ")", steps_list[step]

            if step == 0:
                #prime_all_pumps("reverse")
                print "    Put hoses into rinse water."
            elif step == 1:
                #prime_all_pumps()
                #prime_all_pumps()
                print "    Remove the hoses to allow air to enter."
            elif step == 2:
                #prime_all_pumps()
                print "    Put hoses into bleach water."
            elif step == 3:
                #prime_all_pumps()
                #prime_all_pumps()
                print "    Remove the hoses to allow air to enter."
            elif step == 4:
                #prime_all_pumps()
                print "    Put hoses into rinse water."
            elif step == 5:
                #prime_all_pumps()
                #prime_all_pumps()
                print "    Remove the hoses to allow air to enter"
            elif step == 6:
                #prime_all_pumps()
                print "    YOU ARE NOW READY TO SHUT DOWN"
            my_step = raw_input("    Press Enter for next step, or step #, or CTRL-C to end) ")
            while not my_step == "" and not my_step.isdigit():
                my_step = raw_input("    Press Enter for next step, or step #, or CTRL-C to end) ")
            if my_step == "":
                step += 1
            else: # ASSERT my_step.isdigit():
                step = int(my_step)
            if step >= len(steps_list) - 1:
                not_done = False

    elif my_command in ["X", "x", "E", "e", "Q", "q", "Exit", "exit", "Quit", "quit"]:
        print "I'm done!"
        break
    else:
        print "This is not a command I understand."

