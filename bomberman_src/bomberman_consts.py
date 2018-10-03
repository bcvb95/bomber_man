import pygame
from pygame.locals import *
import os

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 900,900
GRID_SIZE = GRID_WIDTH, GRID_HEIGHT = 13,13
TILE_SIZE = 60

PLAYER_START_POSITIONS = [(50,50), (SCREEN_WIDTH-50, 50), (50, SCREEN_HEIGHT-50), (SCREEN_WIDTH-50, SCREEN_HEIGHT-50)]
PLAYER_START_IDX_POSITIONS = [(0,0), (GRID_WIDTH-1, 0), (GRID_WIDTH-1, GRID_HEIGHT-1), (0, GRID_HEIGHT-1) ]

BLACK = Color(0,0,0,1)
WHITE = Color(255,255,255,1)
RED = Color(255,0,0,1)
GREEN = Color(0,255,0,1)
BLUE = Color(0,0,255,1)
ORANGE = Color(200,200,0,1)

BOMB_TIME = 5

#----- Movable gameobject constants-----#
STEPSIZE = 3 # Must be int
MINMOVEFREQ = 0.3
STEPFREQ = 0.005

KEY_TO_DIR_DICT = {
    K_LEFT:  (-1, 0),
    K_a:     (-1, 0),
    K_RIGHT: (1, 0),
    K_d:     (1, 0),
    K_UP:    (0, -1),
    K_w:     (0, -1),
    K_DOWN:  (0, 1),
    K_s:     (0, 1)
}

DIR_TO_MOVE_DICT = {
    (-1, 0): 'l',
    (1, 0):  'r',
    (0, -1): 'u',
    (0, 1):  'd',
}

MOVE_TO_DIR_DICT = {
    'l' : (-1,0),
    'r' : (1, 0),
    'u' : (0,-1),
    'd' : (0, 1)
}


#------ RESOURCES ------#
res_path = "%s/res" % os.path.dirname(os.path.realpath(__file__))
PLAYER_IMG_DICT= {
    1 : pygame.image.load('%s/images/player1_img.png' % res_path),
    2 : pygame.image.load('%s/images/player2_img.png' % res_path),
    3 : pygame.image.load('%s/images/player3_img.png' % res_path),
    4 : pygame.image.load('%s/images/player4_img.png' % res_path)
}

GAMEBOARD_TEXTURES = {
    "bounding_walls" : pygame.image.load("%s/images/bounding_walls.png" % res_path),
    "static_wall"    : pygame.image.load("%s/images/static_wall.png" % res_path),
    "floor"          : pygame.image.load("%s/images/floor.png" % res_path),
}