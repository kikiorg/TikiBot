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
from subprocess import call

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Recipes import DrinkRecipes
from SoundEffects import SoundEffects
from yesno import yesno

# my_recipes.print_full_recipes()
my_yesno = yesno()

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
print "MassiveDrinks.csv"
#print "TikiDrinks_orig.csv"
#print "KidDrinks.csv"
#drink_file = raw_input("Please enter the drink file name, or [Enter] to use MassiveDrinks.csv: ")
#if drink_file is "":
#    drink_file = "MassiveDrinks.csv"
drink_file = "MassiveDrinks.csv"

# Kiki init and bottles low
my_sound_init_prime = SoundEffects(sound_name="sounds/init_q/init_prime_pumpsQ.wav", channel=1)
my_sound_init_date = SoundEffects(sound_name="sounds/init_q/init_dateQ.wav", channel=1)

my_recipes = DrinkRecipes("DrinkBot.py")
my_recipes.get_recipes_from_file(drink_file)
my_recipes.link_to_pumps()

# Ask user to if they want to prime?
my_sound_init_prime.play_sound()
if not my_yesno.is_no("Prime the pumps?"):
    my_recipes.prime()
my_sound_init_prime.join()

# Ask user to if they want to prime?
#my_sound_init_prime.play_sound()
if not my_yesno.is_no("Take inventory (it's kinda long)?"):
    my_recipes.take_inventory()
#my_sound_init_prime.join()

my_drink_ID = None
my_drink = ""
my_sound_lady = SoundEffects(sound_name="sounds/Scream.wav", channel=1)
my_sound_Howie = SoundEffects(sound_name="sounds/HowieScream.ogg", channel=1)
my_sound_wilhelm = SoundEffects(sound_name="sounds/wilhelm.wav", channel=1)
my_sound_drums = SoundEffects(sound_name="sounds/BoraBora.wav", channel=1, music=True, skip=1300000)

# Neverwas Screams!
my_sound_NW_Kathy1 = SoundEffects(sound_name="sounds/Neverwas/Kathy1.wav", channel=1)
my_sound_NW_Birdbath1 = SoundEffects(sound_name="sounds/Neverwas/Birdbath1.wav", channel=1)
my_sound_NW_Birdbath2 = SoundEffects(sound_name="sounds/Neverwas/Birdbath2.wav", channel=1)
my_sound_NW_Birdbath3 = SoundEffects(sound_name="sounds/Neverwas/Birdbath3.wav", channel=1)
my_sound_NW_Birdbath4 = SoundEffects(sound_name="sounds/Neverwas/Birdbath4.wav", channel=1)
my_sound_NW_Birdbath_monkey = SoundEffects(sound_name="sounds/Neverwas/Birdbath_monkey.wav", channel=1)
my_sound_NW_I_heard_your_prayers = SoundEffects(sound_name="sounds/Neverwas/I_heard_your_prayers.wav", channel=1)
my_sound_NW_Sam1 = SoundEffects(sound_name="sounds/Neverwas/Sam1.wav", channel=1)
my_sound_NW_Sam2 = SoundEffects(sound_name="sounds/Neverwas/Sam2.wav", channel=1)
my_sound_NW_Sam3 = SoundEffects(sound_name="sounds/Neverwas/Sam3.wav", channel=1)
my_sound_NW_Sam4 = SoundEffects(sound_name="sounds/Neverwas/Sam4.wav", channel=1)
my_sound_NW_Victor1 = SoundEffects(sound_name="sounds/Neverwas/Victor1.wav", channel=1)
my_sound_NW_Victor2 = SoundEffects(sound_name="sounds/Neverwas/Victor2.wav", channel=1)
my_sound_NW_Victor3 = SoundEffects(sound_name="sounds/Neverwas/Victor3.wav", channel=1)
my_sound_NW_Victor4 = SoundEffects(sound_name="sounds/Neverwas/Victor4.wav", channel=1)

#############################################
#     Now start polling the RFID reader     #
#############################################

## zzzz TEST!! zzzz ##
#my_recipes.test_lights()


