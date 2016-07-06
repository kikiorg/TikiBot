#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# DrinkBot:                                 #
#############################################
# This class reads the RFIDs and dispenses drinks:
#############################################

import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader
from SetupBot import Setup

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Recipes import Drink_Recipes
from yesno import yesno

# my_recipes.print_full_recipes()
my_yesno = yesno()
percent_ice = 55.0
cup_size = my_yesno.get_number("What cup size (in ounces) is provided? ")
max_cocktail_volume = cup_size * ( (100.0 - percent_ice) / 100.0) # Subtract out the ice
format_str = "Cup: {f[0]} max cocktail volume: {f[1]} percent cocktail: {f[2]}%"
format_list = [cup_size, max_cocktail_volume,  (100.0 * (100.0 - percent_ice) / 100.0)]
print format_str.format(f=format_list)

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
my_recipes = Drink_Recipes("DrinkBot.py")
my_recipes.get_recipes_from_file('TikiDrinks.csv')
my_recipes.link_to_motors()

my_drink_ID = None
my_drink = ""

#############################################
#     Now start polling the RFID reader     #
#############################################
while True:

    my_recipes.print_menu()

    logger = logging.getLogger("cardhandler").info
    RFID_reader = NFCReader(logger)
    RFID_reader.run(True) # True waits until the reader has no card before it begins reading

    my_drink_ID = RFID_reader._card_uid

    if not RFID_reader._card_uid == None:
        print "********************    ID found:", my_drink_ID, "    ********************"
    else: # Keyboard interrupt
        print # This keeps the next few lines from printing after the CTRL-C

    # WARNING!!!  HARD CODED DRINK NAMES!!!! Kiki
    my_drink = "test all"
    if my_drink_ID == "dc0a723b": # The sample card that came with the device
        print "Found the large white sample card"
        my_drink = "test"
        my_drink = raw_input("Enter a drink from the menu, or [S]etup to enter setup mode: ")
        while my_drink not in my_recipes.drink_names + ["S", "s", "Setup", "setup"]:
            if my_drink in ["Kill", "Exit", "exit", "X", "x"]:
                break
            print "Invalid drink name!"
            my_drink = raw_input("Enter a drink from the menu: ")
        if my_drink in ["S", "s", "Setup", "setup"]:
            print "Setup mode..."
            my_setup = Setup(my_recipes)
            my_setup.setup_menu()

    elif my_drink_ID == "04380edafe1f80":  # Charlotte's Clipper card
        print "Found Charlotte's Clipper card"
        my_drink = "Pieces of Eight"
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
    elif my_drink not in my_recipes.drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    # Assert: a valid drink name has been generated
    elif my_drink in ["S", "s", "Setup", "setup"]:
        pass
    else:
        my_recipes.make_drink(my_drink, max_cocktail_volume)



