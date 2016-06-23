#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import csv
import logging
import sys
sys.path.insert(0, 'pynfc/src')
from mifareauth import NFCReader

# Kiki's awesome Motors Class that does threading and other cool stuff!  (She's overly proud of herself. :) )
from Motors import Motors

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
class Drink_Recipes():
    def __init__(self):
        # Initialize all member variables:
        self.drinks = {}  # This is a list of all drinks -- key:value pairs of all the ingredient amounts
        self.drink_names = []  # This is simply a list of all the drink names -- the "menu" as it were
        self.ingr_list = []  # List of all ingredients and their link to their respective pumps -- by csv column
        self.recipe_name = "Recipe" # Eventually the upper left cell -- the column name, and key for all drink names
        self.ingr_pumps = {} # List of the pumps themselves
        self.valid_ingr_list = [] # List of all the real ingredients that may be used

    def get_recipes_from_file(self, recipe_file_name):
        # Open the spreadsheet.
        myFile = open(recipe_file_name, 'r')
        # Read the file into a Dictionary type -- this is useful for spreadsheet configurations of CSV data
        recipe_book = csv.DictReader(myFile)

        # Grab a copy of all the ingredient names (which are the top row of the file, also known as the fieldnames in Dict land
        for each_ingredient in recipe_book.fieldnames:
            self.ingr_list.append(each_ingredient)
        # This is the upper left entry, the column title for all drink names, and the key for each drink name
        self.recipe_name = self.ingr_list[0]
        # The first row is all the ingredients, not a drink recipe.
        self.ingr_list.remove(self.recipe_name)

        #####################################
        # Create the list of drink recipes  #
        #####################################
        # This is a list of drinks and each drink has a list of Key:Value pairs that are the ingredient:amount
        for each_drink in recipe_book:
            self.drinks[each_drink[self.recipe_name]] = {}  # Start with an empty recipe, so we can append each ingredient Key:Value pair
            self.drink_names.append(each_drink[self.recipe_name])  # Keep a list of all the drink names

            # Now go through all the ingredients for this drink, and append the amounts into the drink
            for each_ingredient in self.ingr_list:
                # Append the ingredient amount to the recipe list
                if each_drink[each_ingredient] is not '':
                    # Example: drinks["Mai Tai]["Orgeat"] = ".25oz"
                    # "Mai Tai" = each_drink[recipe_name] -- goes through every drink
                    # "Orgeat" = each_ingredient -- goes through all ingredients
                    # ".25oz" = each_drink[each_ingredient] -- goes through every amount for that drink
                    self.drinks[each_drink[self.recipe_name]][each_ingredient] = float(each_drink[each_ingredient])
                else:
                    # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
                    self.drinks[each_drink[self.recipe_name]][each_ingredient] = 0.0

        # Done getting the info from the file.
        myFile.close()

        # Remove these fake recipes from the list
        # Note: this leaves the data intact in the drinks[] list
        self.drink_names.remove("Calibration")
        self.drink_names.remove("Prime")
        return self

    #############################################
    #     Create pumps linked to ingredients    #
    #############################################
    def link_to_motors(self):
        temp_ingr_list = iter(self.ingr_list)
        # We have three hats right now, so 12 pumps -- range is zero indexed, 0-12, starting at 1
        for each_motor in range(1, 13):
            each_ingredient = temp_ingr_list.next() # Go through all the ingredients by name
            # This is a calibration factor -- more info in Motors.dispense()
            calibration_oz = float(self.drinks["Calibration"][each_ingredient])
            self.ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_oz ) # Create the pump
            self.valid_ingr_list.append(each_ingredient) # Add the pump to the list of valid ingredients

    #############################################################
    # This prints all the ingredients, not including 'Recipe'   #
    #############################################################
    # Note: since the Calibration and Prime lines are not actually removed, these will also print
    def print_full_recipes(self):
        for each_drink in self.drink_names:
            print "*** ", each_drink, " ***"
            for each_ingredient in self.drinks[each_drink]:
                # Skip the ingredients that are not used in this recipe
                # Comment this out of you want empty entries to be printed
                if self.drinks[each_drink][each_ingredient] is not '':
                    print each_ingredient + ': ', self.drinks[each_drink][each_ingredient]

    #############################################################
    # Print the menu                                            #
    #############################################################
    def print_menu(self):
        print "********************   Menu of drinks   ********************"
        for each_drink in self.drink_names:
            print each_drink

