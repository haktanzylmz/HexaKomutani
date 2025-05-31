# src/game_core/unit.py
import pygame
from .unit_states import IdleState  # __init__ içinde import ediliyor
from .constants import PLAYER_HUMAN_ID, PLAYER_AI_ID


class Unit:
    _id_counter = 0

    def __init__(self, grid_x, grid_y, unit_type, player_id, color=(128, 128, 128), size=30):  # Varsayılan renk gri
        self.id = Unit._id_counter
        Unit._id_counter += 1

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.unit_type = unit_type
        self.player_id = player_id
        self.base_color = color  # Artık Unit.draw içinde temadan alınacak birincil renk
        self.size = size
        self.pixel_x = 0
        self.pixel_y = 0
        self.rect = None
        self.is_graphically_selected = False
        self.has_acted_this_turn = False
        self.ai_strategy_instance = None

        # Varsayılan Savaş Değerleri (Alt sınıflar bunları ezecek)
        self.max_health = 100
        self.health = self.max_health
        self.attack_power = 10
        self.attack_range = 1
        self.min_attack_range = 1
        self.movement_range = 1

        # from .unit_states import IdleState # __init__ anında import yerine en üste alındı
        self.current_state_name = IdleState.__name__
        self.current_state = IdleState(self)
        if self.current_state:  # None değilse
            self.current_state.enter_state(game_instance=None)  # Unit __init__'te game_instance henüz yok

    def set_state(self, new_state_instance, game_instance=None):
        if self.current_state:
            self.current_state.exit_state(game_instance)
        self.current_state = new_state_instance
        if self.current_state:  # new_state_instance None değilse adını al
            self.current_state_name = new_state_instance.__class__.__name__
            self.current_state.enter_state(game_instance)
        else:  # Eğer new_state_instance None ise (bu olmamalı ama güvenlik için)
            self.current_state_name = "None"

    def handle_click(self, game_instance, clicked_tile):
        if self.current_state:
            self.current_state.handle_click(game_instance, clicked_tile)

    def update(self, dt):
        if self.current_state:
            self.current_state.update(dt)

    def set_pixel_pos(self, pixel_x, pixel_y, tile_size):
        offset = (tile_size - self.size) / 2
        self.pixel_x = pixel_x + offset;
        self.pixel_y = pixel_y + offset
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface, active_theme, font_small):
        if not self.is_alive() or not self.rect:
            return

        player_type_str = "human" if self.player_id == PLAYER_HUMAN_ID else "ai"
        unit_type_str = self.unit_type.lower()

        color_key = f"unit_{player_type_str}_{unit_type_str}_color"
        default_player_color_key = f"unit_player_{player_type_str}_default_color"  # Genel oyuncu rengi (Piyade, Tank için ayrı yoksa)
        fallback_color = self.base_color  # En son __init__'teki varsayılana düşer

        unit_theme_color = active_theme.get(color_key, active_theme.get(default_player_color_key, fallback_color))

        current_draw_color = unit_theme_color
        if self.has_acted_this_turn:
            dim_factor = 0.6
            current_draw_color = (int(unit_theme_color[0] * dim_factor),
                                  int(unit_theme_color[1] * dim_factor),
                                  int(unit_theme_color[2] * dim_factor))

        pygame.draw.rect(surface, current_draw_color, self.rect)

        health_bar_bg_color = active_theme.get("health_bar_bg", (150, 0, 0))
        health_bar_fg_color = active_theme.get("health_bar_fg", (0, 200, 0))
        if self.health < self.max_health:
            bar_width_ratio = self.health / self.max_health if self.max_health > 0 else 0
            bar_width = self.size * bar_width_ratio;
            bar_height = 5;
            bar_y_offset = 7
            background_bar_rect = pygame.Rect(self.pixel_x, self.pixel_y - bar_y_offset, self.size, bar_height)
            health_bar_rect_obj = pygame.Rect(self.pixel_x, self.pixel_y - bar_y_offset, bar_width, bar_height)
            pygame.draw.rect(surface, health_bar_bg_color, background_bar_rect)
            pygame.draw.rect(surface, health_bar_fg_color, health_bar_rect_obj)

        if self.is_graphically_selected:
            selected_border_color = active_theme.get("unit_selected_border_color", (255, 255, 0))
            pygame.draw.rect(surface, selected_border_color, self.rect, 3)

        label_text_color = active_theme.get("unit_label_text_color", (0, 0, 0))
        label_surf = font_small.render(self.unit_type, True, label_text_color)
        label_rect = label_surf.get_rect(center=(self.rect.centerx, self.rect.top - 6))
        if self.health < self.max_health and label_rect.bottom > (self.pixel_y - bar_y_offset - 2):
            label_rect.center = (self.rect.centerx, self.rect.bottom + 8)
        surface.blit(label_surf, label_rect)

    def get_tiles_in_movement_range(self, game_map):  # !!! BU METODUN TANIMI !!!
        in_range_tiles = []
        if not self.is_alive() or self.has_acted_this_turn: return in_range_tiles
        for r_offset in range(-self.movement_range, self.movement_range + 1):
            for c_offset in range(-self.movement_range, self.movement_range + 1):
                # Manhattan mesafesi
                distance = abs(r_offset) + abs(c_offset)
                if distance == 0 or distance > self.movement_range:  # Kendisi veya menzil dışı
                    continue

                check_x = self.grid_x + c_offset
                check_y = self.grid_y + r_offset

                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.is_walkable and not tile.unit_on_tile:
                    in_range_tiles.append(tile)
        return in_range_tiles

    def get_tiles_in_attack_range(self, game_map):  # !!! BU METODUN TANIMI (min_attack_range KULLANILIYOR) !!!
        in_range_attack_tiles = []  # Sadece saldırılabilecek düşmanların olduğu tile'ları tutar
        if not self.is_alive() or self.has_acted_this_turn: return in_range_attack_tiles

        for r_offset in range(-self.attack_range, self.attack_range + 1):
            for c_offset in range(-self.attack_range, self.attack_range + 1):
                if r_offset == 0 and c_offset == 0: continue

                distance = abs(r_offset) + abs(c_offset)

                if not (self.min_attack_range <= distance <= self.attack_range):
                    continue

                check_x = self.grid_x + c_offset
                check_y = self.grid_y + r_offset

                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.unit_on_tile and tile.unit_on_tile.is_alive() and tile.unit_on_tile.player_id != self.player_id:
                    in_range_attack_tiles.append(tile)
        return in_range_attack_tiles

    def take_damage(self, amount):
        self.health -= amount
        print(f"P{self.player_id} {self.unit_type}(ID:{self.id}) took {amount} dmg, HP:{self.health}")
        if self.health <= 0: self.health = 0; self.die()

    def is_alive(self):
        return self.health > 0

    def die(self):
        print(f"P{self.player_id} {self.unit_type}(ID:{self.id}) at ({self.grid_x},{self.grid_y}) died!")

    def to_dict(self):
        return {"id": self.id, "unit_type": self.unit_type, "player_id": self.player_id,
                "grid_x": self.grid_x, "grid_y": self.grid_y, "health": self.health,
                "max_health": self.max_health, "attack_power": self.attack_power,
                "movement_range": self.movement_range, "attack_range": self.attack_range,
                "min_attack_range": self.min_attack_range,  # min_attack_range eklendi
                "current_state_name": self.current_state_name, "has_acted_this_turn": self.has_acted_this_turn}

    def __str__(self):
        return f"ID:{self.id} P{self.player_id} {self.unit_type}({self.health}HP) Acted:{self.has_acted_this_turn} at ({self.grid_x},{self.grid_y}) St:{self.current_state_name}"


class Piyade(Unit):
    def __init__(self, grid_x, grid_y, player_id):
        # Renk ve size Unit.draw ve tema tarafından yönetilecek, buradaki color geçici
        super().__init__(grid_x, grid_y, "Piyade", player_id, color=(0, 0, 0), size=28)
        self.max_health = 100;
        self.health = self.max_health
        self.attack_power = 30;
        self.movement_range = 3
        self.attack_range = 1;
        self.min_attack_range = 1


class Tank(Unit):
    def __init__(self, grid_x, grid_y, player_id):
        super().__init__(grid_x, grid_y, "Tank", player_id, color=(0, 0, 0), size=32)
        self.max_health = 180;
        self.health = self.max_health
        self.attack_power = 45;
        self.movement_range = 2
        self.attack_range = 1;
        self.min_attack_range = 1


class Topcu(Unit):
    def __init__(self, grid_x, grid_y, player_id):
        super().__init__(grid_x, grid_y, "Topcu", player_id, color=(0, 0, 0), size=26)
        self.max_health = 70;
        self.health = self.max_health
        self.attack_power = 60;
        self.movement_range = 1
        self.attack_range = 5;
        self.min_attack_range = 2  # Bitişiğindekine saldıramaz