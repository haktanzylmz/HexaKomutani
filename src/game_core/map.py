# src/game_core/map.py
from .tile import Tile # Aynı klasördeki tile.py'dan Tile sınıfını import et

class Map:
    def __init__(self, rows, cols, tile_size):
        self.rows = rows
        self.cols = cols
        self.tile_size = tile_size
        self.grid = [] # Hücreleri tutacak 2D liste
        self.create_grid()

    def create_grid(self):
        for row in range(self.rows):
            self.grid.append([])
            for col in range(self.cols):
                # Şimdilik basit kare hücreler için x, y doğrudan col, row olabilir
                tile = Tile(col, row, self.tile_size)
                self.grid[row].append(tile)

    def draw(self, surface):
        for row in self.grid:
            for tile in row:
                tile.draw(surface)