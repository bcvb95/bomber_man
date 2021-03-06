"""
    TODO:
        1.  Make this class derive from a base class that only has the "moving" part
        2.
"""
import time
import pygame
from pygame.locals import *
from gameobject import GameObject
from bomberman_consts import *

class MoveableGameObject(GameObject):
    def __init__(self, stepsize, img):
        GameObject.__init__(self, img)
        self.step_size = STEPSIZE
        self.dest = None
        self.cur_dir = (0,0)
        self.source = self.rect.topleft
        self.last_move = 0
        self.last_step = 0

        self.scr_pos = (0,0)
        self.grid_pos = (0,0)

        # debug
        self.movecount = 0

    def update(self):
        if self.dest and time.time() - self.last_step > STEPFREQ:
            self.movetowarddest()

    def move(self, dir):
        if self.dest:
            return 1
        self.source = self.grid_pos
        self.movecount = 0
        self.cur_dir = dir
        self.dest = ((self.rect.topleft[0]+dir[0]*self.rect.width, \
                    self.rect.topleft[1]+dir[1]*self.rect.height))
        return 0
        #PLANT BOMB HERE

    def movetowarddest(self):
        pos = self.rect.topleft
        self.movecount += 1
        if max(self.dest[0], pos[0]) - min(self.dest[0], pos[0]) + max(self.dest[1], pos[1]) - min(self.dest[1], pos[1]) <= self.step_size:
            self.rect.topleft = self.dest
            self.dest = None
            self.cur_dir = (0,0)
            return

        if self.dest[0] > pos[0]:
            self.move_step((1, 0))
        elif self.dest[0] < pos[0]:
            self.move_step((-1, 0))
        elif self.dest[1] > pos[1]:
            self.move_step((0, 1))
        elif self.dest[1] < pos[1]:
            self.move_step((0, -1))
        self.last_step = time.time()

    def move_step(self, _dir):
        self.rect.topleft = (self.rect.topleft[0]+_dir[0]*self.step_size, \
                             self.rect.topleft[1]+_dir[1]*self.step_size)