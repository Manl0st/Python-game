import pygame
from collections import deque
from pygame.math import Vector2
from typing import TypeVar, Generic, TYPE_CHECKING
if TYPE_CHECKING: from .player import Player; from .arrow import Arrow; from .enemy import Enemy

ContextType = TypeVar('ContextType', bound=pygame.sprite.Sprite)

class State(Generic[ContextType]):
    def __init__(self, context : ContextType):
        self.context = context

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_input(self, input_state : dict, current_time : int, game_events_queue : deque):
        return None

    def update(self, current_time : int, game_events_queue : deque):
        return None