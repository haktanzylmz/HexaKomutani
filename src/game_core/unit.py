# src/game_core/unit.py
import pygame
from .unit_states import IdleState
from .constants import PLAYER_HUMAN_ID, PLAYER_AI_ID


class Unit:
    _id_counter = 0

    def __init__(self, grid_x, grid_y, unit_type, player_id, color=(0, 0, 255), size=30):  # Renk artık temadan gelecek
        self.id = Unit._id_counter
        Unit._id_counter += 1
        self.grid_x = grid_x;
        self.grid_y = grid_y
        self.unit_type = unit_type;
        self.player_id = player_id
        self.base_color = color  # Temadan bağımsız varsayılan (artık pek kullanılmayacak)
        self.size = size
        self.pixel_x = 0;
        self.pixel_y = 0;
        self.rect = None
        self.is_graphically_selected = False;
        self.has_acted_this_turn = False
        self.max_health = 100;
        self.health = self.max_health
        self.attack_power = 10;
        self.attack_range = 1;
        self.movement_range = 0
        from .unit_states import IdleState # Döngüsel importu önlemek için burada
        self.current_state_name = IdleState.__name__
        self.current_state = IdleState(self)
        if self.current_state:  # None değilse
            self.current_state.enter_state(game_instance=None)


    def set_state(self, new_state_instance, game_instance=None):
        if self.current_state: self.current_state.exit_state(game_instance)
        self.current_state = new_state_instance
        self.current_state_name = new_state_instance.__class__.__name__
        if self.current_state: self.current_state.enter_state(game_instance)

    def handle_click(self, game_instance, clicked_tile):
        if self.current_state: self.current_state.handle_click(game_instance, clicked_tile)

    def update(self, dt):
        if self.current_state: self.current_state.update(dt)

    def set_pixel_pos(self, pixel_x, pixel_y, tile_size):
        offset = (tile_size - self.size) / 2
        self.pixel_x = pixel_x + offset;
        self.pixel_y = pixel_y + offset
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface, active_theme):
        if not self.is_alive() or not self.rect:
            return

        player_type_str = "human" if self.player_id == PLAYER_HUMAN_ID else "ai"
        unit_type_str = self.unit_type.lower()  # "Piyade" -> "piyade", "Tank" -> "tank"

        # Temadan birime özel renk anahtarını oluştur: örn. "unit_human_piyade_color"
        color_key = f"unit_{player_type_str}_{unit_type_str}_color"

        # Eğer birime özel renk yoksa, oyuncuya özel genel rengi al, o da yoksa varsayılanı al
        default_player_color_key = f"unit_player_{player_type_str}_default_color"
        fallback_color = (128, 128, 128)  # Genel bir varsayılan renk

        unit_base_color = active_theme.get(color_key, active_theme.get(default_player_color_key, fallback_color))

        current_draw_color = unit_base_color
        if self.has_acted_this_turn:
            dim_factor = 0.6
            current_draw_color = (int(unit_base_color[0] * dim_factor),
                                  int(unit_base_color[1] * dim_factor),
                                  int(unit_base_color[2] * dim_factor))

        pygame.draw.rect(surface, current_draw_color, self.rect)

        health_bar_bg_color = active_theme.get("health_bar_bg", (150, 0, 0))
        health_bar_fg_color = active_theme.get("health_bar_fg", (0, 200, 0))
        health_bar_selected_border_color = active_theme.get("unit_selected_border_color", (255, 255, 0))

        if self.health < self.max_health:
            bar_width_ratio = self.health / self.max_health if self.max_health > 0 else 0
            bar_width = self.size * bar_width_ratio
            bar_height = 5;
            bar_y_offset = 7
            background_bar_rect = pygame.Rect(self.pixel_x, self.pixel_y - bar_y_offset, self.size, bar_height)
            health_bar_rect_obj = pygame.Rect(self.pixel_x, self.pixel_y - bar_y_offset, bar_width, bar_height)
            pygame.draw.rect(surface, health_bar_bg_color, background_bar_rect)
            pygame.draw.rect(surface, health_bar_fg_color, health_bar_rect_obj)

        if self.is_graphically_selected:
            pygame.draw.rect(surface, health_bar_selected_border_color, self.rect, 3)

    def get_tiles_in_movement_range(self, game_map):  # (Bir öncekiyle aynı)
        in_range_tiles = []
        if not self.is_alive() or self.has_acted_this_turn: return in_range_tiles
        for r_offset in range(-self.movement_range, self.movement_range + 1):
            for c_offset in range(-self.movement_range, self.movement_range + 1):
                if abs(r_offset) + abs(c_offset) > self.movement_range: continue
                if abs(r_offset) + abs(c_offset) == 0: continue
                check_x = self.grid_x + c_offset;
                check_y = self.grid_y + r_offset
                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.is_walkable and not tile.unit_on_tile: in_range_tiles.append(tile)
        return in_range_tiles

    def get_tiles_in_attack_range(self, game_map):  # (Bir öncekiyle aynı)
        in_range_attack_tiles = []
        if not self.is_alive() or self.has_acted_this_turn: return in_range_attack_tiles
        for r_offset in range(-self.attack_range, self.attack_range + 1):
            for c_offset in range(-self.attack_range, self.attack_range + 1):
                if r_offset == 0 and c_offset == 0: continue
                distance = abs(r_offset) + abs(c_offset)
                if distance > self.attack_range: continue
                check_x = self.grid_x + c_offset;
                check_y = self.grid_y + r_offset
                tile = game_map.get_tile_at_grid_coords(check_x, check_y)
                if tile and tile.unit_on_tile and tile.unit_on_tile.player_id != self.player_id:
                    in_range_attack_tiles.append(tile)
        return in_range_attack_tiles

    def take_damage(self, amount):  # (Bir öncekiyle aynı)
        self.health -= amount
        print(
            f"Player {self.player_id}'s {self.unit_type} (ID:{self.id}) took {amount} damage, health is now {self.health}")
        if self.health <= 0: self.health = 0; self.die()

    def is_alive(self):
        return self.health > 0  # (Bir öncekiyle aynı)

    def die(self):
        print(
            f"Player {self.player_id}'s {self.unit_type} (ID:{self.id}) at ({self.grid_x}, {self.grid_y}) has died!")  # (Bir öncekiyle aynı)

    def to_dict(self):  # (Bir öncekiyle aynı)
        return {"id": self.id, "unit_type": self.unit_type, "player_id": self.player_id,
                "grid_x": self.grid_x, "grid_y": self.grid_y, "health": self.health,
                "max_health": self.max_health, "attack_power": self.attack_power,
                "movement_range": self.movement_range, "attack_range": self.attack_range,
                "current_state_name": self.current_state_name, "has_acted_this_turn": self.has_acted_this_turn}

    def __str__(self):
        return f"ID:{self.id} P{self.player_id} {self.unit_type} ({self.health}HP) Acted:{self.has_acted_this_turn} at ({self.grid_x}, {self.grid_y}) in state {self.current_state_name}"  # (Bir öncekiyle aynı)


