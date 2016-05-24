#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv
<<<<<<< HEAD
import atexit

import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader

# Kiki's awesome Motors Class that does threading and other cool stuff!
from Motors import Motors, ThreadMe

####### These are needed for the Bot interrupts -- to start and stop the motors on a timer
from twisted.internet import task
from twisted.internet import reactor

=======
# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors
>>>>>>> 6d99b6d6bd0806edcb56d9f617af9fdce397d267

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
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
    # print each_drink[recipe_name]
    # Now go through all the ingredients for this drink, and append the amounts into the drink
    for each_ingredient in ingr_list:
        # print "ingr: " , each_ingredient
        # Skip the ingredients that are not used in this recipe
        # Comment this out of you want empty entries to be added
        if each_drink[each_ingredient] is not '':
            # Explanation:
            # tl;dr eg: drinks["Mai Tai]["Orgeat"] = ".25oz"
            # "Mai Tai" = each_drink[recipe_name]
            # "Orgeat" = each_ingredient
            # ".25oz" = each_drink[each_ingredient]
            # Other:
            # recipe_name = "Recipes" or whatever is in the upper left cell
            # each_ingredient runs through all of the ingredients in this drink
            # each_drink is the entire row for that drink, including all the ingredient amounts
            #
            drinks[each_drink[recipe_name]][each_ingredient] = each_drink[each_ingredient]
        else:
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            drinks[each_drink[recipe_name]][each_ingredient] = 0

# Done getting the info from the file.
myFile.close()

# Check if there's a calibration row in the drink recipe .csv file
# If there is not, then enter not_calibrated into each calibration factor
# Note: Why not just calibrate them now?  Because this allows for a Calibration line
# to have individual entries of not_calibrated so the user can recalibrate individual pumps
# simply by entering the number ito the .csv file.

if drinks.get("Calibration") is None:
    print "NO CALIBRATION!!!!"
    for each_ingredient in ingr_list:
        # This will force each pump to be calibrated by the user
        drinks["Calibration"][each_ingredient] = Motors.not_calibrated

drink_names.remove("Calibration")


#############################################################
# This prints all the ingredients, including 'Recipe'       #
#############################################################
# NOTE: This might not work -- needs to be code checked --Kiki
def print_recipes_old():
    for each_drink in recipe_book:
        for each_ingredient in ingr_list:
            # Skip the ingredients that are not used in this recipe
            # Comment this out of you want empty entries to be printed
            if each_drink[each_ingredient] is not '':
                print each_ingredient + ': ' + each_drink[each_ingredient]


def print_recipes():
    for each_drink in drink_names:
        print each_drink
        for each_ingredient in drinks[each_drink]:
            # Skip the ingredients that are not used in this recipe
            # Comment this out of you want empty entries to be printed
            if drinks[each_drink][each_ingredient] is not '':
                print each_ingredient + ': ', drinks[each_drink][each_ingredient]


# print_recipes ()

#######################
#     DRINK MAKER     #
#######################


ingr_pumps = {}
temp_ingr_list = iter(ingr_list)
# We have two hats right now, so 8 pumps -- range is zero indexed, 0-8, starting at 1
for each_motor in range(1, 9):
    each_ingredient = temp_ingr_list.next()
    calibration_factor = drinks["Calibration"][each_ingredient]
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_factor )

#######################
# PRINT INGREDIENTS   #
#######################
# This prints all the ingredients, including 'Recipe'
# RFID_reader = NFCReader()
while True:
#    RFID_reader.run()

    print ("I can make these drinks:  ")
    for each_drink in drink_names:
        print each_drink
    my_drink = raw_input("Enter Drink Name:  ")
    if my_drink == "Prime":
        my_drink = raw_input("Which pump to prime?  ")
        while my_drink not in ingr_list and my_drink != "stop":
            print "I don't have a pump for " + my_drink
            print "Type stop to not prime a pump."
            my_drink == raw_input("Which pump to prime?")
        ingr_pumps[my_drink].prime()
    elif my_drink in ["Exit", "exit", "X", "x"]:
        print "I'm done!"
        break
    elif my_drink not in drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    else:

        logger = logging.getLogger("cardhandler").info
        RFID_reader = NFCReader(logger)
        while NFCReader(logger).run():
            pass

        # Start all the pumps going
        for each_ingredient in drinks[my_drink]:
            if drinks[my_drink][each_ingredient] > 0:
                print each_ingredient + ": " + drinks[my_drink][each_ingredient]
                #print "Normalized: ", float(drinks[my_drink][each_ingredient]) * ingr_pumps[each_ingredient].calibration_factor, " seconds."
                ingr_pumps[each_ingredient].dispense(float(drinks[my_drink][each_ingredient]))
        # Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in drinks[my_drink]:
            if drinks[my_drink][each_ingredient] > 0:
                ingr_pumps[each_ingredient].wait_untill_done()

