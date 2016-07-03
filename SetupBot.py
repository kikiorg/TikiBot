#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# SetupBot:                                 #
#############################################
# This class executes the setup procedures:
#   It's really just a big while loop that prompts the user for each setup command
#
#   [C]alibrate -- calibrate all the pumps
#   [G]lobal calibration check -- dispense 1oz for every pump; should be 12oz total
#   [P]rime -- prime all pumps
#   [T]iny Prime -- do small, incremental priming of each pump to calibrate the priming sequence
#   [S]hutdown full phase -- this includes all steps needed for the shutdown procedure
#       The user can step through them in order, or skip around by choosing the step number
#############################################

import logging
import sys
sys.path.insert(0, 'pynfc/src')

from Recipes import Drink_Recipes
from yesno import yesno

#############################################
# READ DRINK LIST FROM SPREADSHEET          #
#############################################
my_recipes = Drink_Recipes("SetupBot.py")
my_recipes.get_recipes_from_file('TikiDrinks.csv')
my_recipes.link_to_motors()
my_yesno = yesno()

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

    if my_command in ["P", "p", "prime", "Prime"]:
        my_recipes.prime_all()
    elif my_command in ["G", "g", "global", "Global"]:
        my_recipes.checksum_calibration()
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
            print "***", step, ")", steps_list[step]

            if step == 0:
                my_recipes.prime_all(forwards = False)
                print "    Put hoses into rinse water."
            elif step == 1:
                my_recipes.prime_all()
                my_recipes.prime_all()
                print "    Remove the hoses to allow air to enter."
            elif step == 2:
                my_recipes.prime_all()
                print "    Put hoses into bleach water."
            elif step == 3:
                my_recipes.prime_all()
                my_recipes.prime_all()
                print "    Remove the hoses to allow air to enter."
            elif step == 4:
                my_recipes.prime_all()
                print "    Put hoses into rinse water."
            elif step == 5:
                my_recipes.prime_all()
                my_recipes.prime_all()
                print "    Remove the hoses to allow air to enter"
            elif step == 6:
                my_recipes.prime_all()
                print "    YOU ARE NOW READY TO SHUT DOWN"
            step = my_yesno.get_number("    Press Enter for next step, or step #, or CTRL-C to end) ", int_only = True, default_val = (step + 1))

            if step >= len(steps_list) - 1:
                not_done = False

    elif my_command in ["X", "x", "E", "e", "Q", "q", "Exit", "exit", "Quit", "quit"]:
        print "I'm done!"
        break
    else:
        print "This is not a command I understand."

