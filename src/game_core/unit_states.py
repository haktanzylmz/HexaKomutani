# src/game_core/unit_states.py
import pygame
from .commands import MoveUnitCommand  # DEĞİŞİKLİK BURADA: Artık aynı dizinden import ediliyor


class UnitState:
    def __init__(self, unit):
        self.unit = unit

    def enter_state(self):
        pass

    def exit_state(self):
        pass

    def handle_click(self, game_instance, clicked_tile):
        pass

    def update(self, dt):
        pass


class IdleState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def handle_click(self, game_instance, clicked_tile):
        if clicked_tile and clicked_tile.unit_on_tile == self.unit:
            self.unit.set_state(SelectedState(self.unit))
            game_instance.selected_unit = self.unit
            game_instance.highlight_movable_tiles(self.unit)


class SelectedState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self):
        super().enter_state()
        self.unit.is_graphically_selected = True

    def exit_state(self):
        super().exit_state()
        self.unit.is_graphically_selected = False
        # game_instance.clear_highlighted_tiles() # Game sınıfına eklenecek bir metot

    def handle_click(self, game_instance, clicked_tile):
        if not clicked_tile:
            game_instance.clear_highlighted_tiles()
            self.unit.set_state(IdleState(self.unit))
            if game_instance.selected_unit == self.unit:
                game_instance.selected_unit = None
            return

        if clicked_tile.unit_on_tile == self.unit:
            game_instance.clear_highlighted_tiles()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None

        elif clicked_tile.is_walkable and not clicked_tile.unit_on_tile:
            distance = abs(clicked_tile.x_grid - self.unit.grid_x) + abs(clicked_tile.y_grid - self.unit.grid_y)
            if distance <= self.unit.movement_range:
                move_command = MoveUnitCommand(self.unit, clicked_tile.x_grid, clicked_tile.y_grid,
                                               game_instance.game_map)
                if game_instance.execute_command(move_command):
                    game_instance.clear_highlighted_tiles()
                    self.unit.set_state(IdleState(self.unit))
                    game_instance.selected_unit = None
                else:
                    print(f"Move command failed for {self.unit.unit_type}")
            else:
                print(
                    f"Target tile out of range for {self.unit.unit_type}. Range: {self.unit.movement_range}, Distance: {distance}")

        elif clicked_tile.unit_on_tile and clicked_tile.unit_on_tile != self.unit:
            print(f"Target tile occupied by {clicked_tile.unit_on_tile.unit_type}. Deselecting current unit.")
            game_instance.clear_highlighted_tiles()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None