# src/game_core/ai_strategy.py
import random
from .commands import MoveUnitCommand, AttackCommand


class AIStrategy:
    """Yapay zeka stratejileri için ana sınıf."""

    def choose_action(self, ai_unit, game_instance):
        """
        AI birimi için bir eylem (komut) seçer.
        Döndürülen değer bir ICommand nesnesi veya None olmalı.
        """
        raise NotImplementedError("Subclasses should implement this!")


class SimpleAggressiveStrategy(AIStrategy):
    def choose_action(self, ai_unit, game_instance):
        if not ai_unit.is_alive():
            return None

        game_map = game_instance.game_map

        # 1. Saldırılabilecek düşmanları bul
        attackable_tiles = ai_unit.get_tiles_in_attack_range(game_map)
        if attackable_tiles:
            # Rastgele bir saldırılabilir hedef seç (şimdilik)
            target_tile = random.choice(attackable_tiles)
            target_unit = target_tile.unit_on_tile
            if target_unit:  # Ekstra kontrol, normalde olmalı
                print(
                    f"AI ({ai_unit.unit_type}) decided to ATTACK {target_unit.unit_type} at ({target_tile.x_grid}, {target_tile.y_grid})")
                return AttackCommand(ai_unit, target_unit, game_map)

        # 2. Saldıracak kimse yoksa, en yakın düşmana doğru hareket et
        # En yakın düşmanı bul (basitçe tüm düşman birimlerini kontrol et)
        closest_enemy = None
        min_distance = float('inf')

        human_player_id = 1  # Varsayım
        enemy_units = [unit for unit in game_map.units if unit.player_id == human_player_id and unit.is_alive()]

        if not enemy_units:
            print(f"AI ({ai_unit.unit_type}) has no enemies to target.")
            return None  # Hedef yoksa bir şey yapma

        for enemy in enemy_units:
            distance = abs(ai_unit.grid_x - enemy.grid_x) + abs(ai_unit.grid_y - enemy.grid_y)
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy

        if closest_enemy:
            # Hareket edilecek en iyi tile'ı bul (çok basit yaklaşım: x veya y'de yaklaş)
            # Daha gelişmiş pathfinding (A*) ileride eklenebilir.
            move_options = []
            # Hedefe doğru x ekseninde mi y ekseninde mi yaklaşılacağına karar ver
            delta_x = closest_enemy.grid_x - ai_unit.grid_x
            delta_y = closest_enemy.grid_y - ai_unit.grid_y

            potential_moves = []
            if abs(delta_x) > abs(delta_y):  # X ekseninde daha uzak, x'e öncelik ver
                if delta_x > 0:
                    potential_moves.append((ai_unit.grid_x + 1, ai_unit.grid_y))
                elif delta_x < 0:
                    potential_moves.append((ai_unit.grid_x - 1, ai_unit.grid_y))
                if delta_y > 0:
                    potential_moves.append((ai_unit.grid_x, ai_unit.grid_y + 1))
                elif delta_y < 0:
                    potential_moves.append((ai_unit.grid_x, ai_unit.grid_y - 1))
            else:  # Y ekseninde daha uzak veya eşit, y'ye öncelik ver
                if delta_y > 0:
                    potential_moves.append((ai_unit.grid_x, ai_unit.grid_y + 1))
                elif delta_y < 0:
                    potential_moves.append((ai_unit.grid_x, ai_unit.grid_y - 1))
                if delta_x > 0:
                    potential_moves.append((ai_unit.grid_x + 1, ai_unit.grid_y))
                elif delta_x < 0:
                    potential_moves.append((ai_unit.grid_x - 1, ai_unit.grid_y))

            # Bu potansiyel hareketlerden geçerli ve menzil içinde olanları seç
            valid_move_tiles = ai_unit.get_tiles_in_movement_range(game_map)

            best_move_tile = None
            # Potansiyel hareketleri deneyip hedefe en çok yaklaştıranı seçmeye çalış
            # Bu kısım daha sofistike olabilir. Şimdilik, menzil içindeki geçerli bir tile'a rastgele hareket etsin.
            # Veya yukarıdaki potential_moves'tan ilk geçerli olanı seçsin.

            for move_x, move_y in potential_moves:
                tile = game_map.get_tile_at_grid_coords(move_x, move_y)
                if tile in valid_move_tiles:  # Hem geçerli hem de menzil içinde olmalı
                    best_move_tile = tile
                    break  # İlk uygun olanı seç

            if best_move_tile:
                print(
                    f"AI ({ai_unit.unit_type}) decided to MOVE towards ({best_move_tile.x_grid}, {best_move_tile.y_grid})")
                return MoveUnitCommand(ai_unit, best_move_tile.x_grid, best_move_tile.y_grid, game_map)

        print(f"AI ({ai_unit.unit_type}) could not decide on an action.")
        return None  # Hiçbir eylem bulunamadıysa