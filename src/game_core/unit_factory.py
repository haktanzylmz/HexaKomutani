# src/game_core/unit_factory.py
from .unit import Piyade

class UnitFactory:
    @staticmethod
    def create_unit(unit_type, grid_x, grid_y, player_id): # player_id parametresi burada
        if unit_type == "Piyade":
            return Piyade(grid_x, grid_y, player_id) # player_id Piyade'ye yollanıyor
        # Örnek:
        # elif unit_type == "Tank":
        #     return Tank(grid_x, grid_y, player_id)
        else:
            print(f"Uyarı: Bilinmeyen birim tipi '{unit_type}'. Varsayılan olarak Piyade oluşturuluyor.")
            return Piyade(grid_x, grid_y, player_id) # Hata durumunda bile player_id'yi yolla