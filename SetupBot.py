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

from yesno import yesno

class Setup:
    def __init__(self, my_recipes):
        #############################################
        # READ DRINK LIST FROM SPREADSHEET          #
        #############################################
        self.my_recipes = my_recipes
        self.my_yesno = yesno()
        self.my_drink_ID = None
        self.my_command = ""
        self.logger = logging.getLogger("cardhandler").info

    def shutdown(self):
        not_done = True
        step = 0
        steps_list = ["REVERSE LIQUIDS",
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
            step = self.my_yesno.get_number("    Press Enter for this step, or step # to skip, or CTRL-C to end) ",
                                            int_only=True,
                                            default_val=(step))

            if step == 0: # Reverse the liquids back into the bottles
                self.my_recipes.prime(forwards=False)
                print "    Put hoses into rinse water."
            elif step == 1 or step == 3 or step == 5:
                self.my_recipes.prime()
                self.my_recipes.prime()
                print "    Remove the hoses to purge with air."
            elif step == 2:
                self.my_recipes.prime()
                print "    Put hoses into bleach water."
            elif step == 4:
                self.my_recipes.prime()
                print "    Put hoses into rinse water."
            elif step == 6:
                self.my_recipes.prime()
                self.my_recipes.prime()
                print "    YOU ARE NOW READY TO SHUT DOWN"

            step += 1

            # if step > len(steps_list) - 1:  # len = 8, -1 = 7
            #     not_done = False
            not_done = (step < len(steps_list))

    def setup_menu(self):

        while self.my_command not in ["end" "End", "e", "E", "exit", "Exit", "x", "X", "quit", "Quit", "q", "Q"]:

            print "List of commands: "
            print "[P]rime -- prime all pumps"
            print "[T]iny Prime -- do small, incremental priming of each pump (tedius)"
            print "[K]id drinks -- create new drinks by shot size."
            print "[B]ottle reprime -- prime a new bottle if it ran out"
            print "Si[Z]e of cup -- change the size of the cup"
            print "[G]lobal calibration check: "
            print "    This dispenses all pumps for 1oz -- more like a fast checksum"
            print "[C]alibrate: "
            print "[S]hutdown full phase -- this includes these steps:"
            print "    Reverse liquids -- then wait"
            print "    Prime 2x with water -- then wait, purge with air, wait"
            print "    Prime with bleach -- then wait, purge with air, wait"
            print "    Prime 2x with water -- then wait, purge with air, DONE"
            print "E[X]it or [Q]uit"
            print
            my_command = raw_input("Please enter your command: ")

            if my_command in ["P", "p", "prime", "Prime"]:
                self.my_recipes.prime()
            elif my_command in ["B","b","Bottle","bottle"]:
                # Print all the pumps as numbers and names
                pump_num = 0
                for each_ingr in self.my_recipes.valid_ingr_list:
                    pump_num += 1
                    print "{} - {}".format(pump_num, each_ingr)
                my_pump = raw_input("Please enter the name or pump number to prime:")
                self.my_recipes.prime(one_pump=my_pump)

            elif my_command in ["G", "g", "global", "Global"]:
                self.my_recipes.checksum_calibration()
            elif my_command in ["T", "t", "tiny prime", "Tiny Prime"]:
                self.my_recipes.calibrate_prime()
            elif my_command in ["K", "k", "kid drink", "Kid Drink"]:
                self.my_recipes.kid_drink()
            elif my_command in ["C", "c", "Calibrate", "calibrate"]:
                self.my_recipes.calibrate()
            elif my_command in ["Z", "z", "Size", "size"]:
                self.my_recipes.get_cup_size()

            elif my_command in ["S", "s", "Shutdown", "shutdown"]:
                self.shutdown()
            elif my_command in ["X", "x", "E", "e", "Q", "q", "Exit", "exit", "Quit", "quit"]:
                print "Return to idol worship!"
                break
            else:
                print "This is not a command I understand."

