# src/game_core/tile.py
import pygame

class Tile:
    def __init__(self, x_grid, y_grid, size, color=(200, 200, 200)):
        self.x_grid = x_grid
        self.y_grid = y_grid
        self.size = size
        self.color = color
        self.is_walkable = True
        self.unit_on_tile = None

        self.pixel_x = self.x_grid * self.size
        self.pixel_y = self.y_grid * self.size
        self.rect = pygame.Rect(self.pixel_x, self.pixel_y, self.size, self.size)

    def draw(self, surface):
        current_color = self.color
        # Hata alınan satırı düzeltiyoruz:
        # Birimin seçili olup olmadığını 'is_graphically_selected' ile kontrol etmeliyiz.
        if self.unit_on_tile and self.unit_on_tile.is_graphically_selected:
            # Eğer hücrede seçili bir birim varsa, hücrenin özel bir renk almasını engelleyebiliriz
            # ya da birime göre farklı bir efekt verebiliriz. Şimdilik bir şey yapmayalım,
            # birim kendi seçili halini çizecek.
            pass
        elif not self.is_walkable:
            current_color = (50,50,50)

        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 1) # Kenarlık

    def set_unit(self, unit):
        self.unit_on_tile = unit
        if unit:
            unit.set_pixel_pos(self.pixel_x, self.pixel_y, self.size)

    def remove_unit(self):
        self.unit_on_tile = None

    def __str__(self):
        return f"Tile ({self.x_grid}, {self.y_grid}) - Unit: {self.unit_on_tile.unit_type if self.unit_on_tile else 'None'}"