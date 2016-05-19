#!/usr/bin/python

# Testing an interesting idea of incrementing through all the motors as each is created.
# I hope that's a good idea! :)

class Motors():
    test_increment = 0
    test_list = {"a","b","c","d"}

    def __init__(self, item):
        self.item = item
        Motors.test_increment +=1

mine0 = Motors(Motors.test_increment)
mine1 = Motors(Motors.test_increment)
mine2 = Motors(Motors.test_increment)
mine3 = Motors(Motors.test_increment)

print mine0.item
print mine1.item
print mine2.item
print mine3.item
