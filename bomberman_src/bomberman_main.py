"""
    TODO:
        ** Add mutex for client login to server. And make client.logIn first return when logged in.
"""
import sys, time
import pygame
import misc
import bomberman_res_loader as res_loader
from pygame.locals import *
from bomberman_consts import *
from bomberman_player import BMPlayer
from movable_gameobject import MoveableGameObject

class GameManager(object):
    def __init__(self, username, client_port, server_ip, server_port, is_server):
        self.username = username
        self.client_port = client_port
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_server = is_server

        # input
        self.queued_dir_input = (0,0)
        self.dir_input = (0,0)
        self.move_key_held = None
        self.do_move = False

        # init pygame and screen
        pygame.init()
        pygame.display.set_caption("Bomberman Pygame-edition")
        self.screen = pygame.display.set_mode(SCREEN_SIZE)

        # load images
        player_char_img_dict = res_loader.load_player_images()

        client_ip = misc.getMyIP()
        self.player = None

        # instantiate player
        if is_server:
            self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
            self.player.server.startBroadcasting()
        else:
            self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port)
            self.player.client.logIn()

        # wait for the client to log into the server
        while not self.player.client.logged_in:
            time.sleep(0.001)

        #setup gameboard
        self.gameboard = GameBoard(GRID_SIZE)

        #TODO Instatiate clients player_model

        # instantiate THIS players character, which is object that is being drawn
        self.player_char = MoveableGameObject(STEPSIZE, player_char_img_dict[self.player.client.player_number])

        player_i = self.player.client.player_number-1
        start_i, start_j =PLAYER_START_IDX_POSITIONS[player_i]
        start_x, start_y = (TILE_SIZE+ start_i*TILE_SIZE),  (TILE_SIZE + start_j*TILE_SIZE)
        self.player_char.grid_pos = (start_i, start_j)
        self.player_char.scr_pos = (start_x, start_y)
        self.player_char.set_pos(start_x, start_y)

    def start_game(self):
        #------- LOGIN --------#
        start_game = False
        if self.player.is_server:
            # wait for host to start the game, when it chooses to.
            print("\n\nWaiting for players to join.\n Press \"S\" to start game.\n\n")

            num_connected = len(self.player.server.connected_clients)
            print("> %d/4 number of players connected." % num_connected)
            while not start_game:
                if len(self.player.server.connected_clients) != num_connected:
                    num_connected = len(self.player.server.connected_clients)
                    print("> %d/4 number of players connected" % num_connected)

                for event in pygame.event.get():
                    if (event.type == KEYDOWN and event.key == K_s) or num_connected == 4:

                        self.player.server.sendInitGame()
                        start_game = True
                        print("> Starting game!")
        else:
            print("\n\nWaiting for the host to start the game. DEBUG: press s to start anyway\n")
            while not self.player.client.doInitGame():
                for event in pygame.event.get():
                    if (event.type == KEYDOWN and event.key == K_s):
                        start_game = True
        self.game_loop()

    def game_loop(self):
        game_running = True
        while game_running:
            self.handle_input()
            self.update()
            self.draw()

    def handle_input(self):
        self.do_move = (time.time() - self.player_char.last_move > MINMOVEFREQ)
        for event in pygame.event.get():
            exit_cond = (event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE))
            if exit_cond: # If closing game
                if self.player.is_server:
                    self.player.server.stopBroadcasting()
                self.player.kill()
                sys.exit()

            #---- move specific input ----#
            move = None
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_TO_DIR_DICT and not self.move_key_held:
                    self.dir_input = KEY_TO_DIR_DICT[event.key]
                    move = self.dir_input
                    self.move_key_held = event.key
                elif event.key == K_SPACE:
                    move = "b"
            elif event.type == pygame.KEYUP:
                if event.key in KEY_TO_DIR_DICT and event.key == self.move_key_held:
                    if not self.do_move:
                        self.queued_dir_input = self.dir_input
                    self.dir_input = (0, 0)
                    self.move_key_held = None

            if move != None: # if the player is making a move
                move_msg = ""
                if move in DIR_TO_MOVE_DICT:
                    move_msg = DIR_TO_MOVE_DICT[move]
                elif move == 'b':
                    move_msg = 'b'

                self.player.make_move(move_msg)

    def update(self):
        if self.do_move:
            if self.queued_dir_input != (0,0):
                self.player_char.move(self.queued_dir_input)
                self.queued_dir_input = (0,0)
            elif self.player_char.cur_dir != self.dir_input:
                self.player_char.move(self.dir_input)
        self.player_char.update()

    def draw(self):
        self.screen.fill((200,200,200))
        self.player_char.draw(self.screen)
        pygame.display.flip()

class GameBoard(object):
    """
        Has a grid containing elements of the game.
             'e'        :   empty tile
            ['1'-'4']   :   player 1-4
             'b'        :   bomb
             'w'        :   static wall
             'b'        :   dynamic box
    """

    def __init__(self, size):
        self.size = size
        # init grid
        self.game_grid = [["e"]*size[1]]*size[0]
        for row in self.game_grid:
            continue
            #print(row)

    def change_tile(self, i, j, new_ele):
        self.game_grid[i][j] = new_ele

def main(username, client_port, server_ip, server_port, is_server):
    gameManager = GameManager(username, client_port, server_ip, server_port, is_server)
    gameManager.start_game()