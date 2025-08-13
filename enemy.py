import pygame
from pygame.math import Vector2
from collections import deque
from state import State
from components import SwordComponent
from BFS import finding_a_way
from constants import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
     from .player import Player
     from .world_objects import Wall

class EnemyIdleState(State['Enemy']):
    def __init__(self, enemy : 'Enemy'):
        super().__init__(enemy)
        
    def enter(self):
        self.context.velocity = Vector2(0, 0)
        
    def update(self, current_time : int, game_events_queue : deque):
        if self.context.pos.distance_to(self.context.player.pos) <= self.context.detection_distance:
            return EnemyAttackingState(self.context)
        return None
        
class EnemyAttackingState(State['Enemy']):
    def __init__(self, enemy: 'Enemy'):
        super().__init__(enemy)

    def enter(self):
        self.recalc_interval = 1000 
        self.last_recalc_time = 0
        self.recalculate_path(pygame.time.get_ticks())

    def recalculate_path(self, current_time: int):
        self.last_recalc_time = current_time
        start_pos = Vector2(self.context.pos.x, self.context.pos.y)
        end_pos = Vector2(self.context.player.pos.x, self.context.player.pos.y)
        self.path = finding_a_way(start_pos, end_pos)

    def update(self, current_time: int, game_events_queue: deque):
        if not self.path or current_time - self.last_recalc_time > self.recalc_interval:
            self.recalculate_path(current_time)
        if self.path:
            finishing_pixel_pos = Vector2(self.path[0][1] * TILE_SIZE + TILE_SIZE / 2, 
                                       self.path[0][0] * TILE_SIZE + TILE_SIZE / 2)
            if self.context.pos.distance_to(finishing_pixel_pos) < self.context.speed * 0.5:
                self.path.popleft()
                if self.path:
                    finishing_pixel_pos = Vector2(self.path[0][1] * TILE_SIZE + TILE_SIZE / 2, 
                                               self.path[0][0] * TILE_SIZE + TILE_SIZE / 2)
            if self.context.pos.distance_to(finishing_pixel_pos) > 0:
                move_direction = (finishing_pixel_pos - self.context.pos).normalize()
            else:
                move_direction = Vector2(0, 0)
        else:
            move_direction = Vector2(0, 0)
        self.context.velocity = move_direction * self.context.speed
        if self.context.pos.distance_to(self.context.player.pos) <= self.context.sword_strike_radius:
            self.context.sword_component.start_swing(current_time)
        return None
            
class EnemyDyingState(State['Enemy']):
    def __init__(self, enemy : 'Enemy'):
        super().__init__(enemy)
        
    def update(self, current_time : int, game_events_queue : deque):
        self.context.kill()
        self.context.sword_component.kill()
        return None
            
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos : Vector2, speed : int, health : int, width : int, height : int, sword_strike_cooldown : int,
                sword_strike_damage : int, sword_strike_radius : int, sword_time_swing : int, sword_time_strike : int, 
                detection_distance, all_sprites : pygame.sprite.Group, player : 'Player'):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill("red")
        self.rect = self.image.get_rect(center=pos)
        self.pos = pos
        self.speed = speed
        self.health = health
        self.velocity = Vector2(0, 0)
        self.detection_distance = detection_distance
        self.player = player
        self.sword_strike_cooldown = sword_strike_cooldown
        self.sword_strike_damage = sword_strike_damage
        self.sword_strike_radius = sword_strike_radius
        self.sword_time_swing = sword_time_swing
        self.sword_time_strike = sword_time_strike
        self.sword_component = SwordComponent(sword_strike_cooldown, sword_strike_damage,
                                              sword_strike_radius, sword_time_swing, sword_time_strike, self, player)
        all_sprites.add(self.sword_component)
        self.current_state_obj = EnemyIdleState(self)
        self.current_state_obj.enter()
        
    def change_state(self, new_state : State):
        if self.current_state_obj:
            self.current_state_obj.exit()
        self.current_state_obj = new_state
        self.current_state_obj.enter()
        
    def take_damage(self, damage : int):
        self.health -= damage
        if self.health <= 0:
            self.change_state(EnemyDyingState(self))
                
    def update(self, game_events_queue : deque, current_time : int, walls : pygame.sprite.Group):
        new_state = self.current_state_obj.update(current_time, game_events_queue)
        if new_state:
            self.change_state(new_state)
        
        self.sword_component.update(game_events_queue, current_time)
            
        self.pos.x += self.velocity.x
        self.rect.centerx = self.pos.x
        
        x_collisions : list['Wall'] = pygame.sprite.spritecollide(self, walls, False)
        for wall_hit in x_collisions:
            if self.velocity.x > 0:
                self.rect.right = wall_hit.rect.left
            elif self.velocity.x < 0:
                self.rect.left = wall_hit.rect.right
            self.pos.x = self.rect.centerx
            self.velocity.x = 0
            
        self.pos.y += self.velocity.y
        self.rect.centery = self.pos.y
            
        y_collisions : list['Wall'] = pygame.sprite.spritecollide(self, walls, False)
        for wall_hit in y_collisions:
            if self.velocity.y > 0:
                self.rect.bottom = wall_hit.rect.top
            elif self.velocity.y < 0:
                self.rect.top = wall_hit.rect.bottom
            self.pos.y = self.rect.centery
            self.velocity.y = 0