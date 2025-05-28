# src/game_core/unit_states.py
import pygame
from .commands import MoveUnitCommand, AttackCommand

PLAYER_HUMAN_ID = 1  # game.py'daki ile aynı olmalı


class UnitState:
    def __init__(self, unit):
        self.unit = unit

    def enter_state(self):
        # print(f"{self.unit} entering {self.__class__.__name__}")
        pass

    def exit_state(self):
        # print(f"{self.unit} exiting {self.__class__.__name__}")
        pass

    def handle_click(self, game_instance, clicked_tile):
        pass

    def update(self, dt):
        pass


class IdleState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def handle_click(self, game_instance, clicked_tile):
        if not self.unit.is_alive(): return

        # Sadece mevcut insan oyuncu kendi birimini seçebilir
        if game_instance.current_player_id == PLAYER_HUMAN_ID and self.unit.player_id == PLAYER_HUMAN_ID:
            if clicked_tile and clicked_tile.unit_on_tile == self.unit:
                self.unit.set_state(SelectedState(self.unit))
                game_instance.selected_unit = self.unit
                game_instance.highlight_movable_tiles(self.unit)
                game_instance.highlight_attackable_tiles(self.unit)


class SelectedState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self):
        super().enter_state()
        if self.unit.player_id == PLAYER_HUMAN_ID:  # Sadece insan oyuncunun seçimi görselleşsin
            self.unit.is_graphically_selected = True

    def exit_state(self):
        super().exit_state()
        self.unit.is_graphically_selected = False
        # game_instance.clear_all_highlights() # Bu, game_instance.selected_unit = None sonrası yapılmalı

    def handle_click(self, game_instance, clicked_tile):
        if not self.unit.is_alive() or self.unit.player_id != PLAYER_HUMAN_ID:  # Sadece canlı ve insan oyuncunun birimi eylem yapabilir
            game_instance.clear_all_highlights()
            if game_instance.selected_unit == self.unit:
                game_instance.selected_unit = None
            if self.unit.player_id == PLAYER_HUMAN_ID:  # Kendi state'ini Idle yap
                self.unit.set_state(IdleState(self.unit))
            return

        if not clicked_tile:
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            if game_instance.selected_unit == self.unit:
                game_instance.selected_unit = None
            return

        if clicked_tile.unit_on_tile == self.unit:
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None

        elif clicked_tile.is_walkable and not clicked_tile.unit_on_tile:  # Hareket
            # Menzil içindeki tile'lar zaten Game'de highlight_movable_tiles ile belirleniyor
            # Bu tile onlardan biri mi diye kontrol etmek daha doğru olur.
            if clicked_tile in game_instance.highlighted_tiles_for_move:  # Vurgulananlardan biri mi?
                move_command = MoveUnitCommand(self.unit, clicked_tile.x_grid, clicked_tile.y_grid,
                                               game_instance.game_map)
                if game_instance.execute_command(move_command):
                    # game_instance.clear_all_highlights() # execute_command sonrası Game'de yönetiliyor
                    # self.unit.set_state(IdleState(self.unit))
                    # game_instance.selected_unit = None
                    # Bu kısım execute_command sonrası game'de selected_unit'in durumuna göre yönetilmeli
                    # Eğer komut başarılıysa, birim zaten Idle'a dönecek şekilde execute_command sonrası ayarlanmalı
                    # Ya da komutun kendisi bir sonraki state'i belirleyebilir. Şimdilik Game hallediyor.
                    pass  # Game execute_command sonrası seçimi ve state'i yönetiyor
            else:
                print(f"Target tile for movement out of range or invalid for {self.unit.unit_type}.")

        elif clicked_tile.unit_on_tile and clicked_tile.unit_on_tile.player_id != self.unit.player_id:  # Saldırı
            target_unit = clicked_tile.unit_on_tile
            if clicked_tile in game_instance.highlighted_tiles_for_attack:  # Vurgulananlardan biri mi?
                attack_command = AttackCommand(self.unit, target_unit, game_instance.game_map)
                game_instance.execute_command(attack_command)
            else:
                print(f"Target unit for attack out of range or invalid for {self.unit.unit_type}.")
        else:
            print("Invalid action or target on selected unit. Deselecting.")
            game_instance.clear_all_highlights()
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None