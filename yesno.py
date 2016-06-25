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
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_yes_default

    def is_no(self, message = ""):
        yesno = raw_input(message + " [y/N] ")
        while yesno not in self.valid_all:
            yesno = raw_input(message)
        return yesno in self.valid_no_default

    def get_float(self, message = "Please enter a number: ", default_val = 0.0, neg_ok = False):
        while True:
            try:
                answer = raw_input(message)
                my_number = float(answer)
                if not neg_ok and my_number < 0.0:
                    raise ValueError
                break
            except ValueError:
                if answer == "":
                    my_number = default_val
                    break
        return my_number