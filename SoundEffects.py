#!/usr/bin/python

# Invented by Kiki Jewell with a little help from Spaceman Sam, May 6, 2016

#############################################
# SoundEffects:                             #
#############################################
# This class plays sound effects through the headphone jack
#############################################
import pygame.mixer

class SoundEffects():
    def __init__(self, sound_name="sounds/Scream.wav", channel=1, music=False, skip=0):

        pygame.mixer.init(48000, -16, 2, 4096)

        self.music = music # Whether this is a longer sound or sound effect
        self.name = sound_name
        self.sound = pygame.mixer.Sound(sound_name)
        self.soundChannel = pygame.mixer.Channel(channel)
        self.myBuffer = None
        if self.music:
            try:
                f = open(sound_name, 'rb')
                data = f.read()
                # buffer = data[44:len(data)] # start after header
                self.myBuffer = buffer(data, 44+skip, len(data))

                print "made a mixer.music - len: ", len(data)
            except:
                print "Mixer.music didn't work"
        return

    def play_sound(self):
        print "Playing: {}".format(self.name)
        if self.music:
            pygame.mixer.Sound(self.myBuffer).play()
        else:
            self.soundChannel.play(self.sound)

    def join(self):
        while pygame.mixer.get_busy():
            pass

    # fade_time is in miliseconds -- 5000=5sec
    def stop_sound(self, fade_time=0):
        print "Stopping: {}".format(self.name)
        pygame.mixer.fadeout(fade_time)
        while pygame.mixer.get_busy():
            pass