class Piyade(Unit):
    def __init__(self, grid_x, grid_y, player_id):

        # from .constants import PLAYER_HUMAN_ID # Bu satır unit.py'nin en başında olmalı
        color = (50, 150, 50) if player_id == PLAYER_HUMAN_ID else (150, 50, 50)
        super().__init__(grid_x, grid_y, "Piyade", player_id, color=color, size=28)
        self.max_health = 100
        self.health = self.max_health
        self.attack_power = 30
        self.movement_range = 3
        self.attack_range = 1
        # self.has_acted_this_turn zaten Unit.__init__ içinde False olarak ayarlanıyor.
        # self.current_state ve self.current_state_name de Unit.__init__ içinde ayarlanıyor.


class Tank(Unit):
    def __init__(self, grid_x, grid_y, player_id):
        # Tank için farklı bir varsayılan renk (temadan da üzerine yazılabilir)
        # PLAYER_HUMAN_ID, unit.py'nin en başında constants.py'dan import edilmiş olmalı.
        color = (100, 100, 120) if player_id == PLAYER_HUMAN_ID else (120, 100, 100)

        # Tank'a özel daha büyük bir boyut (isteğe bağlı)
        unit_size = 34

        super().__init__(grid_x, grid_y, "Tank", player_id, color=color, size=unit_size)

        # Tank'a özel nitelikler
        self.max_health = 180  # Piyade'den (100) daha fazla can
        self.health = self.max_health
        self.attack_power = 45  # Piyade'den (30) daha fazla saldırı gücü
        self.movement_range = 2  # Piyade'den (3) daha az hareket menzili
        self.attack_range = 1  # Piyade gibi yakın dövüş (veya 2 yapıp uzak menzilli top olabilir)
        # self.has_acted_this_turn zaten Unit.__init__ içinde False olarak ayarlanıyor.
        # self.current_state ve self.current_state_name de Unit.__init__ içinde ayarlanıyor.