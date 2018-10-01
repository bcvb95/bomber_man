"""
    TODO:
        ** Add mutex for client login to server. And make client.logIn first return when logged in.
"""
import sys, time
import pygame
import misc
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

        # load fonts
        self.font_dejavu72 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 72)
        self.font_dejavu48 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 48)
        self.font_dejavu26 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 26)
        self.font_dejavu14 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 14)

        client_ip = misc.getMyIP()
        self.player = None

        # instantiate player
        if is_server:
            self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
            self.player.server.startBroadcasting()
        else:
            self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port)
            self.player.client.logIn()

        # add gameboard reference to client
        self.player.client.game_manager = self

        #setup gameboard
        self.gameboard = GameBoard(GRID_SIZE)


    def start_game(self):

        welcome_text = "Welcome to Bomberman!"
        client_wait_msg1 = "You are logged in as %s on %s:%s" % (self.username, misc.getMyIP(), self.client_port)
        client_wait_msg2 = "Waiting for the server to start the game."

        #------- LOGIN --------#
        start_game = False
        if self.player.is_server:
            # wait for host to start the game, when it chooses to.

            server_wait_msg1 = "You are a server on %s:%s" % (self.player.client.serverIP, self.player.client.serverPort) 
            server_wait_msg2 = "Wait for players to join the game, or start by pressing \"S\"" 
            server_wait_msg3 = "%d/4 players connected"

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

                # Draw server waiting screen
                self.screen.fill((150,150,150))
                welcome_label = self.font_dejavu72.render(welcome_text, 1, BLACK)

                server_wait_label1 = self.font_dejavu26.render(server_wait_msg1, 1, BLACK)
                server_wait_label2 = self.font_dejavu26.render(server_wait_msg2, 1, BLACK)
                server_wait_label3 = self.font_dejavu48.render(server_wait_msg3 % num_connected, 1, BLACK)

                # Draw text
                self.screen.blit(welcome_label, (SCREEN_WIDTH/2 - (welcome_label.get_width() / 2), (SCREEN_HEIGHT/4)))
                self.screen.blit(server_wait_label1, (SCREEN_WIDTH/2 - (welcome_label.get_width() /2), SCREEN_HEIGHT/3))
                self.screen.blit(server_wait_label2, (SCREEN_WIDTH/2 - (welcome_label.get_width() /2), SCREEN_HEIGHT/3 + 26))
                self.screen.blit(server_wait_label3, (SCREEN_WIDTH/2 - (server_wait_label3.get_width() / 2), SCREEN_HEIGHT/2))

                pygame.display.flip()

        while not self.player.client.doInitGame():
            self.screen.fill((150,150,150))
            # Draw server waiting screen
            welcome_label = self.font_dejavu72.render(welcome_text, 1, BLACK)
            client_wait_label1 = self.font_dejavu26.render(client_wait_msg1, 1, BLACK)
            client_wait_label2 = self.font_dejavu26.render(client_wait_msg2, 1, BLACK)

            self.screen.blit(welcome_label, (SCREEN_WIDTH/2 - (welcome_label.get_width() / 2), (SCREEN_HEIGHT/4)))
            self.screen.blit(client_wait_label1, (SCREEN_WIDTH/2 - (welcome_label.get_width()/2), SCREEN_HEIGHT/3))
            self.screen.blit(client_wait_label2, (SCREEN_WIDTH/2 - (welcome_label.get_width()/2), SCREEN_HEIGHT/3 + 26))

            pygame.display.flip()

        # list for holding all players movable object
        self.player_moveable_objects = []
        self.this_player_i = self.player.client.player_number-1

        for i in range(self.player.client.init_num_players):
            move_go = MoveableGameObject(STEPSIZE, PLAYER_IMG_DICT[i+1])
            start_i, start_j =PLAYER_START_IDX_POSITIONS[i]
            start_x, start_y = (TILE_SIZE+ start_i*TILE_SIZE),  (TILE_SIZE + start_j*TILE_SIZE)
            move_go.grid_pos = (start_i, start_j)
            move_go.scr_pos = (start_x, start_y)
            move_go.set_pos(start_x, start_y)
            self.player_moveable_objects.append(move_go)

        self.game_loop()

    def game_loop(self):
        game_running = True
        while game_running:
            self.handle_input()
            self.update()
            self.draw()

    def handle_input(self):
        self.do_move = (time.time() - self.player_moveable_objects[self.this_player_i].last_move > MINMOVEFREQ)
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
                self.player_moveable_objects[self.this_player_i].move(self.queued_dir_input)
                self.queued_dir_input = (0,0)
            elif self.player_moveable_objects[self.this_player_i].cur_dir != self.dir_input:
                self.player_moveable_objects[self.this_player_i].move(self.dir_input)

        for move_go in self.player_moveable_objects:
            move_go.update()

    def draw(self):
        self.screen.fill((200,200,200))
        for move_object in self.player_moveable_objects:
            move_object.draw(self.screen)
        pygame.display.flip()

    def execute_move(self, move):
        move_list = misc.stringToListParser(move, ':')
        player_id = int(move_list[0][1])
        move = move_list[1]
        self.player_moveable_objects[player_id-1].move(MOVE_TO_DIR_DICT[move])
        print("%s do_moves: " % self.username, move_list)

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