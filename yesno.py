#!/usr/bin/python

##############################################################
#  Very cute little class that gets a yes or no from the user #
##############################################################

class yesno():
    valid_all = ["Y", "y", "YES", "yes", "Yes", "N", "n", "NO", "no", "No", ""]
    valid_yes_default = ["Y", "y", "YES", "yes", "Yes", ""]
    valid_no_default = ["N", "n", "NO", "no", "No", ""]

    def __init__(self):
        return

    # Get a yes/no answer from the user, defaulting to Yes
    def is_yes(self, message = ""):
        yesno = raw_input(message + " [Y/n] ")
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_yes_default

    # Get a yes/no answer from the user, defaulting to Yes
    def is_no(self, message = ""):
        yesno = raw_input(message + " [y/N] ")
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_no_default

    # Get a number from the user, forcing them if they enter not a number
    #   This can get integers only or floats (see default values in the parameters)
    def get_number(self, message = "Please enter a number: ", default_val = 0.0, int_only = False, neg_ok = False):
        my_zero = 0
        if not int_only:
            my_zero = 0.0
        while True:
            try:
                answer = raw_input(message)
                fraction = answer.split('/')
                if int_only:
                    my_number = int(answer)
                elif len(fraction) == 2:
                    numerator = float(fraction[0])
                    denominator = float(fraction[1])
                    my_number = numerator/denominator
                else:
                    my_number = float(answer)
                if not neg_ok and my_number < my_zero:
                    raise ValueError
                break
            except ValueError:
                if answer == "":
                    my_number = default_val
                    break
        return my_number
