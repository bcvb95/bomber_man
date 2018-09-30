import pygame
from pygame.locals import *

class GameObject(object):
    def __init__(self, img):

        self.image = img 
        self.rect = self.image.get_rect()
    
    def get_pos(self):
        return (self.rect.left, self.rect.top)

    def set_pos(self, x, y):
        self.rect.centerx = x
        self.rect.centery = y

    def draw(self, screen):
        screen.blit(self.image, self.rect)