# src/game_core/unit.py
import pygame
from .unit_states import IdleState


class Unit:
    def __init__(self, grid_x, grid_y, unit_type, color=(0, 0, 255), size=30):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.unit_type = unit_type
        self.color = color
        self.size = size
        self.pixel_x = 0
        self.pixel_y = 0
        self.rect = None
        self.is_graphically_selected = False
        self.movement_range = 0  # Varsayılan menzil, alt sınıflar belirleyecek

        self.current_state = IdleState(self)
        self.current_state.enter_state()

    def set_state(self, new_state):
        if self.current_state:
            self.current_state.exit_state()
        self.current_state = new_state
        self.current_state.enter_state()

    def handle_click(self, game_instance, clicked_tile):
        self.current_state.handle_click(game_instance, clicked_tile)

    def update(self, dt):
        self.current_state.update(dt)

    def set_pixel_pos(self, pixel_x, pixel_y, tile_size):
        offset = (tile_size - self.size) / 2
        self.pixel_x = pixel_x + offset
        self.pixel_y = pixel_y + offset
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface):
        if self.rect:
            current_color = self.color
            pygame.draw.rect(surface, current_color, self.rect)
            if self.is_graphically_selected:
                pygame.draw.rect(surface, (255, 255, 0), self.rect, 3)

    def get_tiles_in_movement_range(self, game_map):
        """
        Basit Manhattan mesafesine göre hareket menzilindeki tile'ları döndürür.
        Engelleri veya diğer birimleri şimdilik dikkate almaz.
        Daha gelişmiş pathfinding algoritmaları (A*, Dijkstra) kullanılabilir.
        """
        in_range_tiles = []
        for r_offset in range(-self.movement_range, self.movement_range + 1):
            for c_offset in range(-self.movement_range, self.movement_range + 1):
                # Manhattan mesafesi
                if abs(r_offset) + abs(c_offset) > self.movement_range:
                    continue

                check_x = self.grid_x + c_offset
                check_y = self.grid_y + r_offset

                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.is_walkable and not tile.unit_on_tile:  # Sadece boş ve yürünebilir tile'lar
                    in_range_tiles.append(tile)
        return in_range_tiles

    def __str__(self):
        return f"{self.unit_type} at ({self.grid_x}, {self.grid_y}) in state {self.current_state.__class__.__name__}"


class Piyade(Unit):
    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y, "Piyade", color=(50, 150, 50))
        self.health = 100
        self.attack = 10
        self.movement_range = 3  # Piyade'nin hareket menzili