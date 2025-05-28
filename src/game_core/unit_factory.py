# src/game_core/unit_factory.py
from .unit import Piyade # , Tank, Topcu # Diğer birimler eklendikçe import edilecek

class UnitFactory:
    @staticmethod
    def create_unit(unit_type, grid_x, grid_y):
        if unit_type == "Piyade":
            return Piyade(grid_x, grid_y)
        # elif unit_type == "Tank":
        #     return Tank(grid_x, grid_y)
        # Diğer birim türleri için koşullar eklenebilir
        else:
            # raise ValueError(f"Unknown unit type: {unit_type}")
            print(f"Warning: Unknown unit type '{unit_type}'. Piyade oluşturuluyor.")
            return Piyade(grid_x, grid_y) # Varsayılan olarak Piyade dönebilir veya hata fırlatabilir