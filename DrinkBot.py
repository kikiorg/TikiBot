#!/usr/bin/python

# OLD CODE!!!! REMOVE WHEN THINGS WORK!! :)
#from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import time
import csv
import atexit
# Kiki's awesome Motors Class that does threading and other cool stuff!
from Motors import Motors

####### These are needed for the Bot interrupts -- to start and stop the motors on a timer
from twisted.internet import task
from twisted.internet import reactor


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
# The first row in all the ingredients, but the first entry is the first column title "Recipes"
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
    # Now go through all the ingredient for this drink, and append the amounts into the drink
    for each_ingredient in ingr_list:
        # print "ingr: " , each_ingredient
        # Skip the ingredients that are not used in this recipe
        # Comment this out of you want empty entries to be added
        if each_drink[each_ingredient] is not '':
            # Explanation:
            # tl;dr eg: drinks["Mai Tai]["Orgeat"] = ".25oz"
            # recipe_name is "Recipe" -- the title of the first column, which is the list of drink names
            # each_drink[recipe_name] is the drink name, eg: "Mai Tai"
            # drinks["Mai Tai"] is the list of the amounts for all ingredients of "Mai Tai"
            # [each_ingredient] is the looping of every single ingredient
            # each_drink is the whole row from the file, and each_drink[each_ingredient] one single ingreidnt amount
            drinks[each_drink[recipe_name]][each_ingredient] = each_drink[each_ingredient]
        else:
            # The .csv file has nothing for this cell, so stick in a 0 for none dispensed
            drinks[each_drink[recipe_name]][each_ingredient] = 0

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
for each_motor in range(1, 5):
    each_ingredient = temp_ingr_list.next()
    calibration_factor = drinks["Calibration"][each_ingredient]
    ingr_pumps[each_ingredient] = Motors( each_ingredient, calibration_factor )

for each_pump in ingr_list:
    print "Each pump: " + ingr_pumps[each_pump].name()



#######################
# PRINT INGREDIENTS   #
#######################
# This prints all the ingredients, including 'Recipe'

while True:
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
        for each_ingredient in drinks[my_drink]:
            if drinks[my_drink][each_ingredient] > 0:
                print each_ingredient + ": " + drinks[my_drink][each_ingredient]
                print "Normalized: ", float(drinks[my_drink][each_ingredient]) * calibration_factor[
                    each_ingredient], " seconds."

                ingr_pumps[each_ingredient].dispense(float(drinks[my_drink][each_ingredient]) * calibration_factor[each_ingredient])

# Close the file at the end.
# Note, this annoys me and is not tidy to leave the file open the whole time!
myFile.close()
