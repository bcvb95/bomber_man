import pygame
from pygame.locals import *

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 900,900
GRID_SIZE = GRID_WIDTH, GRID_HEIGHT = 13,13
TILE_SIZE = 60

PLAYER_START_POSITIONS = [(50,50), (SCREEN_WIDTH-50, 50), (50, SCREEN_HEIGHT-50), (SCREEN_WIDTH-50, SCREEN_HEIGHT-50)]
PLAYER_START_IDX_POSITIONS = [(0,0), (GRID_WIDTH-1, 0), (GRID_WIDTH-1, GRID_HEIGHT-1), (0, GRID_HEIGHT-1) ]

#----- Movable gameobject constants-----#
STEPSIZE = 1
MINMOVEFREQ = 0.15
DIRECTION_INPUT_DICT = {
                                K_LEFT:  (-1, 0),
                                K_a:     (-1, 0),
                                K_RIGHT: (1, 0),
                                K_d:     (1, 0),
                                K_UP:    (0, -1),
                                K_w:     (0, -1),
                                K_DOWN:  (0, 1),
                                K_s:     (0, 1)
                        }
