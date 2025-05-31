# src/game_core/map.py
from .tile import Tile


class Map:
    def __init__(self, rows, cols, tile_size):
        self.rows = rows
        self.cols = cols
        self.tile_size = tile_size
        self.grid = []
        self.units = []
        # self.create_grid() # Artık _initialize_game_for_level veya load_game içinde çağrılıyor

    def create_grid(self):
        self.grid = []
        for row_idx in range(self.rows):
            self.grid.append([])
            for col_idx in range(self.cols):
                # Tile'lar _initialize_game_for_level veya load_game'de temaya göre renk alacak
                tile = Tile(col_idx, row_idx, self.tile_size)
                self.grid[row_idx].append(tile)

    def get_tile_at_grid_coords(self, grid_x, grid_y):  # (Bir öncekiyle aynı)
        if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows: return self.grid[grid_y][grid_x]
        return None

    def get_tile_from_pixel_coords(self, pixel_x, pixel_y):  # (Bir öncekiyle aynı)
        if not (0 <= pixel_x < self.cols * self.tile_size and 0 <= pixel_y < self.rows * self.tile_size): return None
        return self.get_tile_at_grid_coords(pixel_x // self.tile_size, pixel_y // self.tile_size)

    def add_unit(self, unit, grid_x, grid_y):  # (Bir öncekiyle aynı)
        tile = self.get_tile_at_grid_coords(grid_x, grid_y)
        if tile and tile.is_walkable and not tile.unit_on_tile:
            tile.set_unit(unit);
            unit.grid_x = grid_x;
            unit.grid_y = grid_y
            unit.set_pixel_pos(tile.pixel_x, tile.pixel_y, self.tile_size)
            if unit not in self.units: self.units.append(unit)
            return True
        # print(f"Cannot add unit {unit.id if unit else 'N/A'} to ({grid_x},{grid_y}).")
        return False

    def move_unit(self, unit, new_grid_x, new_grid_y):  # (Bir öncekiyle aynı)
        if not unit.is_alive(): return False
        old_tile = self.get_tile_at_grid_coords(unit.grid_x, unit.grid_y)
        new_tile = self.get_tile_at_grid_coords(new_grid_x, new_grid_y)
        if new_tile and new_tile.is_walkable and (not new_tile.unit_on_tile or new_tile.unit_on_tile == unit):
            if old_tile and old_tile.unit_on_tile == unit: old_tile.remove_unit()
            new_tile.set_unit(unit);
            unit.grid_x = new_grid_x;
            unit.grid_y = new_grid_y
            unit.set_pixel_pos(new_tile.pixel_x, new_tile.pixel_y, self.tile_size)
            return True
        return False

    def remove_unit_from_map(self, unit_to_remove):  # (Bir öncekiyle aynı)
        if unit_to_remove in self.units: self.units.remove(unit_to_remove)
        tile = self.get_tile_at_grid_coords(unit_to_remove.grid_x, unit_to_remove.grid_y)
        if tile and tile.unit_on_tile == unit_to_remove: tile.remove_unit()
        print(f"Unit ID {unit_to_remove.id} ({unit_to_remove.unit_type}) removed from map.")

    def draw(self, surface, active_theme, font_small):  # !!! font_small parametresi eklendi !!!
        for row_idx in range(self.rows):
            for col_idx in range(self.cols):
                tile = self.get_tile_at_grid_coords(col_idx, row_idx)
                if tile:
                    tile.draw(surface, active_theme)

        for unit in self.units:
            if unit.is_alive():
                unit.draw(surface, active_theme, font_small)  # !!! font_small'u unit.draw'a yolla !!!

    def to_dict(self):  # (Bir öncekiyle aynı)
        return {"rows": self.rows, "cols": self.cols, "tile_size": self.tile_size,
                "grid_tiles": [[tile.to_dict() for tile in row] for row in self.grid]}