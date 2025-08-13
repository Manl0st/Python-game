import pygame
from pygame.math import Vector2
from collections import deque
from state import State
from components import DashComponent, TensionBowstringComponent
from constants import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .world_objects import Wall

class PlayerIdleState(State['Player']):
    def __init__(self, player):
        super().__init__(player)
        
    def enter(self):
        self.context.velocity = Vector2(0, 0)
    
    def handle_input(self, input_state : dict, current_time : int, game_events_queue : deque):
        if input_state.get('key_button_W_hold') or input_state.get('key_button_A_hold') or \
           input_state.get('key_button_S_hold') or input_state.get('key_button_D_hold'):
            return PlayerMovingState(self.context)
        if input_state['mouse_button_left_pressed']:
            if self.context.bow_charge_component.try_tensioning(current_time):
                return PlayerChargingBowState(self.context)
        return None

class PlayerMovingState(State['Player']):
    def __init__(self, player : 'Player'):
        super().__init__(player)
        
    def enter(self):
        direction = self.context.current_input_movement_vector
        if direction.length_squared() > 0:
            self.context.velocity = direction * self.context.speed
        else:
            self.context.velocity = Vector2(0,0)
    
    def handle_input(self, input_state : dict, current_time : int, game_events_queue : deque):
        move_direction_vector : Vector2 = self.context.current_input_movement_vector
        if move_direction_vector.length_squared() == 0:
            return PlayerIdleState(self.context)
        if input_state.get('mouse_button_left_pressed'):
            if self.context.bow_charge_component.try_tensioning(current_time):
                return PlayerChargingBowState(self.context)
        if input_state.get('key_button_SPACE_pressed'):
            if self.context.dash_component.try_dashing(move_direction_vector, current_time):
                return PlayerDashingState(self.context)
        return None
            
    def update(self, current_time : int, game_events_queue : deque):
        move_direction_vector : Vector2 = self.context.current_input_movement_vector
        if move_direction_vector.length_squared() > 0:
            self.context.velocity = move_direction_vector * self.context.speed
        else:
            self.context.velocity = Vector2(0, 0)
        return None
        
class PlayerDashingState(State['Player']):
    def __init__(self, player : 'Player'):
        super().__init__(player)
        
    def enter(self):
        self.context.is_invincible = True
    
    def exit(self):
        self.context.is_invincible = False

    def update(self, current_time : int, game_events_queue : deque):
        player_dash = self.context.dash_component
        if player_dash.is_dashing:
            if current_time - player_dash.dash_start_time >= player_dash.dash_duration:
                player_dash.is_dashing = False
                player_dash.last_dash_end_time = current_time
                player_dash.current_dash_direction = Vector2(0, 0)
        self.context.velocity = player_dash.get_current_velocity()
        if not player_dash.is_active():
            move_direction_vector = self.context.current_input_movement_vector
            if move_direction_vector.length_squared() == 0:
                return PlayerIdleState(self.context)
            else:
                return PlayerMovingState(self.context)
        return None
    
class PlayerChargingBowState(State['Player']):
    def __init__(self, player : 'Player'):
        super().__init__(player)
        
    def enter(self):
        self.context.velocity /= 1.8
        
    def exit(self):
        self.context.velocity *= 1.8
        
    def handle_input(self, input_state : dict, current_time : int, game_events_queue : deque):
        move_direction_vector : Vector2 = self.context.current_input_movement_vector
        if input_state.get('key_button_SPACE_pressed'):
            if self.context.dash_component.try_dashing(move_direction_vector, current_time):
                self.context.bow_charge_component.cancel_tensioning_if_active()
                return PlayerDashingState(self.context)
        if input_state.get('mouse_button_left_released'):
            tension_factor = self.context.bow_charge_component.stop_and_get_factor(current_time)
            if tension_factor > 0.0 and input_state.get('mouse_pos_world') is not None:
                game_events_queue.append({
                    'type' : 'ARROW_SHOT',
                    'tension' : tension_factor,
                    'start_pos' : self.context.pos.copy(),
                    'target_pos' : input_state.get('mouse_pos_world'),
                    'speed' : ARROW_SPEED,
                    'damage' : ARROW_DAMAGE,
                    'state' : 'flight'
                })
            if move_direction_vector.length_squared() == 0:
                return PlayerIdleState(self.context)
            else:
                return PlayerMovingState(self.context)
        return None
    def update(self, current_time : int, game_events_queue : deque):
        move_direction_vector = self.context.current_input_movement_vector
        if move_direction_vector.length_squared() > 0:
            self.context.velocity = move_direction_vector.normalize() * (self.context.speed / 1.5)
        else:
            self.context.velocity = Vector2(0, 0)
        return None
    
class PlayerShootingState(State['Player']):
    pass
        
class PlayerDyingState(State['Player']):
    def __init__(self, player : 'Player'):
        super().__init__(player)
        
    def update(self, current_time : int, game_events_queue : deque):
        self.context.kill()
        return None
    
class Player(pygame.sprite.Sprite):
    def __init__(self, pos : Vector2, speed : int, width : int, height : int, health : int, dash_speed : int,
                 dash_duration : int, dash_cooldown : int, min_tension_duration : int, max_tension_duration : int):
        super().__init__()
        self.image = pygame.Surface([30, 30])
        self.image.fill("blue")
        self.rect = self.image.get_rect(center=pos)
        self.pos = pos
        self.speed = speed
        self.width = width
        self.height = height
        self.health = health
        self.is_invincible = False
        self.dash_speed = dash_speed
        self.dash_duration = dash_duration
        self.dash_cooldown = dash_cooldown
        self.min_tension_time = min_tension_duration
        self.max_tension_time = max_tension_duration
        self.dash_component : DashComponent = DashComponent(dash_duration, dash_cooldown, dash_speed)
        self.bow_charge_component : TensionBowstringComponent = TensionBowstringComponent(min_tension_duration, max_tension_duration)
        self.current_input_movement_vector = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        self.current_state_obj: State = PlayerIdleState(self)
        self.current_state_obj.enter()
        
    def change_state(self, new_state : State):
        if self.current_state_obj:
            self.current_state_obj.exit()
        self.current_state_obj = new_state
        self.current_state_obj.enter()
        
    def take_damage(self, damage : int):
        if not self.is_invincible:
            self.health -= damage
            if self.health <= 0:
                self.change_state(PlayerDyingState(self))
          
    def update(self, input_state : dict, game_events_queue : deque, current_time : int, walls : pygame.sprite.Group):
        self.current_input_movement_vector = Vector2(0,0)
        
        if input_state.get('key_button_W_hold'): self.current_input_movement_vector.y = -1
        if input_state.get('key_button_A_hold'): self.current_input_movement_vector.x = -1
        if input_state.get('key_button_S_hold'): self.current_input_movement_vector.y = 1
        if input_state.get('key_button_D_hold'): self.current_input_movement_vector.x = 1
        
        if self.current_input_movement_vector.length_squared():
            self.current_input_movement_vector.normalize_ip()
            
        new_state = self.current_state_obj.handle_input(input_state, current_time, game_events_queue)
        if new_state:
            self.change_state(new_state)
            
        new_state = self.current_state_obj.update(current_time, game_events_queue)
        if new_state:
            self.change_state(new_state)
            
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