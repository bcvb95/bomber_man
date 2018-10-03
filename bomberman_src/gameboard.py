from bomberman_consts import *

class GameBoard(object):
    """
        Has a grid containing elements of the game.
             'e'        :   empty tile
            ['1'-'4']   :   player 1-4
             'b'        :   bomb
             'w'        :   static wall
             'd'        :   dynamic box / destructable
    """
    def __init__(self, size, board_textures, bomb_tex):
        self.size = size
        # init grid
        self.game_grid = [['e' for x in range(self.size[0])] for y in range(self.size[1])]
        self.bombs = []

        self.bounding_walls_tex = board_textures["bounding_walls"]
        self.floor_tex = board_textures["floor"]
        self.static_wall_tex = board_textures["static_wall"]
        self.destructable_wall_tex = board_textures["destructable_wall"]
        self.bomb_tex = bomb_tex
        self.layout_tex = None

        self.static_walls = []
        self.destructable_walls = []

    def set_layout(self, layout_tex):
        self.layout_tex = layout_tex
        # Place walls
        for i in range(GRID_WIDTH):
            x = (i+1) * TILE_SIZE
            for j in range(GRID_HEIGHT):
                y = (j+1) * TILE_SIZE
                pixel_col = self.layout_tex.get_at((i,j)).normalize()[:3]
                if pixel_col == (0,0,0):
                    self.static_walls.append((x,y))
                    self.game_grid[i][j] = 'w'
                elif pixel_col == (1, 0, 0):
                    self.destructable_walls.append((x,y))
                    self.game_grid[i][j] = 'd'

    def change_tile(self, i, j, new_ele):
        self.game_grid[j][i] = new_ele

    def check_move(self, move_go, move):
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
                return 0
            else:
                exit_code = 1
        else:
            exit_code = 1
        return exit_code

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

    def check_place_bomb(self, move_go):
        exit_code = 0
        i, j = move_go.grid_pos
        from_ele = self.game_grid[j][i]
        if from_ele[0] != 'b': # if there's not a bomb already
            exit_code = 0
        else:
            exit_code = 1
        return exit_code

    def place_bomb(self, move_go):
        exit_code = 0
        i, j = move_go.grid_pos
        from_ele = self.game_grid[j][i]
        if from_ele[0] != 'b': # if there's not a bomb already
            if move_go.dest:   # if move_go is moving
                ps_i, ps_j = move_go.source
                from_ele = self.game_grid[ps_j][ps_i]
                self.change_tile(ps_i, ps_j, 'b')
                self.add_bomb((ps_i, ps_j))
            else:
                p_i, p_j = move_go.grid_pos
                from_ele = self.game_grid[p_j][p_i]
                if len(from_ele) == 1:
                    self.change_tile(p_i, p_j, 'b' + from_ele)
                    self.add_bomb((p_i, p_j))
                else:
                    self.change_tile(p_i, p_j, 'b')
                    self.add_bomb((p_i, p_j))
        else:
            exit_code = 1
        return exit_code

    def add_bomb(self, grid_pos):
        new_bomb = Bomb(grid_pos, self.bomb_tex)
        self.bombs.append(new_bomb)

    def update_bombs(self, player):
        bombs_to_blow = []
        for i in range(len(self.bombs)):
            bomb = self.bombs[i]
            if bomb.isGonnaExplode():
                bombs_to_blow.append([bomb, i])

        for b2b in bombs_to_blow:
            i,j = b2b[0].grid_pos[0], b2b[0].grid_pos[1]
            self.change_tile( i, j, 'e')
            move = "B%d/%d" % (i, j)
            player.make_move(move)
            is_in = (b2b[0] in self.bombs)
            if is_in and len(self.bombs) > b2b[1]:
                del self.bombs[b2b[1]]   # delete bomb from bomb list

    def print_grid(self):
        for row in self.game_grid:
            print(row)
        print('\n')

    def update(self, player):
        self.update_bombs(player)

    def draw(self, screen):
        screen.blit(self.floor_tex, (0,0))
        screen.blit(self.bounding_walls_tex, (0,0))
        for static_wall in self.static_walls:
            screen.blit(self.static_wall_tex, static_wall)
        for destructable_wall in self.destructable_walls:
            screen.blit(self.destructable_wall_tex, destructable_wall)
        for bomb in self.bombs:
            bomb.draw(screen)