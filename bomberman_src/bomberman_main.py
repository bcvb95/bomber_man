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
    player_char_img_dict = res_loader.load_player_images()

    client_ip = misc.getMyIP()
    player = None

    # instantiate player  
    if is_server:
        player = BMPlayer(username,client_ip, client_port, server_ip, server_port, is_server)
        player.server.startBroadcasting()
    else:
        player = BMPlayer(username,client_ip, client_port, server_ip, server_port)
        player.client.logIn()
    
    # wait for the client to log into the server
    while not player.client.logged_in:
        time.sleep(0.001)

    #setup gameboard
    gameboard = GameBoard(GRID_SIZE)

    #TODO Instatiate clients player_model 

    # instantiate THIS players character, which is object that is being drawn
    player_char = MoveableGameObject(STEPSIZE, player_char_img_dict[player.client.player_number])

    player_i = player.client.player_number-1
    start_i, start_j =PLAYER_START_IDX_POSITIONS[player_i]
    start_x, start_y = (TILE_SIZE+ start_i*TILE_SIZE),  (TILE_SIZE + start_j*TILE_SIZE)
    player_char.grid_pos = (start_i, start_j)
    player_char.scr_pos = (start_x, start_y)
    player_char.set_pos(start_x, start_y)

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
                    start_game = True
                    print("> Starting game!")
    else:
        print("\n\nWaiting for the host to start the game. DEBUG: press s to start anyway\n")
        while not start_game:
            for event in pygame.event.get():
                if (event.type == KEYDOWN and event.key == K_s):
                    start_game = True


    queued_dir_input = (0,0)
    dir_input = (0,0)
    
    game_running = True
    while game_running:
        do_move = (time.time() - player_char.last_move > MINMOVEFREQ)
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
                player_char.move(queued_dir_input)
                queued_dir_input = (0,0)
            else:
                player_char.move(dir_input)

        player_char.update()

        #---- DRAW ----#
        screen.fill((200,200,200))
        player_char.draw(screen)
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