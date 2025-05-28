# src/game_core/tile.py
import pygame


class Tile:
    def __init__(self, x_grid, y_grid, size, color=(200, 200, 200), is_walkable=True):
        self.x_grid = x_grid
        self.y_grid = y_grid
        self.size = size  # Tile'ın boyutu (piksel)
        self.color = color
        self.is_walkable = is_walkable
        self.unit_on_tile = None

        self.pixel_x = self.x_grid * self.size
        self.pixel_y = self.y_grid * self.size
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface):
        current_color = self.color
        if self.unit_on_tile and self.unit_on_tile.is_graphically_selected:
            pass
        elif not self.is_walkable:
            current_color = (50, 50, 50)

        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)

    def set_unit(self, unit):
        self.unit_on_tile = unit
        # Birimin pixel pozisyonu Game.load_game veya Map.add_unit içinde ayarlanacak
        # if unit:
        #     unit.set_pixel_pos(self.pixel_x, self.pixel_y, self.size) # Bu satır burada olmamalı, çift ayar yapar

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
    def from_dict(cls, data, tile_size):  # tile_size parametresini alacak
        """Sözlükten Tile nesnesi oluşturur."""
        # Tile'ın boyutu (tile_size) map yüklenirken bilinmeli ve buraya iletilmeli.
        # Renk gibi diğer varsayılanlar __init__ içinde ayarlanır.
        return cls(data["x_grid"],
                   data["y_grid"],
                   tile_size,  # Map'ten gelen tile_size kullanılacak
                   is_walkable=data["is_walkable"])

    def __str__(self):
        return f"Tile ({self.x_grid}, {self.y_grid}) - Unit: {self.unit_on_tile.unit_type if self.unit_on_tile else 'None'}"