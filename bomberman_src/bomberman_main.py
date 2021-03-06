"""
    TODO:
        ** Add mutex for client login to server. And make client.logIn first return when logged in.
"""
import sys, time
import pygame
from threading import Thread, Lock, Condition
import misc
from pygame.locals import *
from bomberman_consts import *
from bomberman_player import BMPlayer
from movable_gameobject import MoveableGameObject
from gameboard import GameBoard
from bomb import Bomb

class GameManager(object):
    def __init__(self, username, client_port, server_ip, server_port, is_server, layout=0):
        self.username = username
        self.client_port = client_port
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_server = is_server

        self.clock = pygame.time.Clock()

        # input
        self.queued_dir_input = (0,0)
        self.dir_input = (0,0)
        self.move_key_held = None
        self.do_move = False
        self.move = None
        self.bomb = False

        self.queued_moves = []

        # init pygame and screen
        pygame.init()
        pygame.display.set_caption("Bomberman Pygame-edition")
        pygame.display.set_caption("BOMBERMAN - User: " + self.username)
        self.screen = pygame.display.set_mode(SCREEN_SIZE)

        # load fonts
        self.font_dejavu72 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 72)
        self.font_dejavu48 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 48)
        self.font_dejavu26 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 26)
        self.font_dejavu14 = pygame.font.SysFont("res/fonts/dejavu_thin.ttf", 14)



        #------ RESOURCES ------#
        self.res_path = "%s/res" % os.path.dirname(os.path.realpath(__file__))
        self.player_img_dict = {
            1 : pygame.image.load('%s/images/player1_img.png' % self.res_path).convert_alpha(),
            2 : pygame.image.load('%s/images/player2_img.png' % self.res_path).convert_alpha(),
            3 : pygame.image.load('%s/images/player3_img.png' % self.res_path).convert_alpha(),
            4 : pygame.image.load('%s/images/player4_img.png' % self.res_path).convert_alpha()
        }

        bomb_img = pygame.image.load('%s/images/bomb_img.png' % self.res_path).convert_alpha()

        gameboard_textures = {
            "bounding_walls"    : pygame.image.load("%s/images/bounding_walls.png" % self.res_path).convert_alpha(),
            "static_wall"       : pygame.image.load("%s/images/static_wall.png" % self.res_path).convert_alpha(),
            "floor"             : pygame.image.load("%s/images/floor.png" % self.res_path).convert_alpha(),
            "destructable_wall" : pygame.image.load("%s/images/destructable_wall.png" % self.res_path).convert_alpha(),
        }

        client_ip = misc.getMyIP()
        self.player = None

        # instantiate player
        self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
        if is_server:
            self.player.server.startBroadcasting()
        else:
            self.player.client.logIn()

 
        # add gameboard reference to client
        self.player.client.game_manager = self

        #setup gameboard
        self.layout = layout
        self.gameboard = GameBoard(GRID_SIZE, gameboard_textures, bomb_img)
        self.gameboard_layout_tex = None
        if is_server:
            self.load_layout(self.layout)

    def load_layout(self, layout):
        if layout == 0:   layout_tex_path = "%s/gameboard/gameboard_layout_empty.png" % self.res_path
        elif layout == 1: layout_tex_path = "%s/gameboard/gameboard_layout1.png" % self.res_path
        else: sys.exit("Unknown layout.")
        self.gameboard_layout_tex = pygame.image.load(layout_tex_path)
        self.gameboard.set_layout(self.gameboard_layout_tex)

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
            while not start_game:
                if len(self.player.server.connected_clients) != num_connected:
                    num_connected = len(self.player.server.connected_clients)

                for event in pygame.event.get():
                    if (event.type == KEYDOWN and event.key == K_s) or num_connected == 4:
                        self.player.server.sendInitGame("%d" % self.layout)
                        start_game = True

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

        if not self.is_server:
            self.load_layout(self.player.layout)

        # list for holding all players movable object
        self.player_moveable_objects = []
        self.this_player_i = self.player.client.player_number-1


        for i in range(self.player.init_num_players):
            # init and calc start positions
            move_go = MoveableGameObject(STEPSIZE, self.player_img_dict[i+1])
            start_i, start_j =PLAYER_START_IDX_POSITIONS[i]
            start_x, start_y = (TILE_SIZE+ start_i*TILE_SIZE),  (TILE_SIZE + start_j*TILE_SIZE)
            # update gameboard
            player_num = str(i+1)
            self.gameboard.change_tile(start_i, start_j, player_num)
            # update moveable go
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
            self.clock.tick(60)

    def handle_input(self):
        move_obj = self.player_moveable_objects[self.this_player_i]
        last_move = move_obj.last_move
        self.do_move = (time.time() - last_move > MINMOVEFREQ)
        if self.do_move:
            move_obj.last_move = time.time()
        self.move = None
        self.bomb = False

        for event in pygame.event.get():
            exit_cond = (event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE))
            if exit_cond: # If closing game
                if self.player.is_server:
                    self.player.server.stopBroadcasting()
                self.player.kill()
                sys.exit()

            #---- move specific input ----#
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_TO_DIR_DICT:# and not self.move_key_held:
                    self.dir_input = KEY_TO_DIR_DICT[event.key]
                    self.move_key_held = event.key
                elif event.key == K_SPACE:
                    self.bomb = True
                elif event.key == K_p:
                    self.gameboard.print_grid()
            elif event.type == pygame.KEYUP:
                if event.key in KEY_TO_DIR_DICT:
                    if not self.do_move and time.time() - last_move > 0.1 and self.dir_input != move_obj.cur_dir:
                        self.queued_dir_input = self.dir_input
                    if self.move:
                        self.queued_dir_input = (0,0)
                    if event.key == self.move_key_held:
                        self.dir_input = (0,0)
                        self.move_key_held = None

        if self.do_move:
            if self.queued_dir_input != (0,0):
                self.move = self.queued_dir_input
                self.queued_dir_input = (0,0)
            elif self.dir_input != (0,0):
                self.move = self.dir_input

            if self.move: # if the player is making a move
                move_msg = "m"
                p_i, p_j = self.player_moveable_objects[self.this_player_i].grid_pos
                move_msg += DIR_TO_MOVE_DICT[self.move]

                if self.gameboard.check_move(self.player_moveable_objects[self.this_player_i], self.move) == 0:
                    if self.player_moveable_objects[self.this_player_i].move(self.move) == 0:
                        self.gameboard.make_move(self.player_moveable_objects[self.this_player_i], self.move)
                        self.player.make_move(move_msg)
        if self.bomb:
            if self.gameboard.check_place_bomb(self.player_moveable_objects[self.this_player_i]) == 0:
                self.gameboard.place_bomb(self.player_moveable_objects[self.this_player_i])
                self.player.make_move('b')


    def update(self):
        i = 0
        while i < len(self.queued_moves) and len(self.queued_moves) != 0:
            move, player_id = self.queued_moves[i]["move"], self.queued_moves[i]["pid"]
            if move[0] == 'm':
                move = move[1:]
                if self.player_moveable_objects[player_id].move(MOVE_TO_DIR_DICT[move]) != 1:
                    self.gameboard.make_move(self.player_moveable_objects[player_id], MOVE_TO_DIR_DICT[move])
                    del self.queued_moves[i]
                else:
                    i += 1
            elif move[0] == 'b':
                self.gameboard.place_bomb(self.player_moveable_objects[player_id])
                del self.queued_moves[i]
            elif move[0] == 'B':
                move = move[1:]
                bomb_pos = move.split('/')
                self.gameboard.change_tile(int(bomb_pos[0]), int(bomb_pos[1]), 'e')
                del self.queued_moves[i]

        for move_go in self.player_moveable_objects:
            move_go.update()

        self.gameboard.update(self.player)


    def draw(self):
        self.screen.fill((200,200,200))
        self.gameboard.draw(self.screen)
        for move_object in self.player_moveable_objects:
            move_object.draw(self.screen)
        pygame.display.flip()

    def execute_move(self, move):
        """ Is called from the client, when it recieves a moves that needs to be executed """
        move_list = misc.stringToListParser(move, ':')
        player_id = int(move_list[0][1])
        move = move_list[1]
        if self.this_player_i != player_id-1:
            if move in MOVE_TO_DIR_DICT:
                move = MOVE_TO_DIR_DICT[move]
            self.queued_moves.append({"move": move, "pid": player_id-1})

def main(username, client_port, server_ip, server_port, is_server, layout):
    gameManager = GameManager(username, client_port, server_ip, server_port, is_server, layout)
    gameManager.start_game()