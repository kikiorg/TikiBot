#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv

import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader
import time

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
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


# for each_drink in recipe_book:
#     drinks[each_drink[recipe_name]] = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair

# KIKI CHECK FOR EXISTANCE OF THIS LINE!!!!  MAKE DEFAULTS!!!
calibration_list = recipe_book.next()
calibration_values = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair
# Now go through all the ingredients for this drink, and append the amounts into the drink
for each_value in ingr_list:
    # print "ingr: " , each_ingredient
    # Skip the ingredients that are not used in this recipe
    # Comment this out of you want empty entries to be added
    if calibration_list[each_value] is not '':
        calibration_values[each_value] = float(calibration_list[each_value])
    else:
        # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
        calibration_values[each_value] = 0.0


# KIKI CHECK FOR EXISTANCE OF THIS LINE!!!!  MAKE DEFAULTS!!!
purge_list = recipe_book.next()
purge_values = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair
# Now go through all the ingredients for this drink, and append the amounts into the drink
for each_value in ingr_list:
    # print "ingr: " , each_ingredient
    # Skip the ingredients that are not used in this recipe
    # Comment this out of you want empty entries to be added
    if purge_list[each_value] is not '':
        # ASSERT: add assert that this is a value -- Kiki
        purge_values[each_value] = float(purge_list[each_value])
    else:
        # The .csv file has nothing for this cell, so use a default value
        purge_values[each_value] = Motors.prime_seconds

# Done getting the info from the file.
myFile.close()

def calibrate_pumps():
    for each_pump in ingr_list:
        # This will force each pump to be calibrated by the user
        each_pump = Motors.not_calibrated

def prime_all_pumps(direction = "forward"):
    if direction in ["forward"]:
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].forward_purge(purge_values[each_ingr])
    else:
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].reverse_purge(purge_values[each_ingr] * 1.25)
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
    calibration_factor = calibration_values[each_ingredient]
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_factor )
    valid_ingr_list.append(each_ingredient)

my_drink_ID = None
my_command = ""


while my_command not in ["end" "End", "e", "E", "exit", "Exit", "x", "X", "quit", "Quit", "q", "Q"]:
#    RFID_reader.run()

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
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].prime(purge_values[each_ingr] - 2)
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].wait_until_done()
    elif my_command in ["G", "g", "global", "Global"]:
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].dispense(1.0)
        for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].wait_until_done()
    elif my_command in ["T", "t", "tiny prime", "Tiny Prime"]:
        # Go through all the pumps and make sure each is primed
        i = 0
        total_string = ""
        for each_ingr in valid_ingr_list:
            i += 1
            print "More for Pump #", i, " Name: ", each_ingr, "?"
            yesno = raw_input( "Enter [y/n]: " )
            total_tiny = 0
            while yesno not in ["Y", "y", "Yes", "YES", "yes"]:
#                ingr_pumps[each_ingr].prime(purge_values[each_ingr]/20)
#                ingr_pumps[each_ingr].prime(0.025)
#                total_tiny = total_tiny + 0.025
                ingr_pumps[each_ingr].prime(float(yesno))
                total_tiny = total_tiny + float(yesno)
                print "More for Pump #", i, " Name: ", each_ingr, "?"
                yesno = raw_input("Enter [y/n]: ")
            print "Total extra priming for " + each_ingr + ": " + str(total_tiny)
            total_string += str(total_tiny) + ","
        print total_string

    elif my_command in ["C", "c", "Calibrate", "calibrate"]:
        new_calibration_string = "Calibration,"
        yesno = raw_input("Have all the pumps been primed? [y/n] ")
        if yesno not in ["Y", "y", "Yes", "YES", "yes"]:
            yesno = raw_input("Press enter to prime all the pumps at once. [CTRL-C to exit and not prime the pumps] ")
            prime_all_pumps()

        i = 0
        for each_ingr in valid_ingr_list:
            i = i + 1
            yesno = raw_input("Force calibrate Pump #" + str(i) + " [" + each_ingr + "]? [y/n] ")
            if yesno in ["Y", "y", "yes", "YES", "Yes"]:
                ingr_pumps[each_ingr].force_calibrate_pump()
            new_calibration_string += str(ingr_pumps[each_ingr].calibration_oz) + ","
        print new_calibration_string

    elif my_command in ["S", "s", "Shutdown", "shutdown"]:
        # Reverse all the liquid back into the bottles
        print "Reverse purging liquids back to bottles."
        prime_all_pumps("reverse")
        yesno = raw_input("Put hoses into rinse water then press Enter. (CTRL-C to end) ")

        # Run water through the tubes -- run this twice
        print "1) Prime pumps with water."
        prime_all_pumps()
        print "2) Purge pumps with water."
        prime_all_pumps()
        yesno = raw_input("Remove the hoses to allow air to enter then press Enter. (CTRL-C to end) ")

        # Purge with air
        print "Purge tubes with air."
        prime_all_pumps()
        yesno = raw_input("Put hoses into bleach water then press Enter. (CTRL-C to end) ")

        # Run bleach water through the tubes -- run this twice
        print "1) Prime pumps with bleach."
        prime_all_pumps()
        print "2) Purge pumps with bleach."
        prime_all_pumps()
        yesno = raw_input("Remove the hoses to allow air to enter then press Enter. (CTRL-C to end) ")
        # Purge with air
        print "Purge tubes with air."
        prime_all_pumps()
        yesno = raw_input("Put hoses into rinse water then press Enter. (CTRL-C to end) ")

        # Run water through the tubes -- run this twice
        print "1) Prime pumps with water."
        prime_all_pumps()
        print "2) Purge pumps with water."
        prime_all_pumps()
        yesno = raw_input("Remove the hoses to allow air to enter then press Enter. (CTRL-C to end) ")

        # Purge with air
        print "Purge tubes with air."
        prime_all_pumps()
        yesno = raw_input("YOU ARE NOW READY TO SHUT DOWN. (CTRL-C to end) ")

    elif my_command in ["X", "x", "E", "e", "Q", "q", "Exit", "exit", "Quit", "quit"]:
        print "I'm done!"
        break
    else:
        print "This is not a command I understand."

