# src/game_core/map.py
from .tile import Tile


# Unit sınıfını import etmeye gerek yok, unit verilerini Game sınıfı yönetecek

class Map:
    def __init__(self, rows, cols, tile_size):
        self.rows = rows
        self.cols = cols
        self.tile_size = tile_size
        self.grid = []  # Hücreleri (Tile nesneleri) tutacak 2D liste
        self.units = []  # Oyundaki tüm birimleri tutacak liste (Game sınıfı da bir kopyasını tutabilir)
        # self.create_grid() # __init__ içinde create_grid çağrısı yerine Game.load_game'de çağrılabilir

    def create_grid(self):  # Bu metot artık sadece boş grid oluşturuyor
        self.grid = []
        for row_idx in range(self.rows):
            self.grid.append([])
            for col_idx in range(self.cols):
                # Tile'lar yüklenirken özellikleriyle (is_walkable vb.) oluşturulacak
                # Şimdilik varsayılan Tile oluşturuyoruz, load_map bunu override edecek.
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

    def add_unit(self, unit, grid_x, grid_y):  # Bu metot Game tarafından kullanılacak
        tile = self.get_tile_at_grid_coords(grid_x, grid_y)
        if tile and tile.is_walkable and not tile.unit_on_tile:
            tile.set_unit(unit)  # Bu, unit'in tile referansını ayarlar
            unit.grid_x = grid_x  # Birimin kendi grid bilgisini de güncelle
            unit.grid_y = grid_y
            unit.set_pixel_pos(tile.pixel_x, tile.pixel_y, self.tile_size)

            # Birimin haritanın ana birim listesinde olduğundan emin ol
            if unit not in self.units:
                self.units.append(unit)
            return True
        print(
            f"Cannot add unit {unit.id} to ({grid_x},{grid_y}). Tile: {tile}, Walkable: {tile.is_walkable if tile else 'N/A'}, Occupied: {tile.unit_on_tile if tile else 'N/A'}")
        return False

    def move_unit(self, unit, new_grid_x, new_grid_y):
        if not unit.is_alive(): return False

        old_tile = self.get_tile_at_grid_coords(unit.grid_x, unit.grid_y)
        new_tile = self.get_tile_at_grid_coords(new_grid_x, new_grid_y)

        if new_tile and new_tile.is_walkable and (not new_tile.unit_on_tile or new_tile.unit_on_tile == unit):
            if old_tile and old_tile.unit_on_tile == unit:
                old_tile.remove_unit()

            new_tile.set_unit(unit)
            unit.grid_x = new_grid_x
            unit.grid_y = new_grid_y
            unit.set_pixel_pos(new_tile.pixel_x, new_tile.pixel_y, self.tile_size)  # Pixel pos güncelle
            return True
        return False

    def remove_unit_from_map(self, unit_to_remove):
        # Birimi ana listeden çıkar
        if unit_to_remove in self.units:
            self.units.remove(unit_to_remove)

        # Birimin bulunduğu tile'dan da kaldır
        tile = self.get_tile_at_grid_coords(unit_to_remove.grid_x, unit_to_remove.grid_y)
        if tile and tile.unit_on_tile == unit_to_remove:
            tile.remove_unit()
        print(f"Unit ID {unit_to_remove.id} ({unit_to_remove.unit_type}) removed from map.")

    def draw(self, surface):
        for row_idx in range(self.rows):
            for col_idx in range(self.cols):
                tile = self.get_tile_at_grid_coords(col_idx, row_idx)
                if tile:  # Emin olmak için
                    tile.draw(surface)

        for unit in self.units:  # self.units listesi güncel olmalı
            if unit.is_alive():
                unit.draw(surface)

    def to_dict(self):
        """Map nesnesini kaydetmek için sözlük formatına çevirir."""
        map_data = {
            "rows": self.rows,
            "cols": self.cols,
            "tile_size": self.tile_size,
            "grid_tiles": [[tile.to_dict() for tile in row] for row in self.grid],
            # Birimleri burada kaydetmiyoruz, Game sınıfı tüm birimleri ayrıca kaydedecek.
            # Çünkü birimler haritadan bağımsız da var olabilir (örn: kenarda bekleyen birimler).
            # Harita sadece hangi tile'da hangi birim ID'sinin olduğunu bilse yeterli olabilir.
            # Ya da Game sınıfı, birimlerin listesini ve konumlarını kaydeder, yüklerken haritaya yerleştirir.
            # Şimdilik en temizi, Game'in birim listesini ve map'in tile listesini ayrı ayrı kaydetmesi.
        }
        return map_data

    # from_dict metodu Game.load_game içinde daha mantıklı olacak.
    # Orada önce boş bir Map oluşturulup, sonra tile'lar ve birimler yüklenecek.