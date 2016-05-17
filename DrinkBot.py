#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

import time
import csv
import atexit


####### These are needed for the Bot interrupts -- to start and stop the motors on a timer
from twisted.internet import task
from twisted.internet import reactor


############################
#  PUMP CALIBRATION TABLE  #
############################
# This is a standardized calibration table.
# To pump 1 ounce, you run each pump approximately this amount.
# The way the rest of the calibration code works, is you run the pump this amount
# Then enter how many ounces you *actually* got from that run.
# The real time to run the pump is then Normalized against this number.
#
# formula: time = ounces * factor
# factor = initial_calibration_factor
# 2 ounces = normalized time
# normalized time = initial time 
# normalized ounces = ounces expected / ounces delivered
#
# We calibrate against 2 ounces -- the larger amount we calibrate against, the more accurate.
# 2 ounces delivers decent accuracy, while not waiting too long for it to finish.
# So we run the pump for 60 seconds and measure the actual ounces delivered -- which should be close to 2 ounces.
# We simply enter the actual ounces delivered into the calibration "drink".
#
# Here's the calibration formula:
# 2oz = about 60 seconds -- but it isn't
# 60 seconds = X ounces
# 2oz/Xoz * 60 = accurate 2oz -- my original formula
# 2oz/Xoz * 60 / 2oz = accurate 1oz -- scaled to 1oz
# 1oz/Xoz * 60 = accurate 1oz -- complete normalized formula
calibration_seconds = 60

# This is how long it should take to fill the pump tubing to dispense
prime_seconds = 2
# This is the speed of the pump
peristaltic_2oz = 2
# If the calibration value for a pump is 0, then this pump is not calibr$
not_calibrated = 0


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
            drinks[each_drink[recipe_name]][each_ingredient] = 0


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

############################################
# Initialize the motors on the Bot         #
############################################
# Set up the address for each of the pumps #
# NOTE: Since we don't have all 3 hats,    #
#   I've commented out for the other       #
#   two boards, until they come in         #
############################################

# bottom hat is default address 0x60 
# Board 0: Address = 0x60 Offset = binary 0000 (no jumpers required)
bottom_hat = Adafruit_MotorHAT(addr=0x60)

# middle hat has A0 jumper closed, so its address 0x61.
# Board 1: Address = 0x61 Offset = binary 0001 (bridge A0)
middle_hat = Adafruit_MotorHAT(addr=0x61)
# top hat has A0 jumper closed, so its address 0x62. 
# Board 2: Address = 0x62 Offset = binary 0010 (bridge A1, the one above A0)
###   top_hat = Adafruit_MotorHAT(addr=0x62)

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    bottom_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    bottom_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)


# middle_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
# middle_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
# top_hat.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

#####################
# Bottom Hat motors #
#####################
# Note: The pumps are indexed by the ingredient name
#   range(1,5) means make a set of 5 numbers, 0-indexed, start at 1
#   Keep in mind, 0-index to 5, is [0,1,2,3,4]
#   So starting at 1 means [1,2,3,4]
#   Index #0 is the name "Recipe" so it is skipped
ingr_pumps = {}
temp_ingr_list = iter(ingr_list)
for each_motor in range(1, 5):
    ingr_pumps[temp_ingr_list.next()] = bottom_hat.getMotor(each_motor)

for each_pump in ingr_pumps:
    print each_pump


#####################
# PUMP CALIBRATION  #
#####################

# This is the calibration for how long to run the pump for 1 ounce
# Note: The drink calibration factor is the number of ounces delivered in 60 seconds -- around 2oz
# Thus, drinks["Calibration"][each_ingredient] should be near to 2oz, the amount that pump delivered in 60 seconds
# In short, the calibration_factor for each pump is multiplied by the number of ounces delivered for that drink
def calibrate_pump(pump):
    pump.setSpeed(255)
    pump.run(Adafruit_MotorHAT.FORWARD)
    time.sleep(calibration_seconds)
    pump.run(Adafruit_MotorHAT.RELEASE)
    print "60 seconds of run have been delivered."
    print "Please enter into your calibration line the exact amount just dispensed."