while True:

    my_recipes.print_menu()

    logger = logging.getLogger("cardhandler").info
    RFID_reader = NFCReader(logger)
    my_recipes.hard_off_effects()
    RFID_reader.run2(no_card_for_seconds=5) # True waits until the reader has no card before it begins reading

    my_recipes.ready_to_dispense()
    RFID_reader.run2() # Now, find a card


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
    # elif my_drink_ID == "0496a589ba578c":  # Swan - tiny little RFID tag
    # elif my_drink_ID == "0496a589ba60a0":  # Owl -- tiny little RFID tag
    # elif my_drink_ID == "0496a589ba56ac":  # tiny little RFID tag
    # elif my_drink_ID == "0496a589ba665a":  # White Duck -- tiny little RFID tag
    # if my_drink_ID == "dc0a723b": # The sample card that came with the device
    # elif my_drink_ID == "ac5fdba1": #Old Chief Lapu Lapu
    # SPARE - listed below, last "c52f76ff"
    override_cards = ["dc0a723b", "04380edafe1f80", "045f8552334680", "044e906a502d80", "0496a589ba56ac", "c52f76ff"]
    if my_drink_ID in override_cards: # All the little rectangular RFIDs, all the Clipper cards, and the white card
        print "OVERRIDE!  Found an override RFID tag -- going into manual mode."
        my_recipes.setup_effects()
        my_drink = "test"
        my_drink = raw_input("Enter a drink from the menu, or [S]etup to enter setup mode: ")
        while my_drink not in my_recipes.drink_names + ["S", "s", "Setup", "setup"]:
            if my_drink in ["Kill", "Exit", "exit", "X", "x"]:
                break
            if my_drink in ["S", "s", "Setup", "setup"]:
                break
            print "Invalid drink name!"
            my_drink = raw_input("Enter a drink from the menu: ")
        if my_drink in ["S", "s", "Setup", "setup"]:
            print "Setup mode..."
            my_setup = Setup(my_recipes)
            my_setup.setup_menu()
        my_recipes.hard_off_effects()

    elif my_drink_ID == "6ce7dea1":
        print "Found the seahorse"
        my_sound_wilhelm.play_sound()
        my_sound_wilhelm.join()
        my_drink = "Mai Tai"
    elif my_drink_ID == "3c62dba1":
        print "Found the Lady Virgin"
        my_sound_lady.play_sound()
        my_sound_lady.join()
        my_drink = "Tail-less Scorpion"
    elif my_drink_ID == "bc5bdca1":
        print "Found the tall black idol"
        my_sound_NW_Birdbath2.play_sound()
        my_sound_NW_Birdbath2.join()
        my_drink = "Scorpion"
    elif my_drink_ID == "0cd9dea1":
        print "Found the black Hawaiin idol"
        my_sound_Howie.play_sound()
        my_sound_Howie.join()
        my_drink = "Trader Vic Grog"
    elif my_drink_ID == "ecf5dea1":
        print "Found Tall freaky lady"
        my_sound_NW_Kathy1.play_sound()
        my_sound_NW_Kathy1.join()
        my_drink = "Pieces of Eight"
    elif my_drink_ID == "8ca3dba1":
        print "Found the tan bottle opener"
        my_sound_NW_Kathy1.play_sound()
        my_sound_NW_Kathy1.join()
        my_drink = "Hurricane"
    elif my_drink_ID == "bc7adba1":
        print "Found the black bottle opener"
        my_sound_NW_Sam2.play_sound()
        my_sound_NW_Sam2.join()
        my_drink = "Outrigger"
    elif my_drink_ID == "858379ff":
        print "Found the Chief!!!"
        my_sound_NW_Birdbath3.play_sound()
        my_sound_NW_Birdbath3.join()
        my_drink = "Chief Lapu Lapu"
    # elif my_drink_ID == "1cbfdba1":
    #    print "Found the BIG BUTT brown Hawaiin idol"
    #    my_sound_wilhelm.play_sound()
    #    my_sound_wilhelm.join()
    #    my_drink = "Hawaiian Eye"
    elif my_drink_ID == "8c97dba1":
        print "Found Charlotte's Hula Lady"
        my_sound_NW_Victor1.play_sound()
        my_sound_NW_Victor1.join()
        my_drink = "Moonlight"
    elif my_drink_ID == "1cbfdba1":
        print "Found the BIG BUTT brown Hawaiin idol"
        my_sound_NW_Victor2.play_sound()
        my_sound_NW_Victor2.join()
        my_drink = "Citrus Sunset"
    elif my_drink_ID == "95a287ff":
        print "Found the Owl!!!"
        my_sound_NW_Victor3.play_sound()
        my_sound_NW_Victor3.join()
        my_drink = "Passionfruit Wellness"
    elif my_drink_ID == "ace3dea1":
        print "Found the Funky Dunky Dude!!!"
        my_sound_NW_I_heard_your_prayers.play_sound()
        my_sound_NW_I_heard_your_prayers.join()
        my_drink = "Cool Coconut"
    elif my_drink_ID == "f5f974ff":
        print "Found the Swan!!!"
        my_sound_NW_Victor4.play_sound()
        my_sound_NW_Victor4.join()
        my_drink = "Pina Co-nada"
    elif my_drink_ID == "05367bff":
        print "Found the White Duck!!!"
        my_sound_NW_Sam4.play_sound()
        my_sound_NW_Sam4.join()
        my_drink = "Pina Colada"
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
    elif my_drink not in my_recipes.drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
        my_recipes.ready_to_dispense(cancel=True)

    # Assert: a valid drink name has been generated
    elif my_drink in ["S", "s", "Setup", "setup"]:
        pass
    else:
        my_sound_drums.play_sound()
        my_recipes.make_drink(my_drink)
        my_sound_drums.stop_sound(fade_time=1000)
        # **********************************
        # Checking Bottle Inventory
        # This is useful for big parites, when bottles run low quickly
        # Uncomment this line if you want to check inventory for each drink
        # **********************************
	# my_recipes.check_inventory() # Make sure bottles aren't empty

## zzzz TEST!! zzzz ##
#    my_recipes.test_lights()
