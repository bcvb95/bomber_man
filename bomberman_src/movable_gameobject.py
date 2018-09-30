import time
import pygame
from pygame.locals import *
from gameobject import GameObject

class MoveableGameObject(GameObject):
    def __init__(self, stepsize, img):
        GameObject.__init__(self, img)

        self.step_size = stepsize
        self.dest = None
        self.source = self.rect.topleft
        self.last_move = 0

        self.scr_pos = (0,0)
        self.grid_pos = (0,0)

        #---- input related ----#
        self.direction_input_dict = {
                                        pygame.K_LEFT:  (-1, 0),
                                        pygame.K_a:     (-1, 0),
                                        pygame.K_RIGHT: (1, 0),
                                        pygame.K_d:     (1, 0),
                                        pygame.K_UP:    (0, -1),
                                        pygame.K_w:     (0, -1),
                                        pygame.K_DOWN:  (0, 1),
                                        pygame.K_s:     (0, 1)
                                    }
        self.queued_dir_input = (0,0)
        self.dir_input = (0,0)

    def update(self):
        if self.dest:
            self.movetowarddest()

    def move(self, dir):
        if self.dest:
            return
        self.dest = ((self.rect.topleft[0]+dir[0]*self.rect.width, \
                      self.rect.topleft[1]+dir[1]*self.rect.height))
        self.source = self.rect.topleft

    def movetowarddest(self):
        pos = self.rect.topleft
        if abs(self.dest[0] - pos[0]) + abs(self.dest[1] - pos[1]) <= self.step_size:
            self.rect.topleft = self.dest
            self.dest = None
            self.last_move = time.time()
            return

        if self.dest[0] > pos[0]:
            self.move_step((1, 0))
        elif self.dest[0] < pos[0]:
            self.move_step((-1, 0))
        elif self.dest[1] > pos[1]:
            self.move_step((0, 1))
        elif self.dest[1] < pos[1]:
            self.move_step((0, -1))

    def move_step(self, _dir):
        self.rect.topleft = (self.rect.topleft[0]+_dir[0]*self.step_size, \
                             self.rect.topleft[1]+_dir[1]*self.step_size)

    def handle_input(self, event, do_move):
        move = None
        if event.type == pygame.KEYDOWN:
            if event.key in self.direction_input_dict:
                self.dir_input = self.direction_input_dict[event.key]
                move = self.dir_input
            elif event.key == K_SPACE:
                move = "b"

        elif event.type == pygame.KEYUP:
            if event.key in self.direction_input_dict:
                if not do_move:
                    self.queued_dir_input = self.dir_input
                self.dir_input = (0, 0)
        return move

    def do_move(self):
        if self.queued_dir_input != (0,0):
            self.move(self.queued_dir_input)
            self.queued_dir_input = (0,0)
        else:
            self.move(self.dir_input)