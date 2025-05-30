# src/game_core/ai_strategy.py
import random
from .commands import MoveUnitCommand, AttackCommand
from .constants import PLAYER_HUMAN_ID  # Sabitleri import et


class AIStrategy:
    """Yapay zeka stratejileri için ana sınıf."""

    def choose_action(self, ai_unit, game_instance):
        raise NotImplementedError("Subclasses should implement this!")


class SimpleAggressiveStrategy(AIStrategy):
    def choose_action(self, ai_unit, game_instance):
        if not ai_unit.is_alive() or ai_unit.has_acted_this_turn:  # Canlı mı ve eylem hakkı var mı?
            return None

        game_map = game_instance.game_map

        # 1. Saldırı Önceliklendirme
        attackable_tiles = ai_unit.get_tiles_in_attack_range(game_map)
        potential_targets = []
        if attackable_tiles:
            for tile_obj in attackable_tiles:
                if tile_obj.unit_on_tile and tile_obj.unit_on_tile.is_alive():
                    potential_targets.append(tile_obj.unit_on_tile)

        if potential_targets:
            # Öncelik 1: Tek vuruşta öldürülebilir hedefler
            killable_targets = [t for t in potential_targets if t.health <= ai_unit.attack_power]
            if killable_targets:
                best_target = min(killable_targets, key=lambda t: t.health)  # Aralarından da en düşük canlıyı seç
                print(
                    f"AI (ID:{ai_unit.id}) -> ATTACK (Killable): {best_target.unit_type} (ID:{best_target.id}) at ({best_target.grid_x},{best_target.grid_y})")
                return AttackCommand(ai_unit, best_target, game_map)

            # Öncelik 2: Tek vuruşta öldürülebilir yoksa, en düşük canlı hedef
            best_target = min(potential_targets, key=lambda t: t.health)
            print(
                f"AI (ID:{ai_unit.id}) -> ATTACK (Lowest HP): {best_target.unit_type} (ID:{best_target.id}) at ({best_target.grid_x},{best_target.grid_y})")
            return AttackCommand(ai_unit, best_target, game_map)

        # 2. Saldıracak kimse yoksa, en yakın düşmana doğru hareket et
        enemy_units = [unit for unit in game_map.units if unit.player_id == PLAYER_HUMAN_ID and unit.is_alive()]
        if not enemy_units:
            print(f"AI (ID:{ai_unit.id}) -> No enemies left to target for movement.");
            return None

        closest_enemy = None;
        min_distance = float('inf')
        for enemy in enemy_units:
            distance = abs(ai_unit.grid_x - enemy.grid_x) + abs(ai_unit.grid_y - enemy.grid_y)
            if distance < min_distance: min_distance = distance; closest_enemy = enemy

        if closest_enemy:
            # En yakın düşmana doğru adım atmak için potansiyel hareketleri değerlendir
            possible_next_steps = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue  # Kendi yerinde durma
                    # Sadece yatay/dikey hareketleri önceliklendirelim (Manhattan için daha mantıklı)
                    if abs(dx) + abs(
                        dy) > 1 and ai_unit.movement_range < 2: continue  # Basit birimler için çaprazı zorlama

                    next_x, next_y = ai_unit.grid_x + dx, ai_unit.grid_y + dy
                    tile = game_map.get_tile_at_grid_coords(next_x, next_y)

                    # Hareket menzili içinde mi, tile boş ve yürünebilir mi?
                    move_dist = abs(dx) + abs(dy)  # Bu adımın maliyeti (basitçe 1)
                    if move_dist <= ai_unit.movement_range and tile and tile.is_walkable and not tile.unit_on_tile:
                        # Hedefe olan yeni mesafeyi hesapla
                        new_distance_to_target = abs(next_x - closest_enemy.grid_x) + abs(next_y - closest_enemy.grid_y)
                        possible_next_steps.append(((next_x, next_y), new_distance_to_target))

            if possible_next_steps:
                # Hedefe en çok yaklaştıran adımı seç
                possible_next_steps.sort(key=lambda item: item[1])  # Mesafeye göre sırala (küçükten büyüğe)
                best_move_coords = possible_next_steps[0][0]
                print(
                    f"AI (ID:{ai_unit.id}) -> MOVE to ({best_move_coords[0]},{best_move_coords[1]}) towards {closest_enemy.unit_type} (ID:{closest_enemy.id})")
                return MoveUnitCommand(ai_unit, best_move_coords[0], best_move_coords[1], game_map)

        print(f"AI (ID:{ai_unit.id}) -> No action decided.");
        return None