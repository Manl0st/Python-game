import pygame
from pygame.math import Vector2
from constants import *

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos : Vector2):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.image.fill((100, 100, 100))
        self.pos = pos
        self.rect = self.image.get_rect(center=pos)
        