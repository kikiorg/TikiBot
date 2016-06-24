#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv

import logging
import sys
sys.path.insert(0, 'pynfc/src')

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
#   DONE -- Check for the existence of the Calibration line -- if it doesn't exist, then use defaults
#   DONE -- Check for the existence of the Prime line -- if it doesn't exist, then use defaults
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
        my_recipes.tiny_prime()
    elif my_command in ["C", "c", "Calibrate", "calibrate"]:
        my_recipes.calibrate()
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
                my_recipes.purge_all("reverse")
                print "    Put hoses into rinse water."
            elif step == 1:
                my_recipes.purge_all()
                my_recipes.purge_all()
                print "    Remove the hoses to allow air to enter."
            elif step == 2:
                my_recipes.purge_all()
                print "    Put hoses into bleach water."
            elif step == 3:
                my_recipes.purge_all()
                my_recipes.purge_all()
                print "    Remove the hoses to allow air to enter."
            elif step == 4:
                my_recipes.purge_all()
                print "    Put hoses into rinse water."
            elif step == 5:
                my_recipes.purge_all()
                my_recipes.purge_all()
                print "    Remove the hoses to allow air to enter"
            elif step == 6:
                my_recipes.purge_all()
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

