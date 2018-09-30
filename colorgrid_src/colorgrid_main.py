import sys
import math
import misc

from colorgrid_consts import *
from colorgrid_player import CGPlayer

MOVE_CD = 0.001
"""
    Server  |    ip: 127.0.0.1, port: 8909
    Client1 |    ip: 127.0.0.1, port: 8403
"""
def start_game(username, client_port, server_ip, server_port, is_server):
    """ This function is called when the game is started  """
    pygame.init()
    clock = pygame.time.Clock()

    mouse_down = False
    last_mouse_keys = []
    last_cd = misc.time.time()

    screen = pygame.display.set_mode(SCR_SIZE)
    colorgrid = ColorGrid(20)
    client_ip = misc.getMyIP()
    player = None

    if is_server: # if player is a server
        player = CGPlayer(username, colorgrid,client_ip, client_port, client_ip, server_port, is_server)
        player.server.startBroadcasting()
    else:         # if the player is not a server
        player = CGPlayer(username, colorgrid, client_ip, client_port, server_ip, server_port )

    # log in
    if not player.is_server:
        player.client.should_sync = True
        player.client.logIn()

    while True:
        screen.fill(WHITE)
        for event in pygame.event.get():
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                if player.is_server:
                    player.server.stopBroadcasting()
                player.kill()
                sys.exit()

            elif event.type == MOUSEBUTTONDOWN and not mouse_down:
                mouse_down = True
                last_mouse_keys = pygame.mouse.get_pressed()
            elif event.type == MOUSEBUTTONUP:
                mouse_down = False

            if event.type == pygame.KEYDOWN:
                num_key = event.key-48
                if num_key > 0 and num_key < 10:
                    player.selected_color = num_key-1

        if mouse_down:
            pressed_i = colorgrid.getRectIndexFromClick(mouse_x, mouse_y)
            move  = str(pressed_i)
            if last_mouse_keys[0]:
                move += '/l'
                if (misc.time.time() - last_cd) > MOVE_CD:
                    player.make_move(move)
                    last_cd = misc.time.time()

            if last_mouse_keys[2]:
                move += '/r'
                if (misc.time.time() - last_cd) > MOVE_CD:
                    player.make_move(move)
                    last_cd = misc.time.time()
        player.colorgrid_lock.acquire()
        colorgrid.drawGrid(screen)
        player.colorgrid_lock.release()
        pygame.display.flip()

class ColorGrid(object):
    def __init__(self, rect_size):
        self.rect_size = rect_size

        self.grid_rects = []
        for x in range(0, SCR_WIDTH, self.rect_size):
            for y in range(0, SCR_HEIGHT, self.rect_size):
                rect = Rect(x,y, self.rect_size, self.rect_size)
                filled_rect = (-1, rect)
                self.grid_rects.append(filled_rect)


    def drawGrid(self, screen):
        for i in range(len(self.grid_rects)):
            rect = self.grid_rects[i]
            if rect[0] == -1:
                pygame.draw.rect(screen, BLACK, rect[1], 1)
            else:
                try:
                    color = CLIENT_COLORS[rect[0]]
                except:
                    color = BLACK
                pygame.draw.rect(screen, color, rect[1])

            # else if color grid


    def colorRect(self, index, color):
        self.grid_rects[index] = (color, self.grid_rects[index][1])

    def clearRect(self, index):
        self.grid_rects[index] = (-1, self.grid_rects[index][1])

    def getRectIndexFromClick(self ,x ,y):
        # find tile closest to mousepress
        min_dist = 9999999
        min_i = 0
        for i in range(len(self.grid_rects)):
            rect = self.grid_rects[i]
            center_x, center_y = rect[1].centerx, rect[1].centery
            dist = misc.get_dist( (x,y), (center_x, center_y))
            if dist < min_dist:
                min_dist = dist
                min_i = i

        # return the index of the rext to be colored
        return min_i