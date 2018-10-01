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

def start_game(username, client_port, server_ip, server_port, is_server):
    # init pygame and screen
    pygame.init()
    pygame.display.set_caption("Bomberman Pygame-edition")
    screen = pygame.display.set_mode(SCREEN_SIZE)

    # load images
    player_img_dict = res_loader.load_player_images()

    client_ip = misc.getMyIP()
    player = None

    # instantiate player  
    if is_server:
        player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
        player.server.startBroadcasting()
    else:
        player = BMPlayer(username,client_ip, client_port, server_ip, server_port)
        player.client.logIn()

    #setup gameboard
    gameboard = GameBoard(GRID_SIZE)

    #------- LOGIN --------#
    start_game = False
    if player.is_server: 
        # wait for host to start the game, when it chooses to.
        print("\n\nWaiting for players to join.\n Press \"S\" to start game.\n\n")

        num_connected = len(player.server.connected_clients)
        print("> %d/4 number of players connected." % num_connected)
        while not start_game:
            if len(player.server.connected_clients) != num_connected:
                num_connected = len(player.server.connected_clients)
                print("> %d/4 number of players connected" % num_connected)

            for event in pygame.event.get():
                if (event.type == KEYDOWN and event.key == K_s) or num_connected == 4:

                    player.server.sendInitGame()
                    start_game = True
                    print("> Starting game!")
    
    print("\n\nWaiting for the host to start the game. DEBUG: press s to start anyway\n")
    while not player.client.doInitGame():
        for event in pygame.event.get():
            if (event.type == KEYDOWN and event.key == K_s):
                start_game = True

    #TODO Instatiate clients player_model 

    # list for holding all players movable object
    player_moveable_objects = []
    this_player_i = player.client.player_number-1

    for i in range(player.client.init_num_players):
        move_go = MoveableGameObject(STEPSIZE, player_img_dict[i+1])
        start_i, start_j =PLAYER_START_IDX_POSITIONS[i]
        start_x, start_y = (TILE_SIZE+ start_i*TILE_SIZE),  (TILE_SIZE + start_j*TILE_SIZE)
        move_go.grid_pos = (start_i, start_j)
        move_go.scr_pos = (start_x, start_y)
        move_go.set_pos(start_x, start_y)
        player_moveable_objects.append(move_go)

    print(player_moveable_objects)

    queued_dir_input = (0,0)
    dir_input = (0,0)
    
    game_running = True
    while game_running:
        do_move = (time.time() - player_moveable_objects[this_player_i].last_move > MINMOVEFREQ)
        for event in pygame.event.get():
            exit_cond = (event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)) 
            if exit_cond: # If closing game
                if player.is_server:
                    player.server.stopBroadcasting()
                player.kill()
                sys.exit()
            
            #---- move specific input ----#
            move = None
            if event.type == pygame.KEYDOWN:
                if event.key in DIRECTION_INPUT_DICT:
                    dir_input = DIRECTION_INPUT_DICT[event.key]
                    move = dir_input
                elif event.key == K_SPACE:
                    move = "b"
            elif event.type == pygame.KEYUP:
                if event.key in DIRECTION_INPUT_DICT:
                    if not do_move:
                        queued_dir_input = dir_input
                    dir_input = (0, 0)

            if move != None: # if the player is making a move
                move_msg = ""
                if move == (1, 0):
                    move_msg = 'r'
                elif move == (-1,0):
                    move_msg = 'l'
                elif move == (0,1):
                    move_msg = 'd'
                elif move == (0,-1):
                    move_msg = 'u'
                elif move == 'b':
                    move_msg = 'b'

                player.make_move(move_msg)
                

        #---- UPDATE ----#
        if do_move:
            if queued_dir_input != (0,0):
                player_moveable_objects[this_player_i].move(queued_dir_input)
                queued_dir_input = (0,0)
            else:
                player_moveable_objects[this_player_i].move(dir_input)
                player_moveable_objects[this_player_i].move(dir_input)

        player_moveable_objects[this_player_i].update()

        #---- DRAW ----#
        screen.fill((200,200,200))

        for move_go in player_moveable_objects:
            move_go.draw(screen)

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

if __name__ == "__main__":
    start_game()