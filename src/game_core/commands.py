# src/game_core/commands.py (YENİ KONUMU: src/game_core/commands.py)

class ICommand:
    def __init__(self, description="Generic Command"):
        self.description = description

    def execute(self):
        raise NotImplementedError("Subclasses should implement this!")

    def undo(self):
        pass


class MoveUnitCommand(ICommand):
    def __init__(self, unit, new_grid_x, new_grid_y, game_map):
        super().__init__(f"Move {unit.unit_type} to ({new_grid_x}, {new_grid_y})")
        self.unit = unit
        self.old_grid_x = unit.grid_x
        self.old_grid_y = unit.grid_y
        self.new_grid_x = new_grid_x
        self.new_grid_y = new_grid_y
        self.game_map = game_map
        self.executed_successfully = False

    def execute(self):
        if self.unit.is_alive() and self.game_map.move_unit(self.unit, self.new_grid_x, self.new_grid_y):
            print(f"Executed: {self.description}")
            self.executed_successfully = True
            return True
        else:
            print(f"Failed to execute: {self.description} (Unit might be dead or target invalid)")
            self.executed_successfully = False
            return False

    def undo(self):
        if self.executed_successfully:
            if self.game_map.move_unit(self.unit, self.old_grid_x, self.old_grid_y):
                print(
                    f"Undid: {self.description}, {self.unit.unit_type} moved back to ({self.old_grid_x}, {self.old_grid_y})")
            else:
                print(f"Failed to undo: {self.description}")
        else:
            print(f"Cannot undo a command that was not successfully executed: {self.description}")


class AttackCommand(ICommand):
    def __init__(self, attacker, target_unit, game_map):
        super().__init__(
            f"{attacker.unit_type} attacks {target_unit.unit_type} at ({target_unit.grid_x}, {target_unit.grid_y})")
        self.attacker = attacker
        self.target_unit = target_unit
        self.game_map = game_map  # Haritadan birim silmek için gerekebilir
        self.damage_done = 0
        self.target_was_alive_before_attack = target_unit.is_alive()

    def execute(self):
        if not self.attacker.is_alive() or not self.target_unit.is_alive():
            print(f"Attack failed: {self.attacker.unit_type} or {self.target_unit.unit_type} is not alive.")
            return False

        # Saldırı menzil kontrolü burada veya komut oluşturulmadan önce yapılmalı.
        # Şimdilik komut oluşturulmadan önce yapıldığını varsayıyoruz.

        self.damage_done = self.attacker.attack_power  # Basit saldırı, savunma vs. yok
        self.target_unit.take_damage(self.damage_done)
        print(f"Executed: {self.description}, {self.target_unit.unit_type} health: {self.target_unit.health}")

        if not self.target_unit.is_alive():
            # Eğer hedef öldüyse, haritadan kaldır.
            self.game_map.remove_unit_from_map(self.target_unit)  # Yeni metot
        return True

    def undo(self):
        # Basit bir undo: Canı geri ver. Eğer öldüyse haritaya geri eklemek daha karmaşık olabilir.
        if self.target_was_alive_before_attack:  # Sadece hasar geri verilecek
            self.target_unit.health += self.damage_done
            # max_health'i geçmemesini sağla
            if self.target_unit.health > self.target_unit.max_health:
                self.target_unit.health = self.target_unit.max_health
            print(f"Undid attack: {self.target_unit.unit_type} health restored to {self.target_unit.health}")

            # Eğer undo sırasında hedef ölü durumdan canlıya döndüyse ve haritadan silindiyse,
            # bu durumu ele almak gerekir. Şimdilik basit tutuyoruz.
            if not self.game_map.get_tile_at_grid_coords(self.target_unit.grid_x, self.target_unit.grid_y).unit_on_tile:
                if self.target_unit.is_alive():  # Eğer canı geri gelince canlandıysa
                    print(f"Attempting to re-add {self.target_unit.unit_type} to map (Undo might be complex)")
                    # self.game_map.add_unit(self.target_unit, self.target_unit.grid_x, self.target_unit.grid_y) # Bu sorunlu olabilir, tile doluysa vs.
        else:
            print(f"Undo for attack not fully implemented if target died and was removed.")