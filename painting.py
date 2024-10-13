#!/usr/bin/python3
# This module provides basic functionality for painting & graphics in the terminal.

import sys, os
from enum import Enum

class IOMonopoly:
    # Only works for single threading
    # This may be not exactly safe

    def __init__(self):
        self.lockable = True

    def lock_stdin(self):
        pass

    def unlock_stdin(self):
        pass

    def lock_stdout(self):
        pass

    def unlock_stdout(self):
        pass

    def lock_io(self):
        lock_stdin()
        lock_stdout()

    def unlock_io(self):
        unlock_stdin()
        unlock_stdout()

    def finish(self):
        unlock_io()
        self.lockable = False

class ColorMode(Enum):
    RGB = 1
    HSL = 2
    SGR = 3

class Color:

    def __init__(self, fg=[0,0,0], fg_mode=ColorMode.SGR, bg=[0,0,0], bg_mode=ColorMode.SGR, effects=None): # a selection can be disabled by setting to sgr and selecting 39 / 49
        self.fg = fg
        self.bg = bg
        self.fg_mode = fg_mode
        self.bg_mode = bg_mode
        self.effects = None





class Canvas:# Maybe make it a child of IOMonopoly => no other command can interfere with the canvas
############# important class

    def __init__(self, width: int, height: int):
        self.height = height
        self.width = width
        self.cursor_offset = self._get_absolute_position()
        # reserve space in terminal
        for h in range(self.height-1):
            print()
        for w in range(self.width-1):
            print(' ', end='')
        self.cursor = [width, height]# position after reservin space



    def setCursor(x:int, y:int):
        #absolute_pos = _get_absolute_position()
        #pos = absolute_pos-self-cursor_offset #hope vector addition works
        #delta = (x, y) - pos
        abs_x = self.cursor_offset(0)+x
        abs_y = self.cursor_offset(1)+y
        sys.stdout.write("\x1b["+str(abs_x)+";"+str(abs_y)+"H") # Siehe https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_(Control_Sequence_Introducer)_sequences

        pass

    @staticmethod
    def _get_absolute_position() -> (int, int):
        sys.stdout.write("\x1b[6n")
        response=sys.stdin.read()
        print(response)
        response= response.replace('[', ';').replace('R', '').split(';')
        return response[1], response[2]

        

    def print_in_place(string):
        print(string, end="")
        print('\x1b['+str(len(string))+'D', end="")# go to initial position

    def paint(string, color):
        """
        color is of type Color.
        """
        s = color.sgr()+string+color.sgr_reset()
        print_in_place(s)

    


class Pixelflut(Canvas):
    """
    Spaßklasse.
    Assumes dark mode
    """

    def set_white(x, y):
        setCursor(x, y)
        print_in_place('#')

    def set_black(x, y):
        setCursor(x, y)
        print_in_place(' ')

    def set_color(x, y, color: list):
        # color is [r: int, g:int, b:int]
        setCursor(x, y)
        # TODO


######## Testing

def quadratflut():
    canvas = Pixelflut(100, 50)
    start = [0,0]
    size = 1
    while start[2]<50:
        for w in range(size):
            for h in range(size):
                set_white(start[0]+w, start[1]+h)
        start[0] += size
        start[1] += size
        size += 1

if __name__ == "__main__":
    quadratflut()

