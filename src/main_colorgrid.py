import sys
import pygame
from pygame.locals import *
import math
from misc import *

from listener import Listener
from server import Server
from client import Client 
from player import Player

SCR_SIZE = SCR_WIDTH, SCR_HEIGHT = 500, 500 

BLACK = Color(0,0,0,1)
WHITE = Color(255,255,255,1)
RED = Color(255,0,0,1)
GREEN = Color(0,255,0,1)
BLUE = Color(0,0,255,1)
ORANGE = Color(255,255,0,1)

def main():
    pygame.init()
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode(SCR_SIZE) 
    color_grid = ColorGrid(100)

    print("Welcom to Color-Grid!")

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            keys = pygame.key.get_pressed()

            mouse_x, mouse_y = pygame.mouse.get_pos()

            if event.type == QUIT or keys[K_ESCAPE]:
                sys.exit()

            if keys[K_w]:
                color_grid.colorTile(3, BLUE)
            
            if event.type == MOUSEBUTTONDOWN:
               if event.button == 1:
                   color_grid.colorTileClick(mouse_x, mouse_y, BLUE)

        color_grid.drawGrid(screen)


        clock.tick(10)
        pygame.display.flip()

class ColorGrid(object):
    def __init__(self, rect_size):
        self.rect_size = rect_size
        range(0,SCR_WIDTH, 20)
        
        self.grid_rects = []
        for x in range(0, SCR_WIDTH, self.rect_size):
            for y in range(0, SCR_HEIGHT, self.rect_size):
                rect = Rect(x,y, self.rect_size, self.rect_size)
                filled_rect = (None, rect)
                self.grid_rects.append(filled_rect)


    def drawGrid(self, screen):
        for i in range(len(self.grid_rects)):
            rect = self.grid_rects[i]
            if rect[0] == None:
                pygame.draw.rect(screen, BLACK, rect[1], 1)
            else:
                pygame.draw.rect(screen, rect[0], rect[1])
            # else if color grid
     

    def colorTileClick(self ,x ,y , color):
        # find tile closest to mousepress
        min_dist = 9999999
        min_i = 0
        for i in range(len(self.grid_rects)):
            rect = self.grid_rects[i]
            center_x, center_y = rect[1].centerx, rect[1].centery
            dist = get_dist( (x,y), (center_x, center_y))
            if dist < min_dist:
                min_dist = dist
                min_i = i

        # color the tile on index min_i
        self.grid_rects[min_i] = (color, self.grid_rects[min_i][1])
