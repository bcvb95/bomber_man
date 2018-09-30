import pygame
from pygame.locals import *
from bomberman_consts import *

class GameObject(object):
    def __init__(self, img):

        self.image = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()

    def get_pos(self):
        return (self.rect.left, self.rect.top)

    def set_pos(self, x, y):
        self.rect.topleft = (x,y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)