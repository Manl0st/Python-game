import pygame
from pygame.math import Vector2
from constants import *
from collections import deque

def finding_a_way(starting_pos : Vector2, finishing_pos : Vector2):
    starting_pos = (int(starting_pos.y // TILE_SIZE), int(starting_pos.x // TILE_SIZE))
    finishing_pos = (int(finishing_pos.y // TILE_SIZE), int(finishing_pos.x // TILE_SIZE))
    queue = deque([starting_pos])
    queue_visits = {starting_pos : None}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while queue:
        current_pos = queue.popleft()
        if current_pos == finishing_pos:
            return reconstruct_path(queue_visits, starting_pos, finishing_pos)
        for x, y in directions:
            neighbor_pos = (current_pos[0] + x, current_pos[1] + y)
            if 0 <= neighbor_pos[0] < MAP_HEIGHT_TILES and \
                0 <= neighbor_pos[1] < MAP_WIDTH_TILES:
                if TILE_MAP[neighbor_pos[0]][neighbor_pos[1]] != 'W' and neighbor_pos not in queue_visits:
                    queue.append(neighbor_pos)
                    queue_visits[neighbor_pos] = current_pos
    return deque()

def reconstruct_path(queue_visits: dict, starting_pos: tuple[int, int], finishing_pos: tuple[int, int]):
    current = finishing_pos
    path = []
    while current != starting_pos:
        if current not in queue_visits:
            return deque()
        path.append(current)
        current = queue_visits[current]
    return deque(path[::-1])