#!/bin/bash
rsync -v --update --existing ./DrinkBot.py pi@169.254.174.79:TikiBot/DrinkBot.py
rsync -v --update --existing ./SetupBot.py pi@169.254.174.79:TikiBot/SetupBot.py
rsync -v --update --existing ./Recipes.py pi@169.254.174.79:TikiBot/Recipes.py
rsync -v --update --existing ./Motors.py pi@169.254.174.79:TikiBot/Motors.py
rsync -v --update --existing ./Pumps.py pi@169.254.174.79:TikiBot/Pumps.py
rsync -v --update --existing ./yesno.py pi@169.254.174.79:TikiBot/yesno.py
rsync -v --update --existing ./SoundEffects.py pi@169.254.174.79:TikiBot/SoundEffects.py
rsync -v --update --existing ./pynfc/src/mifareauth.py pi@169.254.174.79:TikiBot/pynfc/src/mifareauth.py
# rsync -v --update --existing ./DispenseLog.txt pi@169.254.174.79:TikiBot/DispenseLog.txt
# rsync -v --update --existing ./CommandLog.txt pi@169.254.174.79:TikiBot/CommandLog.txt
rsync -v --update --existing ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_PWM_Servo_Driver.py pi@169.254.174.79:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_PWM_Servo_Driver.py
rsync -v --update --existing ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_MotorHAT.py pi@169.254.174.79:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_MotorHAT.py
rsync -v --update --existing ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_I2C.py pi@169.254.174.79:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_I2C.py
rsync -v --update --existing ./MassiveDrinks.csv pi@169.254.174.79:TikiBot/MassiveDrinks.csv
