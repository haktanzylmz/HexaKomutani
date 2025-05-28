# src/game_core/map.py
from .tile import Tile


# UnitFactory'i veya Unit'i doğrudan import etmeye gerek yok, Game sınıfı yönetecek

class Map:
    def __init__(self, rows, cols, tile_size):
        self.rows = rows
        self.cols = cols
        self.tile_size = tile_size
        self.grid = []  # Hücreleri (Tile nesneleri) tutacak 2D liste
        self.units = []  # Oyundaki tüm birimleri tutacak liste
        self.create_grid()

    def create_grid(self):
        self.grid = []  # Yeniden oluştururken listeyi temizle
        for row_idx in range(self.rows):
            self.grid.append([])
            for col_idx in range(self.cols):
                tile = Tile(col_idx, row_idx, self.tile_size)
                self.grid[row_idx].append(tile)

    def get_tile_at_grid_coords(self, grid_x, grid_y):
        if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
            return self.grid[grid_y][grid_x]
        return None

    def get_tile_from_pixel_coords(self, pixel_x, pixel_y):
        if pixel_x < 0 or pixel_x > self.cols * self.tile_size or \
                pixel_y < 0 or pixel_y > self.rows * self.tile_size:
            return None
        grid_x = pixel_x // self.tile_size
        grid_y = pixel_y // self.tile_size
        return self.get_tile_at_grid_coords(grid_x, grid_y)

    def add_unit(self, unit, grid_x, grid_y):
        tile = self.get_tile_at_grid_coords(grid_x, grid_y)
        if tile and tile.is_walkable and not tile.unit_on_tile:
            tile.set_unit(unit)
            unit.grid_x = grid_x
            unit.grid_y = grid_y
            self.units.append(unit)
            return True
        return False

    def move_unit(self, unit, new_grid_x, new_grid_y):
        old_tile = self.get_tile_at_grid_coords(unit.grid_x, unit.grid_y)
        new_tile = self.get_tile_at_grid_coords(new_grid_x, new_grid_y)

        if new_tile and new_tile.is_walkable and not new_tile.unit_on_tile:
            if old_tile:
                old_tile.remove_unit()

            new_tile.set_unit(unit)
            unit.grid_x = new_grid_x
            unit.grid_y = new_grid_y
            return True
        return False

    def draw(self, surface):
        # Önce haritayı çiz
        for row in self.grid:
            for tile in row:
                tile.draw(surface)

        # Sonra birimleri çiz (haritanın üzerine)
        for unit in self.units:
            unit.draw(surface)