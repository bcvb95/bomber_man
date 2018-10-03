import pygame, time
from pygame.locals import *

from bomberman_consts import *
from gameobject import GameObject

class Bomb(GameObject):
    def __init__(self, grid_pos):
        GameObject.__init__(self, BOMB_IMG)

        self.grid_pos = grid_pos
        self.time_placed = time.time()

        scr_x = TILE_SIZE + self.grid_pos[0]*TILE_SIZE
        scr_y = TILE_SIZE + self.grid_pos[1]*TILE_SIZE
        self.set_pos(scr_x, scr_y)

    def isGonnaExplode(self):
        if (time.time() - self.time_placed) > BOMB_TIME:
            return True
        else:
            return False

    

