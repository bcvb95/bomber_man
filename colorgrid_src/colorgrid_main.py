import sys
import math
from misc import *

from colorgrid_consts import *
from packetmanager import PacketManager
from server import Server
from client import Client 
from player import Player


"""
    Server  |    ip: 127.0.0.1, port: 8909
    Client1 |    ip: 127.0.0.1, port: 8403
"""


def start_game(username, client_port, server_ip, server_port, is_server):
    pygame.init()
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode(SCR_SIZE) 
    colorgrid = ColorGrid(10)

    client_ip = getMyIP()

    player = None
    
    if is_server: # if player is a server
        player = Player(colorgrid,client_ip, client_port, client_ip, server_port, is_server)
        time.sleep(1)
        player.server.startBroadcasting()
    else:         # if the player is not a server
        player = Player(colorgrid, client_ip, client_port, server_ip, server_port )

    # log in
    while not player.client.logged_in:
        player.client.logIn(username)
        time.sleep(0.1)

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            keys = pygame.key.get_pressed()
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if event.type == QUIT or keys[K_ESCAPE]:
                if player.is_server:
                    player.server.stopBroadcasting()
                player.kill()
                player.logfile.close()
                sys.exit()
                
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    pressed_i = colorgrid.getRectIndexFromClick(mouse_x, mouse_y)
                    move  = str(pressed_i)
                    player.make_move(move)

            if keys[K_m]:
                player.make_move("MOVE")

        player.colorgrid_lock.acquire()
        colorgrid.drawGrid(screen)
        player.colorgrid_lock.release()

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


    def colorRect(self, index, color):
        if self.grid_rects[index][0] == None:
            self.grid_rects[index] = (color, self.grid_rects[index][1])  
        else:
            self.grid_rects[index] = (None, self.grid_rects[index][1])

    def getRectIndexFromClick(self ,x ,y):
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

        # return the index of the rext to be colored
        return min_i
