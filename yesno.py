#!/usr/bin/python

# Very cute little class that gets a yes or no from the user

class yesno():
    valid_all = ["Y", "y", "YES", "yes", "Yes", "N", "n", "NO", "no", "No", ""]
    valid_yes_default = ["Y", "y", "YES", "yes", "Yes", ""]
    valid_no_default = ["N", "n", "NO", "no", "No", ""]

    def __init__(self):
        return

    def is_yes(self, message = ""):
        yesno = raw_input(message + " [Y/n] ")
        print self.valid_all
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_yes_default

    def is_no(self, message = ""):
        yesno = raw_input(message + " [y/N] ")
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_no_default
