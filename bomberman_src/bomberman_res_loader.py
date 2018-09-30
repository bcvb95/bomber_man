import os
import pygame
from pygame.locals import *

def load_player_images():
    img_dict = { 1 : pygame.image.load('bomberman_src/res/images/player1_img.png'),
                 2 : pygame.image.load('bomberman_src/res/images/player2_img.png'),
                 3 : pygame.image.load('bomberman_src/res/images/player3_img.png'),
                 4 : pygame.image.load('bomberman_src/res/images/player4_img.png')}

    return img_dict