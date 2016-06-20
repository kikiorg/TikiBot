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
valid_ingr_list = []
temp_ingr_list = iter(ingr_list)
# We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
for each_motor in range(1, 13):
    each_ingredient = temp_ingr_list.next()
    calibration_factor = float(drinks["Calibration"][each_ingredient])
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_factor )
    valid_ingr_list.append(each_ingredient)

#######################
# PRINT INGREDIENTS   #
#######################
# This prints all the ingredients, including 'Recipe'
# RFID_reader = NFCReader()
my_drink_ID = None
my_drink = ""

while True:
#    RFID_reader.run()

    print ("***************************   I can make these drinks:  ")
    for each_drink in drink_names:
        print each_drink

    logger = logging.getLogger("cardhandler").info
    # print "Kiki: Before init"
    #my_drink_ID = None

    RFID_reader = NFCReader(logger)
    time_polling = time.mktime(time.gmtime())
    RFID_reader.run()

    while RFID_reader._card_uid != None:
        if time.mktime(time.gmtime()) - time_polling > 120:
            print "Will die in ", 153-(time.mktime(time.gmtime()) - time_polling), " seconds!"
        RFID_reader.run()

    # Assert: RFID_reader._card_uid == None
    while RFID_reader._card_uid == None:
        #if time.mktime(time.gmtime()) - time_polling > 120:
        #    print "Will die in ", 153-(time.mktime(time.gmtime()) - time_polling), " seconds!"
        RFID_reader.run()
    print "*****************************   Now throw the idol into the volcano!!!"
    print "Here's the ID: ", RFID_reader._card_uid
    # Assert: RFID_reader._card_uid != None
    my_drink_ID = RFID_reader._card_uid
    #print "Encode (Kiki):", RFID_reader._card_uid, " drink: ", my_drink_ID == "045f8552334680"

    # WARNING!!!  HARD CODED DRINK NAMES!!!! Kiki
    my_drink = "test all"
    if my_drink_ID == "dc0a723b": # The sample card that came with the device
        print "Found the large white sample card"
        my_drink = "Exit" # This is the test drink name --Kiki crossing fingers!!!
    elif my_drink_ID == "04380edafe1f80":  # Charlotte's Clipper card
        print "Found Charlotte's Clipper card"
        my_drink = "Prime"
        my_drink = "Pieces of Eight"
    elif my_drink_ID == "045f8552334680":  # Kiki's Clipper card
        print "Found Kiki's Clipper card"
	my_drink = "Prime"
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
    else:
        print "CARD NOT FOUND!!! RDFI: ", my_drink_ID
        my_drink = "ta"


    # my_drink = raw_input("Enter Drink Name:  ")
    if my_drink in ["Prime"]:
	for each_ingr in valid_ingr_list:
            ingr_pumps[each_ingr].prime()
#        while True:
#            my_drink = raw_input("Which pump to prime (stop to stop)?  ")
#            while my_drink not in ingr_list and my_drink != "stop":
#                print "I don't have a pump for " + my_drink
#                print "Type stop to not prime a pump."
#                my_drink == raw_input("Which pump to prime (stop to stop)?")
#            ingr_pumps[my_drink].prime()
            
    elif my_drink in ["test all2"]:
	i = 1
        for each_ingredient in valid_ingr_list:
            print "Pump number:", i, " name: ", each_ingredient
            ingr_pumps[each_ingredient].dispense(2.0)
	    time.sleep(5)
	    i = i + 1
    elif my_drink in ["Kill", "Exit", "exit", "X", "x"]:
        print "I'm done!"
        break
    elif my_drink not in drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    else:
        print "***************************   Making this drink: ", my_drink
        # Start all the pumps going
        for each_ingredient in drinks[my_drink]:
            if drinks[my_drink][each_ingredient] > 0:
                print each_ingredient + ": " + drinks[my_drink][each_ingredient]
                #print "Normalized: ", float(drinks[my_drink][each_ingredient]) * ingr_pumps[each_ingredient].calibration_factor, " seconds."
                if each_ingredient in valid_ingr_list:
                    ingr_pumps[each_ingredient].dispense(float(drinks[my_drink][each_ingredient]))
                else:
                    print "We don't have ", each_ingredient, " on a pump in this DrinkBot."
        # Wait for all the pumps to complete before moving on -- technical: this calls .join() on each thread
        for each_ingredient in drinks[my_drink]:
            if each_ingredient in valid_ingr_list and drinks[my_drink][each_ingredient] > 0:
                ingr_pumps[each_ingredient].wait_until_done()

