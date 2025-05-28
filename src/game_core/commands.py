# src/game_core/commands.py

class ICommand:
    """Komut arayüzü."""
    def __init__(self, description="Generic Command"):
        self.description = description

    def execute(self):
        """Komutu çalıştırır."""
        raise NotImplementedError("Subclasses should implement this!")

    def undo(self):
        """Komutu geri alır (ileride eklenebilir)."""
        # print(f"Undo for {self.description} not implemented.")
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
        # Menzil kontrolünü burada veya komut oluşturulmadan önce yapabiliriz.
        # Şimdilik komut oluşturulmadan önce yapılacağını varsayalım.
        if self.game_map.move_unit(self.unit, self.new_grid_x, self.new_grid_y):
            print(f"Executed: {self.description}")
            self.executed_successfully = True
            return True
        else:
            print(f"Failed to execute: {self.description}")
            self.executed_successfully = False
            return False

    def undo(self):
        # Eğer hareket başarılı olduysa geri al
        if self.executed_successfully:
            if self.game_map.move_unit(self.unit, self.old_grid_x, self.old_grid_y):
                print(f"Undid: {self.description}, {self.unit.unit_type} moved back to ({self.old_grid_x}, {self.old_grid_y})")
            else:
                print(f"Failed to undo: {self.description}")
        else:
            print(f"Cannot undo a command that was not successfully executed: {self.description}")

# Gelecekte AttackUnitCommand, DefendCommand gibi komutlar eklenebilir.