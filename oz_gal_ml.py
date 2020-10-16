#!/usr/bin/python

##################################################
#  Very cute little class that gets a            #
#    valid liquid measure and converts to ounces #
##################################################

import re

class oz_gal_ml():
    valid_sizes = {"oz":1, "OZ":1, "ounce":1, "ounces":1,
                   "gal":64, "GAL":64, "gals":64, "GALS":64, "gallons":64, "GALLONS":64,
                   "ml":0.033814, "ML":0.033814, "milliliter":0.033814, "milliliters":0.033814,
                   "mililiter": 0.033814, "mililiters": 0.033814, # handle misspellings
                   "c":8, "cup":8, "cups":8, "C":8, "CUP":8, "CUPS":8,
                   "pt":16, "pint":16}

    def __init__(self):
        return

    # Get a number from the user, forcing them if they enter not a number
    #   This can get integers only or floats (see default values in the parameters)
    def get_oz(self, message = "How much liquid: ", enter_means_zero = True, default_val = 0.0):
        while True:
            new_val = default_val
            answer = raw_input(message) # Ask the user for the liquid measure
            if (enter_means_zero and answer == ''):
                new_value = 0.0
                break # Let user press [ENTER] for nothing
            try:
                # Split the answer into the number and the size (the first (nul) is garbage)
                nul, num, sz = re.split(r'(\d+)', answer) # \d is decimal values
                sz = sz.split() # Strip any lead/trailing whitespace
            except ValueError:
                pass
            if (sz in valid_sizes):
                new_val = float(num) * valid_sizes[sz]
                break
            print("ERROR: try '16oz', or '1gal', or '750ml'")
        return new_val

    # Get a number from the user, forcing them if they enter not a number
    #   This can get integers only or floats (see default values in the parameters)
    def get_portion(self, message="How much of the whole: ", percent = True, enter_means_full = True, default_val=0.0):
        while True:
            new_val = default_val
            answer = raw_input(message)  # Ask the user for the liquid measure
            if (enter_means_full and answer == ''):
                new_value = 1.0
                break # Let user press [ENTER] for nothing
            fraction_parts = answer.split('/') # If it's a fraction
            if(len(fraction_parts) == 2):
                try:
                    new_val = fraction_parts[0] / fraction_parts[1]
                    if (not percent):
                        break # Acceptable value
                    elif (new_val < 1.0 and new_val > 0):
                        break # Acceptable value
                except ValueError:
                    print("ERROR: must be a fraction or decimal!")
            else:
                try:
                    new_val = float(answer)
                    if (not percent):
                        break  # Acceptable value
                    elif (new_val < 1.0 and new_val > 0):
                        break  # Acceptable value
                except ValueError:
                    print("ERROR: must be a fraction or decimal!")

        return new_val
