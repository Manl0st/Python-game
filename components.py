import pygame
from pygame.math import Vector2
from state import State
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .enemy import Enemy
    from .player import Player

class DashComponent:
    def __init__(self, dash_duration : int, dash_cooldown : int, dash_speed : int):
        self.dash_duration = dash_duration
        self.dash_cooldown = dash_cooldown
        self.dash_start_time = 0
        self.last_dash_end_time = -dash_cooldown
        self.is_dashing = False
        self.current_dash_direction = Vector2(0, 0)
        self.dash_speed = dash_speed
        
    def get_current_velocity(self):
        if self.is_dashing:
            return self.current_dash_direction * self.dash_speed
        else:
            return Vector2(0, 0)
        
    def is_active(self):
        return self.is_dashing
        
    def try_dashing(self, direction : Vector2, current_time : int):
        if not self.is_dashing and current_time - self.last_dash_end_time >= self.dash_cooldown:
            self.is_dashing = True
            self.dash_start_time = current_time
            self.current_dash_direction = direction.normalize()
            return True
        return False
    
class TensionBowstringComponent:
    def __init__(self, min_tension_duration, max_tension_duration):
        self.min_tension_duration = min_tension_duration
        self.max_tension_duration = max_tension_duration
        self._is_tensioning = False
        self._tension_start_time = 0

    def try_tensioning(self, current_time : int):
        if not self._is_tensioning:
            self._is_tensioning = True
            self._tension_start_time = current_time
            return True
        return False

    def stop_and_get_factor(self, current_time : int):
        if self._is_tensioning:
            self._is_tensioning = False
            hold_duration = current_time - self._tension_start_time
            if hold_duration < self.min_tension_duration:
                return 0.0
            clamped_duration = min(hold_duration, self.max_tension_duration)
            duration_range = self.max_tension_duration - self.min_tension_duration
            if duration_range > 0:
                normalized_progress = (clamped_duration - self.min_tension_duration) / duration_range
                tension_factor = 1.0 + normalized_progress * (2.0 - 1.0)
            else:
                if hold_duration >= self.min_tension_duration:
                    tension_factor = 1.0
                else:
                    tension_factor = 0.0
            return tension_factor
        return 0.0

    def cancel_tensioning_if_active(self):
        if self._is_tensioning:
            self._is_tensioning = False

    def is_tensioning(self):
        return self._is_tensioning

    def get_current_tension_factor(self, current_time : int):
        if self._is_tensioning:
            hold_duration = current_time - self._tension_start_time
            duration_range = self.max_tension_duration - self.min_tension_duration
            if duration_range > 0:
                normalized_progress = (hold_duration - self.min_tension_duration) / duration_range
                tension_factor = 1.0 + max(0.0, normalized_progress) * (2.0 - 1.0)
                return tension_factor
            else:
                if hold_duration >= self.min_tension_duration:
                    return 1.0
                else:
                    return 0.0
        return 0.0
    
class SwordComponent(pygame.sprite.Sprite):
    def __init__(self, sword_strike_cooldown : int, sword_strike_damage : int, sword_strike_radius : int,
                 sword_time_swing : int, sword_time_strike : int, owner_sword : 'Enemy', purpose_strike : 'Player'):
        super().__init__()
        self.sword_strike_cooldown = sword_strike_cooldown
        self.sword_strike_damage = sword_strike_damage
        self.sword_strike_radius = sword_strike_radius
        self.sword_time_swing = sword_time_swing
        self.sword_time_strike = sword_time_strike
        self.sword_last_time_strike = 0
        self.sword_is_strike = False
        self.sword_is_touch = False
        self.pos = owner_sword.pos
        self.owner_sword = owner_sword
        self.purpose_strike = purpose_strike
        self.image = pygame.Surface([30, 30])
        self.image.fill("green")
        self.rect = self.image.get_rect(center=self.owner_sword.pos)
        self.current_state_obj = SwordIdleState(self)
        self.current_state_obj.enter()
        
    def change_state(self, new_state : State):
        if self.current_state_obj:
            self.current_state_obj.exit()
        self.current_state_obj = new_state
        self.current_state_obj.enter()
        
    def try_swing(self, current_time : int):
        if not self.sword_is_strike and current_time - self.sword_last_time_strike >= \
            self.sword_time_swing + self.sword_time_strike + self.sword_strike_cooldown:
                self.sword_is_strike = True
                self.sword_last_time_strike = current_time
                return True
        return False
    
    def try_strike(self, current_time : int):
        if current_time - self.sword_last_time_strike >= self.sword_time_swing:
            return True
        return False
    
    def try_cooldown(self, current_time : int):
        if current_time - self.sword_last_time_strike >= \
            self.sword_time_swing + self.sword_time_strike:
                self.sword_is_strike = False
                return True
        return False
    
    def try_idle(self, current_time : int):
        if current_time - self.sword_last_time_strike >= \
            self.sword_time_swing + self.sword_time_strike + self.sword_strike_cooldown:
                return True
        return False
    
    def start_swing(self, current_time : int):
        if isinstance(self.current_state_obj, SwordIdleState):
            if self.try_swing(current_time):
                self.change_state(SwordStrikeState(self))
                return True
        return False
                
    def update(self, game_events_queue : deque, current_time : int):
        self.rect.center = self.owner_sword.pos
        new_state = self.current_state_obj.update(current_time, game_events_queue)
        if new_state:
            self.change_state(new_state)
    
class SwordIdleState(State['SwordComponent']):
    def __init__(self, swordcomponent : 'SwordComponent'):
        super().__init__(swordcomponent)
                
class SwordSwingState(State['SwordComponent']):
    def __init__(self, swordcomponent : 'SwordComponent'):
        super().__init__(swordcomponent)
        
    def update(self, current_time : int, game_events_queue : deque):
        if self.context.try_strike(current_time):
            return SwordStrikeState(self.context)
        return None
        
class SwordStrikeState(State['SwordComponent']):
    def __init__(self, swordcomponent : 'SwordComponent'):
        super().__init__(swordcomponent)
        
    def update(self, current_time : int, game_events_queue : deque):
        if not self.context.sword_is_touch:
            direction = Vector2(0, 0)
            if (self.context.purpose_strike.pos - self.context.owner_sword.pos).length_squared():
                direction = Vector2(self.context.purpose_strike.pos - self.context.owner_sword.pos).normalize()
            self.context.rect.center = direction * self.context.sword_strike_radius + self.context.owner_sword.pos
            if self.context.purpose_strike.rect.colliderect(self.context.rect):
                self.context.sword_is_touch = True
                game_events_queue.append({
                    'type' : 'DEALING_DAMAGE',
                    'from_what' : 'sword',
                    'targets' : [self.context.purpose_strike],
                    'amount_damage' : self.context.sword_strike_damage
                })
        if self.context.try_cooldown(current_time):
            return SwordCooldownState(self.context)
        return None
        
class SwordCooldownState(State['SwordComponent']):
    def __init__(self, swordcomponent : 'SwordComponent'):
        super().__init__(swordcomponent)
        
    def enter(self):
        self.context.sword_is_touch = False
        
    def update(self, current_time : int, game_events_queue : deque):
        if self.context.try_idle(current_time):
            return SwordIdleState(self.context)
        return None