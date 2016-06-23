#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv

import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors
from Recipes import Drink_Recipes

#############################################
# To Do List for this file:                 #
#############################################
# Log all drinks dispensed by date
#   Ask the user at the start of each run what the event is
#   Make a class for the logging of drinks
#       You pass in a string, and it outputs a date and the string
# Error checking:
#   Check for the existence of the Calibration line -- if it doesn't exist, then use defaults
#   Check for the existence of the Prime line -- if it doesn't exist, then use defaults
#   Check for strings vs floats vs ints and handle the error
# Constants: change any hard coded constants to global named constants
# Make yesno into its own function, maybe yesno("no") for default no -- don't duplicate effort

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
my_recipes = Drink_Recipes()
my_recipes.get_recipes_from_file('TikiDrinks.csv')
my_recipes.print_recipes()

# Open the spreadsheet.
myFile = open('TikiDrinks.csv', 'r')

# Read the file into a Dictionary type -- this is useful for spreadsheet configurations of CSV data
recipe_book = csv.DictReader(myFile)

# We are appending to all of these lists, so we need to create them as empty to start
drinks = {}  # This is a list of drinks, which includes a list of key:value pairs of all the ingredient amounts
drink_names = []  # This is simply a list of all the drink names -- the "menu" as it were
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

#####################################
# Create the list of drink recipes  #
#####################################
# This is a list of drinks and each drink has a list of Key:Value pairs that are the ingredient:amount
for each_drink in recipe_book:
    drinks[each_drink[recipe_name]] = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair
    drink_names.append(each_drink[recipe_name])  # Keep a list of all the drink names

    # Now go through all the ingredients for this drink, and append the amounts into the drink
    for each_ingredient in ingr_list:
        # Append the ingredient amount to the recipe list
        if each_drink[each_ingredient] is not '':
            # Example: drinks["Mai Tai]["Orgeat"] = ".25oz"
            # "Mai Tai" = each_drink[recipe_name] -- goes through every drink
            # "Orgeat" = each_ingredient -- goes through all ingredients
            # ".25oz" = each_drink[each_ingredient] -- goes through every amount for that drink
            drinks[each_drink[recipe_name]][each_ingredient] = each_drink[each_ingredient]
        else:
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            drinks[each_drink[recipe_name]][each_ingredient] = 0

# Done getting the info from the file.
myFile.close()

# Remove these fake recipes from the list
# Note: this leaves the data intact in the drinks[] list
drink_names.remove("Calibration")
drink_names.remove("Prime")

#############################################################
# This prints all the ingredients, not including 'Recipe'   #
#############################################################
# Note: since the Calibration and Prime lines are not actually removed, these will also print
def print_recipes():
    for each_drink in drink_names:
        print each_drink
        for each_ingredient in drinks[each_drink]:
            # Skip the ingredients that are not used in this recipe
            # Comment this out of you want empty entries to be printed
            if drinks[each_drink][each_ingredient] is not '':
                print each_ingredient + ': ', drinks[each_drink][each_ingredient]

#############################################
#     Create pumps linked to ingredients    #
#############################################
ingr_pumps = {}
valid_ingr_list = []
temp_ingr_list = iter(ingr_list)
# We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
for each_motor in range(1, 13):
    each_ingredient = temp_ingr_list.next() # Go through all the ingredients by name
    # This is a calibration factor -- more info in Motors.dispense()
    calibration_oz = float(drinks["Calibration"][each_ingredient])
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_oz ) # Create the pump
    valid_ingr_list.append(each_ingredient) # Add the pump to the list of valid ingredients

my_drink_ID = None
my_drink = ""

#############################################
#     Now start polling the RFID reader     #
#############################################
while True:

    print "********************   Menu of drinks   ********************"

    for each_drink in drink_names:
        print each_drink

    logger = logging.getLogger("cardhandler").info
    RFID_reader = NFCReader(logger)
    RFID_reader.run(True) # True waits until the reader has no card before it begins reading
    my_drink_ID = RFID_reader._card_uid

    if not RFID_reader._card_uid == None:
        print "********************    Remove idol!    ********************"
        print "Here's the ID: ", my_drink_ID
    else: # Keyboard interrupt
        print # This keeps the next few lines from printing after the CTRL-C

    # WARNING!!!  HARD CODED DRINK NAMES!!!! Kiki
    my_drink = "test all"
    if my_drink_ID == "dc0a723b": # The sample card that came with the device
        print "Found the large white sample card"
        my_drink = "Exit" # This is the test drink name --Kiki crossing fingers!!!
    elif my_drink_ID == "04380edafe1f80":  # Charlotte's Clipper card
        print "Found Charlotte's Clipper card"
        my_drink = "Pieces of Eight"
        my_drink = "test"
    elif my_drink_ID == "045f8552334680":  # Kiki's Clipper card
        print "Found Kiki's Clipper card"
        my_drink = "Prime"
        my_drink = "Reverse purge"
    elif my_drink_ID == "8ca3dba1":  # round sample RFID tag -- taped to tan bottle opener
        print "Found the round RFID card"
        my_drink = "Hurricane"
    elif my_drink_ID == "0496a589ba578c":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the tiny rectangular card"
        my_drink = "Outrigger"

    elif my_drink_ID == "1cbfdba1":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the brown Hawaiin idol"
        my_drink = "Hawaiian Eye"
    elif my_drink_ID == "0cd9dea1":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the black Hawaiin idol"
        my_drink = "Trader Vic Grog"
    elif my_drink_ID == "bc5bdca1":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the tall black idol"
        my_drink = "Scorpion"
    elif my_drink_ID == "0496a589ba60a0":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the seahorse"
        my_drink = "Mai Tai"
    elif my_drink_ID == "0496a589ba56ac":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the Lady Virgin"
        my_drink = "Tail-less Scorpion"
    elif my_drink_ID == "0496a589ba665a":  # tiny little RFID tag -- tapes to black bottle opener
        print "Found the Chief!!!"
        my_drink = "Chief Lapu Lapu"
    elif my_drink_ID == None:  # tiny little RFID tag -- tapes to black bottle opener
        print "Keyboard inturrupt."
        my_drink = "Exit"
    else:
        print "CARD NOT FOUND!!! RFID: ", my_drink_ID
        my_drink = "new card"


# Assert: a valid drink name has been generated
    if my_drink in ["Kill", "Exit", "exit", "X", "x"]:
        print "I'm done!"
        break
    elif my_drink not in drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    # Assert: a valid drink name has been generated
    else:
        print "******************** Making this drink  ********************", my_drink
        # Start all the pumps going
        for each_ingredient in drinks[my_drink]:
            if float(drinks[my_drink][each_ingredient]) > 0.0:
                print each_ingredient + ": " + drinks[my_drink][each_ingredient]
                if each_ingredient in valid_ingr_list: # Some recipes might have ingredients not added to motors
                    ingr_pumps[each_ingredient].dispense(float(drinks[my_drink][each_ingredient]))
                else:
                    print "We don't have ", each_ingredient, " on a pump in this DrinkBot."
        # Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in drinks[my_drink]:
            if each_ingredient in valid_ingr_list and float(drinks[my_drink][each_ingredient]) > 0.0:
                ingr_pumps[each_ingredient].wait_until_done()


