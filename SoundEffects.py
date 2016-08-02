#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# SoundEffects:                             #
#############################################
# This class plays sound effects through the headphone jack
#############################################

import os
import pygame.mixer

class SoundEffects():
    def __init__(self, sound_name="sounds/Scream.wav", channel = 1):
        pygame.mixer.init(48000, -16, 1, 1024)
        self.name = sound_name
        self.sound = pygame.mixer.Sound(sound_name)
        self.soundChannel = pygame.mixer.Channel(channel)
        return

    # Get a yes/no answer from the user, defaulting to Yes
    def play_sound(self):
        #os.system('mpg123 -q power-converters.mp3 &')
        print "Playing: {}".format(self.name)
        self.soundChannel.play(self.sound)
