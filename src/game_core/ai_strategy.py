# src/game_core/ai_strategy.py
import random
from .commands import MoveUnitCommand, AttackCommand
from .constants import PLAYER_HUMAN_ID, PLAYER_AI_ID  # Sabitleri import et


class AIStrategy:
    """Yapay zeka stratejileri için ana sınıf."""

    def choose_action(self, ai_unit, game_instance):
        raise NotImplementedError("Subclasses should implement this!")


class SimpleAggressiveStrategy(AIStrategy):
    def choose_action(self, ai_unit, game_instance):
        if not ai_unit.is_alive() or ai_unit.has_acted_this_turn: return None
        game_map = game_instance.game_map

        attackable_tiles = ai_unit.get_tiles_in_attack_range(game_map)
        potential_targets = []
        if attackable_tiles:
            for tile_obj in attackable_tiles:
                if tile_obj.unit_on_tile and tile_obj.unit_on_tile.is_alive():
                    potential_targets.append(tile_obj.unit_on_tile)

        if potential_targets:
            killable_targets = [t for t in potential_targets if t.health <= ai_unit.attack_power]
            if killable_targets:
                best_target = min(killable_targets, key=lambda t: t.health)
                print(
                    f"AI (Aggressive ID:{ai_unit.id}) -> ATTACK (Killable): {best_target.unit_type} (ID:{best_target.id})")
                return AttackCommand(ai_unit, best_target, game_map)
            best_target = min(potential_targets, key=lambda t: t.health)
            print(
                f"AI (Aggressive ID:{ai_unit.id}) -> ATTACK (Lowest HP): {best_target.unit_type} (ID:{best_target.id})")
            return AttackCommand(ai_unit, best_target, game_map)

        enemy_units = [u for u in game_map.units if u.player_id == PLAYER_HUMAN_ID and u.is_alive()]
        if not enemy_units: print(f"AI (Aggressive ID:{ai_unit.id}) -> No enemies for movement."); return None

        closest_enemy = None;
        min_distance = float('inf')
        for enemy in enemy_units:
            distance = abs(ai_unit.grid_x - enemy.grid_x) + abs(ai_unit.grid_y - enemy.grid_y)
            if distance < min_distance: min_distance = distance; closest_enemy = enemy

        if closest_enemy:
            possible_next_steps = []
            # Basit adım mantığı (önce eksenlerde, sonra çaprazlar)
            preferred_steps = []
            if closest_enemy.grid_x > ai_unit.grid_x:
                preferred_steps.append((ai_unit.grid_x + 1, ai_unit.grid_y))
            elif closest_enemy.grid_x < ai_unit.grid_x:
                preferred_steps.append((ai_unit.grid_x - 1, ai_unit.grid_y))
            if closest_enemy.grid_y > ai_unit.grid_y:
                preferred_steps.append((ai_unit.grid_x, ai_unit.grid_y + 1))
            elif closest_enemy.grid_y < ai_unit.grid_y:
                preferred_steps.append((ai_unit.grid_x, ai_unit.grid_y - 1))

            random.shuffle(preferred_steps)  # Biraz rastgelelik katmak için

            valid_move_tiles = ai_unit.get_tiles_in_movement_range(game_map)
            best_move_tile_obj = None

            for move_x, move_y in preferred_steps:
                tile = game_map.get_tile_at_grid_coords(move_x, move_y)
                if tile in valid_move_tiles: best_move_tile_obj = tile; break

            if not best_move_tile_obj and valid_move_tiles:  # Öncelikli hamle yoksa, hedefe yaklaştıran herhangi bir geçerli hamle
                current_min_dist_to_target = min_distance
                temp_best_moves = []
                for tile_obj in valid_move_tiles:
                    new_dist = abs(tile_obj.x_grid - closest_enemy.grid_x) + abs(tile_obj.y_grid - closest_enemy.grid_y)
                    if new_dist < current_min_dist_to_target:
                        temp_best_moves.append(tile_obj)
                if temp_best_moves:
                    best_move_tile_obj = random.choice(temp_best_moves)
                elif valid_move_tiles:
                    best_move_tile_obj = random.choice(valid_move_tiles)  # En kötü rastgele bir geçerli hamle

            if best_move_tile_obj:
                print(
                    f"AI (Aggressive ID:{ai_unit.id}) -> MOVE to ({best_move_tile_obj.x_grid},{best_move_tile_obj.y_grid}) towards {closest_enemy.unit_type} (ID:{closest_enemy.id})")
                return MoveUnitCommand(ai_unit, best_move_tile_obj.x_grid, best_move_tile_obj.y_grid, game_map)
        print(f"AI (Aggressive ID:{ai_unit.id}) -> No action decided.");
        return None


class DefensiveStrategy(AIStrategy):
    """
    Savunmacı yapay zeka stratejisi.
    - Sadece menzilindeki düşmanlara saldırır (öncelik canı az olan veya öldürülebilir olan).
    - Eğer canı kritik seviyedeyse ve saldıracak hedefi yoksa veya düşman güçlüyse geri çekilebilir (ileride eklenebilir).
    - Genellikle pozisyonunu korur veya daha güvenli bir yere hareket eder.
    """

    def choose_action(self, ai_unit, game_instance):
        if not ai_unit.is_alive() or ai_unit.has_acted_this_turn:
            return None

        game_map = game_instance.game_map

        # 1. Saldırılabilecek düşmanları bul
        attackable_tiles = ai_unit.get_tiles_in_attack_range(game_map)
        potential_targets = []
        if attackable_tiles:
            for tile_obj in attackable_tiles:
                if tile_obj.unit_on_tile and tile_obj.unit_on_tile.is_alive():
                    potential_targets.append(tile_obj.unit_on_tile)

        if potential_targets:
            # Öncelik 1: Tek vuruşta öldürülebilir hedef
            killable_targets = [t for t in potential_targets if t.health <= ai_unit.attack_power]
            if killable_targets:
                best_target = min(killable_targets, key=lambda t: t.health)
                print(
                    f"AI (ID:{ai_unit.id}) [Defensive] -> ATTACK (Killable): {best_target.unit_type} (ID:{best_target.id})")
                return AttackCommand(ai_unit, best_target, game_map)

            # Öncelik 2: Canı %75'ten fazlaysa en düşük canlıya saldır
            if ai_unit.health > ai_unit.max_health * 0.75:
                best_target = min(potential_targets, key=lambda t: t.health)
                print(
                    f"AI (ID:{ai_unit.id}) [Defensive] -> ATTACK (Lowest HP, Health OK): {best_target.unit_type} (ID:{best_target.id})")
                return AttackCommand(ai_unit, best_target, game_map)
            else:
                print(
                    f"AI (ID:{ai_unit.id}) [Defensive] -> HOLDING (Targets in range, but low health or no kill shot).")
                return None  # Canı azsa saldırma, pozisyonunu koru

        # 2. Saldıracak kimse yoksa, pozisyonunu koru (hareket etme)
        #    İleride: Eğer yakınlarda düşman varsa ve birim güvendeyse, iyi bir savunma pozisyonuna geçebilir.
        #            Eğer canı azsa, güvenli bir yere geri çekilebilir.
        print(f"AI (ID:{ai_unit.id}) [Defensive] -> HOLDING POSITION (No targets in attack range).")
        return None