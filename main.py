import pygame
import random
from pygame.math import Vector2
from collections import deque
from player import Player
from enemy import Enemy
from arrow import Arrow
from world_objects import Wall
from camera import Camera
from constants import *

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.all_sprites = pygame.sprite.Group()
        self.walls_group = pygame.sprite.Group()
        self.arrows_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        
        player_start_pos = Vector2(80, 80)
        
        for ind_row, tile_row in enumerate(TILE_MAP):
            for ind_col, tile_char in enumerate(tile_row):
                world_x = ind_col * TILE_SIZE
                world_y = ind_row * TILE_SIZE
                if tile_char == "W":
                    wall = Wall(Vector2(world_x + TILE_SIZE / 2, world_y + TILE_SIZE / 2))
                    self.all_sprites.add(wall)
                    self.walls_group.add(wall)
                elif tile_char == "E":
                    enemy = Enemy(
                        Vector2(world_x + TILE_SIZE / 2, world_y + TILE_SIZE / 2), ENEMY_SPEED, ENEMY_HEALTH, ENEMY_SPRITE_WIDTH,
                        ENEMY_SPRITE_HEIGHT, SWORD_STRIKE_COOLDOWN, SWORD_STRIKE_DAMAGE, SWORD_STRIKE_RADIUS, SWORD_TIME_SWING,
                        SWORD_TIME_STRIKE, ENEMY_DETECTION_DISTANCE, self.all_sprites, None
                    )
                    self.all_sprites.add(enemy)
                    self.enemies_group.add(enemy)
                elif tile_char == "P":
                    player_start_pos = Vector2(world_x + TILE_SIZE / 2, world_y + TILE_SIZE / 2)

        self.player = Player(
            player_start_pos, PLAYER_SPEED, WIDTH, HEIGHT, PLAYER_HEALTH, PLAYER_DASH_SPEED,
            PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN, PLAYER_MIN_TENSION_DURATION, PLAYER_MAX_TENSION_DURATION
        )
        self.all_sprites.add(self.player)
        for enemy in self.enemies_group:
            enemy.player = self.player
            enemy.sword_component.purpose_strike = self.player
            
        self.camera = Camera(WIDTH, HEIGHT, MAP_WIDTH_PX, MAP_HEIGHT_PX)

        self.clock = pygame.time.Clock()
        self.game_events_queue = deque()
        self.running = True
        
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            current_time = pygame.time.get_ticks()
            input_state = {
                'quit_requested': False,
                'mouse_pos': Vector2(pygame.mouse.get_pos()),
                'mouse_pos_world' : self.camera.screen_to_world(Vector2(pygame.mouse.get_pos())),
                'mouse_button_left_hold' : pygame.mouse.get_pressed()[0],
                'mouse_button_left_pressed' : False,
                'mouse_button_left_released' : False,
                'key_button_W_hold' : pygame.key.get_pressed()[pygame.K_w],
                'key_button_A_hold' : pygame.key.get_pressed()[pygame.K_a],
                'key_button_S_hold' : pygame.key.get_pressed()[pygame.K_s],
                'key_button_D_hold' : pygame.key.get_pressed()[pygame.K_d],
                'key_button_SPACE_pressed' : False
            }
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    input_state['quit_requested'] = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        input_state['key_button_SPACE_pressed'] = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        input_state['mouse_button_left_pressed'] = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        input_state['mouse_button_left_released'] = True
            
            if input_state['quit_requested']:
                self.running = False
                continue
            
            self.player.update(input_state, self.game_events_queue, current_time, self.walls_group)
            for enemy_sprite in self.enemies_group:
                enemy_sprite.update(self.game_events_queue, current_time, self.walls_group)
            for arrow_sprite in self.arrows_group:
                arrow_sprite.update(self.game_events_queue, current_time)
            self.camera.update(self.player)
            
            while self.game_events_queue:
                event = self.game_events_queue.popleft()
                if event['type'] == 'ARROW_SHOT':
                    new_arrow = Arrow(event['tension'], event['start_pos'], event['target_pos'],
                                    event['speed'], event['damage'], event['state'], self.enemies_group,
                                    self.walls_group)
                    self.all_sprites.add(new_arrow)
                    self.arrows_group.add(new_arrow)
                if event['type'] == 'DEALING_DAMAGE':
                    for target in event['targets']:
                        target.take_damage(event['amount_damage'])
            
            if not self.player.alive():
                self.running = False
            
            self.screen.fill((30, 30, 30))
            for sprite_obj in self.all_sprites:
                self.screen.blit(sprite_obj.image, self.camera.apply_to_pos(sprite_obj.pos))
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()