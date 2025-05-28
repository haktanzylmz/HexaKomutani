# src/game_core/unit_factory.py
from .unit import Piyade

class UnitFactory:
    @staticmethod
    def create_unit(unit_type, grid_x, grid_y, player_id): # player_id eklendi
        if unit_type == "Piyade":
            return Piyade(grid_x, grid_y, player_id)
        else:
            print(f"Warning: Unknown unit type '{unit_type}'. Piyade oluşturuluyor.")
            return Piyade(grid_x, grid_y, player_id)