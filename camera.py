import pygame
from pygame import Vector2
from player import Player

class Camera:
    def __init__(self, screen_width, screen_height, world_width, world_height):
        self.offset = Vector2(0, 0)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height

    def apply_to_pos(self, pos: Vector2):
        return pos - self.offset
    
    def screen_to_world(self, screen_pos: Vector2):
        return screen_pos + self.offset

    def update(self, player: 'Player'):
        self.offset = Vector2(player.pos.x - self.screen_width / 2, player.pos.y - self.screen_height / 2)
        self.offset.x = max(0, min(self.offset.x, self.world_width - self.screen_width))
        self.offset.y = max(0, min(self.offset.y, self.world_height - self.screen_height))