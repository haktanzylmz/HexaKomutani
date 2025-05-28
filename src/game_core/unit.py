# src/game_core/unit.py
import pygame
from .unit_states import IdleState


class Unit:
    def __init__(self, grid_x, grid_y, unit_type, player_id, color=(0, 0, 255), size=30):  # player_id eklendi
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.unit_type = unit_type
        self.player_id = player_id  # 1: Human, 2: AI gibi
        self.color = color
        self.size = size
        self.pixel_x = 0
        self.pixel_y = 0
        self.rect = None
        self.is_graphically_selected = False

        self.max_health = 100
        self.health = self.max_health
        self.attack_power = 10
        self.attack_range = 1
        self.movement_range = 0

        self.current_state = IdleState(self)
        # self.current_state.enter_state() # IdleState __init__'i içinde yapılabilir veya Unit __init__'te çağrılır

    def set_state(self, new_state):
        if self.current_state:
            self.current_state.exit_state()
        self.current_state = new_state
        self.current_state.enter_state()

    def handle_click(self, game_instance, clicked_tile):
        # Sadece mevcut oyuncunun birimleri tıklanabilir olmalı (Game sınıfında kontrol edilecek)
        self.current_state.handle_click(game_instance, clicked_tile)

    def update(self, dt):
        self.current_state.update(dt)

    def set_pixel_pos(self, pixel_x, pixel_y, tile_size):
        offset = (tile_size - self.size) / 2
        self.pixel_x = pixel_x + offset
        self.pixel_y = pixel_y + offset
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface):
        if not self.is_alive():
            return

        if self.rect:
            current_color = self.color
            pygame.draw.rect(surface, current_color, self.rect)

            if self.health < self.max_health:
                bar_width = self.size * (self.health / self.max_health)
                health_bar_rect = pygame.Rect(self.pixel_x, self.pixel_y - 7, self.size, 5)
                red_bar_rect = pygame.Rect(self.pixel_x, self.pixel_y - 7, bar_width, 5)
                pygame.draw.rect(surface, (255, 0, 0), health_bar_rect)
                pygame.draw.rect(surface, (0, 255, 0), red_bar_rect)

            if self.is_graphically_selected:
                pygame.draw.rect(surface, (255, 255, 0), self.rect, 3)

    def get_tiles_in_movement_range(self, game_map):
        in_range_tiles = []
        if not self.is_alive(): return in_range_tiles

        for r_offset in range(-self.movement_range, self.movement_range + 1):
            for c_offset in range(-self.movement_range, self.movement_range + 1):
                if abs(r_offset) + abs(c_offset) > self.movement_range:
                    continue

                check_x = self.grid_x + c_offset
                check_y = self.grid_y + r_offset

                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.is_walkable and not tile.unit_on_tile:
                    in_range_tiles.append(tile)
        return in_range_tiles

    def get_tiles_in_attack_range(self, game_map):
        in_range_attack_tiles = []  # Sadece tile'ları döndürsün
        if not self.is_alive(): return in_range_attack_tiles

        for r_offset in range(-self.attack_range, self.attack_range + 1):
            for c_offset in range(-self.attack_range, self.attack_range + 1):
                if r_offset == 0 and c_offset == 0:
                    continue

                distance = abs(r_offset) + abs(c_offset)
                if distance > self.attack_range:
                    continue

                check_x = self.grid_x + c_offset
                check_y = self.grid_y + r_offset

                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                # Sadece üzerinde DÜŞMAN birim olan tile'ları döndür.
                if tile and tile.unit_on_tile and tile.unit_on_tile.player_id != self.player_id:
                    in_range_attack_tiles.append(tile)
        return in_range_attack_tiles

    def take_damage(self, amount):
        self.health -= amount
        print(f"Player {self.player_id}'s {self.unit_type} took {amount} damage, health is now {self.health}")
        if self.health <= 0:
            self.health = 0
            self.die()

    def is_alive(self):
        return self.health > 0

    def die(self):
        print(f"Player {self.player_id}'s {self.unit_type} at ({self.grid_x}, {self.grid_y}) has died!")

    def __str__(self):
        return f"P{self.player_id} {self.unit_type} ({self.health}HP) at ({self.grid_x}, {self.grid_y}) in state {self.current_state.__class__.__name__}"


class Piyade(Unit):
    def __init__(self, grid_x, grid_y, player_id):  # player_id eklendi
        super().__init__(grid_x, grid_y, "Piyade", player_id,
                         color=(50, 150, 50) if player_id == 1 else (150, 50, 50))  # Renk oyuncuya göre
        self.max_health = 100
        self.health = self.max_health
        self.attack_power = 30  # Biraz arttıralım ki bir şeyler olsun :)
        self.movement_range = 3
        self.attack_range = 1