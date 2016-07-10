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
    RFID_reader.run(wait_for_clear = True, delay_for_clear = 5) # True waits until the reader has no card before it begins reading

    my_drink_ID = RFID_reader._card_uid

    if not RFID_reader._card_uid == None:
        print "********************    ID found:", my_drink_ID, "    ********************"
    else: # Keyboard interrupt
        print # This keeps the next few lines from printing after the CTRL-C

    # WARNING!!!  HARD CODED DRINK NAMES!!!! Kiki
    my_drink = "test all"
    # elif my_drink_ID == "04380edafe1f80":  # Charlotte's Clipper card
    # elif my_drink_ID == "045f8552334680":  # Kiki's Clipper card
    # elif my_drink_ID == "044e906a502d80":  # Sam's Clipper card
    # elif my_drink_ID == "0496a589ba578c":  # tiny little RFID tag -- tapes to black bottle opener
    # elif my_drink_ID == "0496a589ba60a0":  # tiny little RFID tag -- tapes to black bottle opener
    # elif my_drink_ID == "0496a589ba56ac":  # tiny little RFID tag -- tapes to black bottle opener
    # elif my_drink_ID == "0496a589ba665a":  # tiny little RFID tag -- tapes to black bottle opener
    # if my_drink_ID == "dc0a723b": # The sample card that came with the device

#    override_cards = ["dc0a723b", "04380edafe1f80", "045f8552334680", "044e906a502d80", "0496a589ba578c", "0496a589ba60a0", "0496a589ba56ac", "0496a589ba665a"]
    override_cards = ["dc0a723b", "04380edafe1f80", "045f8552334680", "044e906a502d80", "0496a589ba578c", "0496a589ba56ac"]
    if my_drink_ID in override_cards: # All the little rectangular RFIDs, all the Clipper cards, and the white card
        print "OVERRIDE!  Found an override RFID tag -- going into manual mode."
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

    elif my_drink_ID == "ecf5dea1":
        print "Found Tall freaky lady"
        my_drink = "Pieces of Eight"
    elif my_drink_ID == "8ca3dba1":
        print "Found the tan bottle opener"
        my_drink = "Hurricane"
    elif my_drink_ID == "bc7adba1":
        print "Found the black bottle opener"
        my_drink = "Outrigger"
    elif my_drink_ID == "1cbfdba1":
        print "Found the BIG BUTT brown Hawaiin idol"
        my_drink = "Hawaiian Eye"
    elif my_drink_ID == "0cd9dea1":
        print "Found the black Hawaiin idol"
        my_drink = "Trader Vic Grog"
    elif my_drink_ID == "bc5bdca1":
        print "Found the tall black idol"
        my_drink = "Scorpion"
    elif my_drink_ID == "6ce7dea1":
        print "Found the seahorse"
        my_drink = "Mai Tai"
    elif my_drink_ID == "3c62dba1":
        print "Found the Lady Virgin"
        my_drink = "Tail-less Scorpion"
    elif my_drink_ID == "ac5fdba1":
        print "Found the Chief!!!"
        my_drink = "Chief Lapu Lapu"
    elif my_drink_ID == "0496a589ba60a0":
        print "Smoke test"
        my_drink = "Smoke test"
    elif my_drink_ID == None:
        print "Keyboard inturrupt."
        my_drink = "Exit"
    else:
        print "CARD NOT FOUND!!! RFID: ", my_drink_ID
        my_drink = "new card"


# Assert: a valid drink name has been generated
    if my_drink in ["Kill", "Exit", "exit", "X", "x"]:
        print "I'm done!"
        break
    elif my_drink in ["Smoke test"]:
	print "Found Smoke test"
        my_recipes.smoke_test()
    elif my_drink not in my_recipes.drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    # Assert: a valid drink name has been generated
    else:
        my_recipes.make_drink(my_drink)



