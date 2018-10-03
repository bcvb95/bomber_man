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
        self.move = None
        self.bomb = False

        self.queued_moves = []
        self.bombs = []

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
        self.player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
        if is_server:
            self.player.server.startBroadcasting()
        else:
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
            while not start_game:
                if len(self.player.server.connected_clients) != num_connected:
                    num_connected = len(self.player.server.connected_clients)

                for event in pygame.event.get():
                    if (event.type == KEYDOWN and event.key == K_s) or num_connected == 4:

                        self.player.server.sendInitGame()
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

        # list for holding all players movable object
        self.player_moveable_objects = []
        self.this_player_i = self.player.client.player_number-1


        for i in range(self.player.client.init_num_players):
            # init and calc start positions
            move_go = MoveableGameObject(STEPSIZE, PLAYER_IMG_DICT[i+1])
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
                if event.key in KEY_TO_DIR_DICT and not self.move_key_held:
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

                if self.gameboard.make_move(self.player_moveable_objects[self.this_player_i], self.move) == 0:
                    if self.player_moveable_objects[self.this_player_i].move(self.move) == 0:
                        self.player.make_move(move_msg)
        if self.bomb:
            if self.gameboard.place_bomb(self.player_moveable_objects[self.this_player_i]) != 1:
                p_i, p_j = self.player_moveable_objects[self.this_player_i].grid_pos
                self.bombs.append([ (p_i, p_j), time.time() ])
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
            # Bomb destroying here

        for move_go in self.player_moveable_objects:
            move_go.update()
        
        self.update_bombs()

    def draw(self):
        self.screen.fill((200,200,200))
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

    def update_bombs(self):
        ts = time.time()
        bombs_to_blow = []
        for i in range(len(self.bombs)):
            bomb = self.bombs[i]
            if (ts - bomb[1]) > BOMB_TIME:
                bombs_to_blow.append([bomb[0], i])

        for b2b in bombs_to_blow:
            i,j = b2b[0][0], b2b[0][1]
            self.gameboard.change_tile( i, j, 'e')
            move = "B%d/%d" % (i, j)
            self.player.make_move(move) 
            del self.bombs[b2b[1]]   # delete bomb from bomb list


class GameBoard(object):
    """
        Has a grid containing elements of the game.
             'e'        :   empty tile
            ['1'-'4']   :   player 1-4
             'b'        :   bomb
             'w'        :   static wall
             'd'        :   dynamic box
    """

    def __init__(self, size):
        self.size = size
        # init grid
        self.game_grid = [['e' for x in range(self.size[0])] for y in range(self.size[1])]

    def make_move(self, move_go, move):
        exit_code = 0
        from_ele = self.game_grid[move_go.grid_pos[1]][move_go.grid_pos[0]]
        # if the move is not a bomb move, try to move player
        dir = (move[1], move[0]) # direction is swapped arround
        from_j, from_i = move_go.grid_pos[1], move_go.grid_pos[0]
        new_j, new_i = from_j + dir[0], from_i + dir[1]
        in_bounds = ((new_j < self.size[0] and new_j >= 0) and (new_i < self.size[0] and new_i >= 0))
        if in_bounds:
            #--- if moving to an empty tile
            if self.game_grid[new_j][new_i] == 'e':
                if from_ele[0] == 'b':
                    # if moving from a tile with a bomb
                    self.change_tile(from_i, from_j, 'b')
                    self.change_tile(new_i, new_j, from_ele[1])
                else:
                    # if moving from an empty tile
                    self.change_tile(from_i, from_j, 'e')
                    self.change_tile(new_i, new_j, from_ele)
                move_go.grid_pos = (new_i, new_j)
            else:
                exit_code = 1
        else:
            exit_code = 1
        return exit_code

    def place_bomb(self, move_go):
        exit_code = 0
        p_j, p_i = move_go.grid_pos[1], move_go.grid_pos[0]
        from_ele = self.game_grid[p_j][p_i]
        if from_ele[0] != 'b': # if there's not a bomb already
            self.change_tile(p_i, p_j, 'b' + from_ele)
        else:
            exit_code = 1
        return exit_code


    def change_tile(self, i, j, new_ele):
        self.game_grid[j][i] = new_ele

    def print_grid(self):
        for row in self.game_grid:
            print(row)
        print('\n')

def main(username, client_port, server_ip, server_port, is_server):
    gameManager = GameManager(username, client_port, server_ip, server_port, is_server)
    gameManager.start_game()