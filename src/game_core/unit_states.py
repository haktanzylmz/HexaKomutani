# src/game_core/unit_states.py
import pygame
from .commands import MoveUnitCommand, AttackCommand


class UnitState:
    def __init__(self, unit):
        self.unit = unit

    def enter_state(self, game_instance=None):
        pass

    def exit_state(self, game_instance=None):
        pass

    def handle_click(self, game_instance, clicked_tile):
        pass

    def update(self, dt):
        pass


class IdleState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self, game_instance=None):
        super().enter_state(game_instance)
        self.unit.is_graphically_selected = False
        if game_instance and game_instance.selected_unit == self.unit:
            game_instance.selected_unit = None
            game_instance.clear_all_highlights()

    def handle_click(self, game_instance, clicked_tile):
        if not self.unit.is_alive(): return

        # !!! YENİ KONTROL: Eğer birim bu tur zaten eylem yaptıysa, tekrar seçilemez !!!
        if self.unit.has_acted_this_turn:
            print(f"{self.unit.unit_type} (ID:{self.unit.id}) has already acted this turn.")
            game_instance.show_feedback_message("Unit has already acted!", game_instance.feedback_message_duration // 2)
            # Seçimi temizle (eğer başka bir birim seçiliyse)
            if game_instance.selected_unit and game_instance.selected_unit != self.unit:
                # game_instance.selected_unit.set_state(IdleState(game_instance.selected_unit), game_instance)
                # Yukarıdaki yerine doğrudan game_instance'tan temizlemek daha iyi olabilir
                game_instance.selected_unit.is_graphically_selected = False  # Önceki seçili olanın seçimini kaldır
                game_instance.selected_unit = None
                game_instance.clear_all_highlights()
            return

        if game_instance.current_player_id == self.unit.player_id:
            if clicked_tile and clicked_tile.unit_on_tile == self.unit:
                self.unit.set_state(SelectedState(self.unit), game_instance)


class SelectedState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self, game_instance=None):
        super().enter_state(game_instance)
        # Eğer birim zaten eylem yapmışsa bu duruma hiç girmemeli (IdleState kontrol etmeli)
        # Ama ek bir kontrol olarak burada da yapılabilir.
        if game_instance and self.unit.has_acted_this_turn:
            print(f"Attempted to select an already acted unit (ID:{self.unit.id}). Reverting to Idle.")
            self.unit.set_state(IdleState(self.unit), game_instance)
            return

        if game_instance and self.unit.player_id == game_instance.current_player_id:
            self.unit.is_graphically_selected = True
            game_instance.selected_unit = self.unit
            game_instance.highlight_movable_tiles(self.unit)
            game_instance.highlight_attackable_tiles(self.unit)
        elif game_instance:
            self.unit.set_state(IdleState(self.unit), game_instance)

    def exit_state(self, game_instance=None):
        super().exit_state(game_instance)
        self.unit.is_graphically_selected = False
        # Vurguların temizlenmesi artık IdleState.enter_state'te veya Game'de selected_unit değişince yapılıyor.

    def handle_click(self, game_instance, clicked_tile):
        if not self.unit.is_alive() or self.unit.player_id != game_instance.current_player_id or self.unit.has_acted_this_turn:
            # Eğer birim bu tur zaten eylem yaptıysa, tıklamalar işlenmemeli. Idle'a dön.
            if game_instance:
                game_instance.clear_all_highlights()
                if game_instance.selected_unit == self.unit:
                    game_instance.selected_unit = None
            if self.unit.current_state == self:
                self.unit.set_state(IdleState(self.unit), game_instance)
            return

        if not clicked_tile:
            self.unit.set_state(IdleState(self.unit), game_instance)
            return

        action_command_executed = False

        if clicked_tile.unit_on_tile == self.unit:  # Kendi üzerine tıklama
            self.unit.set_state(IdleState(self.unit), game_instance)
            return

        elif clicked_tile.is_walkable and not clicked_tile.unit_on_tile:  # Hareket
            if clicked_tile in game_instance.highlighted_tiles_for_move:
                move_command = MoveUnitCommand(self.unit, clicked_tile.x_grid, clicked_tile.y_grid,
                                               game_instance.game_map)
                if game_instance.execute_command(move_command):
                    action_command_executed = True
            else:
                print(f"Target tile for movement out of range or invalid for {self.unit.unit_type}.")

        elif clicked_tile.unit_on_tile and clicked_tile.unit_on_tile.player_id != self.unit.player_id:  # Saldırı
            target_unit = clicked_tile.unit_on_tile
            if clicked_tile in game_instance.highlighted_tiles_for_attack:
                attack_command = AttackCommand(self.unit, target_unit, game_instance.game_map)
                if game_instance.execute_command(attack_command):
                    action_command_executed = True
            else:
                print(f"Target unit for attack out of range or invalid for {self.unit.unit_type}.")

        else:
            print(f"Invalid action or target on selected unit. {self.unit.unit_type} remains selected.")
            return  # Geçersiz tıklamada state değişmiyor, seçili kalıyor.

        if action_command_executed:
            self.unit.has_acted_this_turn = True  # !!! EYLEM YAPTI BAYRAĞINI AYARLA !!!
            self.unit.set_state(IdleState(self.unit), game_instance)