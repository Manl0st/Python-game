import pygame
from pygame.math import Vector2
from collections import deque
from state import State
from constants import *

class ArrowIdleState(State['Arrow']):
    pass
      
class ArrowFlyingState(State['Arrow']):
    def __init__(self, arrow : 'Arrow'):
        super().__init__(arrow)
    
    def update(self, current_time : int, game_events_queue : deque):
        enemies = pygame.sprite.spritecollide(self.context, self.context.enemies_group, False)
        if enemies:
            game_events_queue.append({
                'type' : 'DEALING_DAMAGE',
                'from_what' : 'arrow',
                'targets' : enemies,
                'amount_damage' : self.context.damage,
            })
            return ArrowDestroyingState(self.context)
        if pygame.sprite.spritecollide(self.context, self.context.walls, False):
            return ArrowDestroyingState(self.context)
        self.context.pos += self.context.velocity
        self.context.rect.center = self.context.pos
        return None

class ArrowDestroyingState(State['Arrow']):
    def __init__(self, arrow : 'Arrow'):
        super().__init__(arrow)
        
    def update(self, current_time : int, game_events_queue : deque):
        self.context.kill()
        return None
    
class Arrow(pygame.sprite.Sprite):
    def __init__(self, tension : float, start_pos : Vector2, target_pos : Vector2, speed : int,
                 damage : int, state : str, enemies_group : pygame.sprite.Group, walls : pygame.sprite.Group):
        super().__init__()
        self.image = pygame.Surface([20, 5])
        self.image.fill((0, 0, 0))
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(center=(start_pos))
        self.tension = tension
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.speed = speed
        self.damage = damage * tension
        self.pos = start_pos
        self.state = state
        self.enemies_group = enemies_group
        self.walls = walls
        self.velocity = Vector2(0, 0)
        if state == 'flight':
            direction_vec = Vector2(target_pos) - Vector2(start_pos)
            if direction_vec.length_squared():
                self.velocity = direction_vec.normalize() * self.speed
                angle_degrees = self.velocity.angle_to(Vector2(1, 0))
                self.image = pygame.transform.rotate(self.original_image, -angle_degrees)
                self.rect = self.image.get_rect(center=self.pos)
                self.current_state_obj: State = ArrowFlyingState(self)
            else:
                self.velocity = Vector2(0,0)
                self.current_state_obj = ArrowIdleState(self)
        elif state == 'idle':
            self.current_state_obj = ArrowIdleState(self)
        else:
            self.current_state_obj = ArrowFlyingState(self)
        self.current_state_obj.enter()
        
    def change_state(self, new_state : State):
        if self.current_state_obj:
            self.current_state_obj.exit()
        self.current_state_obj = new_state
        self.current_state_obj.enter()
        
    def update(self, game_events_queue : deque, current_time : int):
        new_state = self.current_state_obj.update(current_time, game_events_queue)
        if new_state:
            self.change_state(new_state)