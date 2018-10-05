#!/bin/bash
rsync -v --update --existing pi@192.168.2.3:TikiBot/DrinkBot.py ./DrinkBot.py
rsync -v --update --existing pi@192.168.2.3:TikiBot/SetupBot.py ./SetupBot.py
rsync -v --update --existing pi@192.168.2.3:TikiBot/Recipes.py ./Recipes.py
rsync -v --update --existing pi@192.168.2.3:TikiBot/Motors.py ./Motors.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/Pumps.py ./Pumps.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/yesno.py ./yesno.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/SoundEffects.py ./SoundEffects.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/pynfc/src/mifareauth.py ./pynfc/src/mifareauth.py 
# rsync -v --update --existing pi@192.168.2.3:TikiBot/DispenseLog.txt ./DispenseLog.txt 
# rsync -v --update --existing pi@192.168.2.3:TikiBot/CommandLog.txt ./CommandLog.txt 
rsync -v --update --existing  pi@192.168.2.3:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_PWM_Servo_Driver.py ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_PWM_Servo_Driver.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_MotorHAT.py ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_MotorHAT.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_I2C.py ./Adafruit-Motor-HAT-Python-Library/Adafruit_MotorHAT/Adafruit_I2C.py 
rsync -v --update --existing pi@192.168.2.3:TikiBot/MassiveDrinks.csv ./MassiveDrinks.csv 
