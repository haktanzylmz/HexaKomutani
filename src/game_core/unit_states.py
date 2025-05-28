# src/game_core/unit_states.py
import pygame
from .commands import MoveUnitCommand, AttackCommand  # AttackCommand'ı ekledik


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
        if not self.unit.is_alive(): return  # Ölü birim seçilemez

        if clicked_tile and clicked_tile.unit_on_tile == self.unit:
            self.unit.set_state(SelectedState(self.unit))
            game_instance.selected_unit = self.unit
            game_instance.highlight_movable_tiles(self.unit)
            game_instance.highlight_attackable_tiles(self.unit)  # Saldırılabilecekleri de vurgula


class SelectedState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self):
        super().enter_state()
        self.unit.is_graphically_selected = True

    def exit_state(self):
        super().exit_state()
        self.unit.is_graphically_selected = False
        # game_instance.clear_highlighted_tiles() # Game'e taşıdık

    def handle_click(self, game_instance, clicked_tile):
        if not self.unit.is_alive():  # Seçili birim öldüyse bir şey yapma
            game_instance.clear_all_highlights()
            game_instance.selected_unit = None
            return

        if not clicked_tile:
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            if game_instance.selected_unit == self.unit:
                game_instance.selected_unit = None
            return

        # 1. Kendi üzerine tekrar tıklanırsa: Seçimi kaldır
        if clicked_tile.unit_on_tile == self.unit:
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None

        # 2. Boş ve yürünebilir bir hücreye tıklanırsa: Hareket et
        elif clicked_tile.is_walkable and not clicked_tile.unit_on_tile:
            distance = abs(clicked_tile.x_grid - self.unit.grid_x) + abs(clicked_tile.y_grid - self.unit.grid_y)
            if distance <= self.unit.movement_range:
                move_command = MoveUnitCommand(self.unit, clicked_tile.x_grid, clicked_tile.y_grid,
                                               game_instance.game_map)
                if game_instance.execute_command(move_command):
                    game_instance.clear_all_highlights()
                    self.unit.set_state(IdleState(self.unit))
                    game_instance.selected_unit = None
            else:
                print(f"Target tile for movement out of range for {self.unit.unit_type}.")

        # 3. Başka bir birimin olduğu hücreye tıklanırsa: Saldır
        elif clicked_tile.unit_on_tile and clicked_tile.unit_on_tile != self.unit:
            target_unit = clicked_tile.unit_on_tile
            # Saldırı menzil kontrolü
            attack_distance = abs(target_unit.grid_x - self.unit.grid_x) + abs(target_unit.grid_y - self.unit.grid_y)
            if attack_distance <= self.unit.attack_range:
                attack_command = AttackCommand(self.unit, target_unit, game_instance.game_map)
                if game_instance.execute_command(attack_command):
                    game_instance.clear_all_highlights()
                    # Saldırı sonrası birim ya Idle'a döner ya da bir "ActionCompletedState" eklenebilir.
                    # Şimdilik Idle'a dönsün.
                    self.unit.set_state(IdleState(self.unit))
                    game_instance.selected_unit = None
                    # Eğer hedef öldüyse ve seçili olan hedef idiyse, seçimi temizle
                    if not target_unit.is_alive() and game_instance.selected_unit == target_unit:
                        game_instance.selected_unit = None  # Bu zaten yukarıda yapılıyor
            else:
                print(f"Target unit for attack out of range for {self.unit.unit_type}.")
                # Menzil dışıysa, şimdilik seçimi iptal et ve Idle'a dön
                game_instance.clear_all_highlights()
                self.unit.set_state(IdleState(self.unit))
                game_instance.selected_unit = None
        else:  # Diğer durumlar (örn: yürünemez boş bir tile'a tıklama)
            print("Invalid action or target. Deselecting.")
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None