calibration_factor = {}
for each_ingredient in ingr_list:
    if float(drinks["Calibration"][each_ingredient]) == not_calibrated:
        yesno = raw_input("Do you want to calibrate pump for " + each_ingredient + "?")
        if yesno == "yes":
            calibrate_pump(ingr_pumps[each_ingredient])
            new_factor = raw_input("How much liquid was delivered?")
            calibration_factor[each_ingredient] = 1 / float(new_factor) * calibration_seconds
        else:
            print "Well...ok, but that means I'll enter a standard 2oz for this pump and it will be inaccurate!"
            calibration_factor[each_ingredient] = 1 / 2 * calibration_seconds
    else:
        calibration_factor[each_ingredient] = 1 / float(drinks["Calibration"][each_ingredient]) * calibration_seconds

# Check if there's a calibration "drink" -- this "drink" is a multiplier for each pump to equal 1oz
# If there's no calibration "drink" then give a warning, and use a default calibration
#   not ideal! Each pump is different!

if drinks.get("Calibration") is None:
    print "NO CALIBRATION!!!!"
    for each_ingredient in ingr_list:
        # We assume the pump delivered 2oz in 60 seconds
        drinks["Calibration"][each_ingredient] = peristaltic_2oz
else:
    # Since there's a line for calibration, don't actually treat it like a drink. :)
    drink_names.remove("Calibration")

# DEFINE mixMe code


def mixMeOld(ingredient, ounces):
    ingredient.setSpeed(255)
    ingredient.run(Adafruit_MotorHAT.FORWARD)
    time.sleep(ounces)
    ingredient.run(Adafruit_MotorHAT.RELEASE)

def mixMe(ingredient, ounces):
    ingredient.setSpeed(255)
    ingredient.run(Adafruit_MotorHAT.FORWARD)

    clock = task.Clock()
    l = task.LoopingCall(clock, 1.5, ingredient.run,Adafruit_MotorHAT.RELEASE)
    l.start(1.5)
    reactor.run()

####### Sample code to test interrupts
    # def runEverySecond( some_text ):
    #print some_text

    #l = task.LoopingCall(runEverySecond, "Kiki a second has passed")
    #l.start(1.0) # call every second

    # l.stop() will stop the looping calls
    #reactor.run()
####### END Temp code to test interrupts



# Define primeMe code
def primeMe(ingredient):
    ingredient.setSpeed(255)
    ingredient.run(Adafruit_MotorHAT.FORWARD)
    time.sleep(prime_seconds)
    ingredient.run(Adafruit_MotorHAT.RELEASE)

    answer = raw_input("More?")
    while answer == "y":
        ingredient.setSpeed(255)
        ingredient.run(Adafruit_MotorHAT.FORWARD)
        time.sleep(prime_seconds / 10)
        ingredient.run(Adafruit_MotorHAT.RELEASE)
        answer = raw_input("More? [y/n]")


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
        primeMe(ingr_pumps[my_drink])
    elif my_drink in ["Exit","exit","X","x"]:
        print "I'm done!"
        break
    elif my_drink not in drink_names:
        print "THAT'S NOT A DRINK, YOU SILLY!"
    else:
        for each_ingredient in drinks[my_drink]:
            if drinks[my_drink][each_ingredient] > 0:
                print each_ingredient + ": " + drinks[my_drink][each_ingredient]
                print "Normalized: ", float(drinks[my_drink][each_ingredient]) * calibration_factor[each_ingredient], " seconds."
                mixMe(ingr_pumps[each_ingredient], float(drinks[my_drink][each_ingredient]) * calibration_factor[each_ingredient])

# Close the file at the end.
# Note, this annoys me and is not tidy to leave the file open the whole time!
myFile.close()
