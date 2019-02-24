#!/usr/bin/python
#
# Copyright 2015 - Jonathan Gordon
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
# KIND, either express or implied.

from sys import stdin
from common import *
import cards
import random


class Personality:
    def __init__(self):
        pass
    
    def make_choice(self, options):
        pass


class StupidAI(Personality):
    def __init__(self):
        self.choice = []
        self.options = []
    
    def make_choice(self, options):
        self.choice.append([ch, [(o[0], o[1].id) for o in options]])
        return 0


class RandomAI(Personality):
    def __init__(self):
        self.choice = []
        self.options = []
    
    def make_choice(self, options):
        ch = random.randint(0, len(options) - 1)
        self.choice.append([ch, [(o[0], o[1].id) for o in options]])
        return ch


class GoodAI(Personality):
    def __init__(self):
        self.choice = []
    
    def make_choice(self, options):
        ch = 0
        for i in options:
            if i[1].is_science_card():
                if i[0] == 0:
                    ch = options.index(i)
            else:
                for o in options:
                    if o[1].is_resource_card() and o[0] == 0:
                        ch = options.index(o)
                    else:
                        ch = 0
        # self.choice.append([ch, [(o[0], o[1].id) for o in options]])
        self.choice.append([ch, [o[0] * 1000 + o[1].id for o in options]])
        return ch
        # return random.randint(0, len(options) - 1)


class Human(Personality):
    def __init__(self):
        self.choice = []
    
    def make_choice(self, options):
        ch = int(stdin.readline())
        self.choice.append([ch, [(o[0], o[1].id) for o in options]])
        return ch

