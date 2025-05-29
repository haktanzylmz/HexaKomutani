# src/game_core/tile.py
import pygame


class Tile:
    def __init__(self, x_grid, y_grid, size, color=(200, 200, 200), is_walkable=True):
        self.x_grid = x_grid
        self.y_grid = y_grid
        self.size = size
        self.base_color = color  # Temadan bağımsız varsayılan renk (artık pek kullanılmayacak)
        self.is_walkable = is_walkable
        self.unit_on_tile = None

        self.pixel_x = self.x_grid * self.size
        self.pixel_y = self.y_grid * self.size
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface, active_theme):  # !!! active_theme parametresi eklendi !!!
        # Tema renklerini al, eğer temada yoksa varsayılan renkleri kullan
        default_walkable_color = active_theme.get("tile_walkable_default_color", (200, 200, 200))
        obstacle_color = active_theme.get("tile_obstacle_color",
                                          (50, 50, 50))  # "tile_obstacle" idi, "tile_obstacle_color" daha iyi
        border_color = active_theme.get("tile_border_color", (0, 0, 0))

        current_fill_color = default_walkable_color
        if not self.is_walkable:
            current_fill_color = obstacle_color

        # Eğer üzerinde seçili bir birim varsa, tile'ı farklı çizme (birim kendi vurgusunu yapar)
        # Bu kontrol artık gereksiz, çünkü vurgular Tile'dan bağımsız Game.render_gameplay'de çiziliyor.
        # if self.unit_on_tile and self.unit_on_tile.is_graphically_selected:
        #     pass # Özel bir şey yapma, birim kendini çizecek

        pygame.draw.rect(surface, current_fill_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)

    def set_unit(self, unit):
        self.unit_on_tile = unit
        # Pixel pos ayarı Map.add_unit veya Map.move_unit içinde yapılmalı
        # if unit:
        #     unit.set_pixel_pos(self.pixel_x, self.pixel_y, self.size)

    def remove_unit(self):
        self.unit_on_tile = None

    def to_dict(self):
        tile_data = {
            "x_grid": self.x_grid,
            "y_grid": self.y_grid,
            "is_walkable": self.is_walkable,
        }
        return tile_data

    @classmethod
    def from_dict(cls, data, tile_size):
        return cls(data["x_grid"], data["y_grid"], tile_size,
                   is_walkable=data["is_walkable"])

    def __str__(self):
        return f"Tile ({self.x_grid}, {self.y_grid}) - Unit: {self.unit_on_tile.unit_type if self.unit_on_tile else 'None'}"