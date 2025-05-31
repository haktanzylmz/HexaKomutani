# src/game_core/unit_factory.py
from .unit import Piyade, Tank, Topcu
class UnitFactory:
    @staticmethod
    def create_unit(unit_type, grid_x, grid_y, player_id):
        if unit_type == "Piyade":
            return Piyade(grid_x, grid_y, player_id)
        elif unit_type == "Tank":
            return Tank(grid_x, grid_y, player_id)
        elif unit_type == "Topcu": # !!! YENİ BLOK !!!
            return Topcu(grid_x, grid_y, player_id)
        else:
            print(f"Uyarı: Bilinmeyen birim tipi '{unit_type}'. Varsayılan olarak Piyade oluşturuluyor.")
            return Piyade(grid_x, grid_y, player_id)