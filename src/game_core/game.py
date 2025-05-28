# src/game_core/game.py
import pygame
import time
import json
import os

from .map import Map
from .tile import Tile
from .unit_factory import UnitFactory
from .ai_strategy import SimpleAggressiveStrategy  # Stratejiyi import ediyoruz
from .unit import Unit
from .unit_states import IdleState, SelectedState

PLAYER_HUMAN_ID = 1
PLAYER_AI_ID = 2
SAVE_FILE_NAME = "savegame.json"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(SCRIPT_DIR)
LEVELS_DIR = os.path.join(SRC_DIR, "levels")
LEVEL_FILE_PREFIX = os.path.join(LEVELS_DIR, "level")

MAX_LEVELS = 2

STATE_NAME_TO_CLASS_MAP = {
    "IdleState": IdleState,
    "SelectedState": SelectedState,
}


class Game:
    def __init__(self, screen_width, screen_height, load_from_save=False):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")

        self.font_small = pygame.font.SysFont(None, 24)
        self.font_medium = pygame.font.SysFont(None, 30)
        self.clock = pygame.time.Clock()
        self.running = False
        self.selected_unit = None
        self.command_history = []
        self.highlighted_tiles_for_move = []
        self.highlighted_tiles_for_attack = []
        self.feedback_message = ""
        self.feedback_message_timer = 0
        self.feedback_message_duration = 120
        self.game_over_flag = False
        self.current_level_number = 1

        self.tile_size = 40
        self.initialized_successfully = False

        self.unit_factory = UnitFactory()
        # !!! AI STRATEJİSİ BURADA TANIMLANIYOR !!!
        self.ai_strategies = {"SimpleAggressiveStrategy": SimpleAggressiveStrategy()}
        self.default_ai_strategy = self.ai_strategies["SimpleAggressiveStrategy"]  # BU SATIR ÇOK ÖNEMLİ

        if load_from_save:
            if self.load_game(SAVE_FILE_NAME):
                self.initialized_successfully = True
                self.show_feedback_message("Game Loaded!", self.feedback_message_duration)
            else:
                print("Failed to load save game. Attempting to start a new game from level 1.")
                self.show_feedback_message("Load Failed. New Game Lvl 1.", self.feedback_message_duration)
                if self._initialize_game_for_level(1, is_new_game_session=True):
                    self.initialized_successfully = True
        else:
            if self._initialize_game_for_level(self.current_level_number, is_new_game_session=True):
                self.initialized_successfully = True

        if not self.initialized_successfully:
            print("FATAL: Game initialization failed. Check level files or save data.")
            if self.screen:
                error_surf = self.font_medium.render("Initialization Failed! Check Console.", True, (255, 0, 0))
                self.screen.blit(error_surf, (50, self.screen_height // 2))
                pygame.display.flip()
                pygame.time.wait(5000)

    def _initialize_game_for_level(self, level_number, is_new_game_session=False):
        self.current_level_number = level_number
        level_data = self.load_level_data(level_number)
        if not level_data:
            print(f"Could not load level {level_number} data. Initialization aborted.")
            return False

        self.map_cols = level_data.get("map_cols", self.screen_width // self.tile_size)
        self.map_rows = level_data.get("map_rows", self.screen_height // self.tile_size)

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.game_map.create_grid()

        self.current_player_id = PLAYER_HUMAN_ID
        self.game_map.units = []
        self.command_history = []
        self.selected_unit = None
        self.clear_all_highlights()

        if is_new_game_session:
            Unit._id_counter = 0

        self.setup_units_from_level_data(level_data)

        self.ai_turn_processed = False
        self.game_over_flag = False
        print(f"Level {level_number} initialized.")
        self.show_feedback_message(f"Level {level_number}: {level_data.get('level_name', '')}",
                                   self.feedback_message_duration)
        return True

    def load_level_data(self, level_number):
        filename = f"{LEVEL_FILE_PREFIX}{level_number}.json"
        print(f"Attempting to load level data from: {filename}")
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)
            print(f"Level {level_number} data loaded from {filename}")
            return level_data
        except FileNotFoundError:
            print(f"LEVEL FILE NOT FOUND AT: '{filename}'")
            self.show_feedback_message(f"Level File Not Found: level{level_number}.json", 9999)
            return None
        except Exception as e:
            print(f"Error loading level data from {filename}: {e}")
            self.show_feedback_message(f"Error Loading Level {level_number}!", 9999)
            return None

    def setup_units_from_level_data(self, level_data):
        if "player_units" in level_data:
            for unit_info in level_data["player_units"]:
                unit = self.unit_factory.create_unit(
                    unit_info["type"], unit_info["x"], unit_info["y"], unit_info["player_id"]
                )
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)
        if "ai_units" in level_data:
            for unit_info in level_data["ai_units"]:
                unit = self.unit_factory.create_unit(
                    unit_info["type"], unit_info["x"], unit_info["y"], unit_info["player_id"]
                )
                if unit and unit.player_id == PLAYER_AI_ID: unit.color = (200, 50, 50)
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)

    def show_feedback_message(self, message, duration_frames):
        self.feedback_message = message
        self.feedback_message_timer = duration_frames

    def save_game(self, filename):
        if not self.initialized_successfully:
            self.show_feedback_message("Cannot save: Game not initialized.", self.feedback_message_duration)
            return
        print(f"Saving game to {filename}...")
        if self.selected_unit: self.selected_unit.is_graphically_selected = False
        game_state_data = {
            "current_player_id": self.current_player_id,
            "current_level_number": self.current_level_number,
            "map_data": self.game_map.to_dict(),
            "units_data": [unit.to_dict() for unit in self.game_map.units if unit.is_alive()],
            "next_unit_id": Unit._id_counter,
            "game_over_flag": self.game_over_flag,
            "ai_turn_processed": self.ai_turn_processed
        }
        try:
            with open(filename, 'w') as f:
                json.dump(game_state_data, f, indent=4)
            print("Game saved successfully!")
            self.show_feedback_message("Game Saved!", duration_frames=self.feedback_message_duration)
        except IOError as e:
            print(f"Error saving game: {e}")
            self.show_feedback_message("Error Saving Game!", duration_frames=self.feedback_message_duration)

    def load_game(self, filename):
        print(f"Attempting to load game from {filename}...")
        try:
            with open(filename, 'r') as f:
                game_state_data = json.load(f)
            self.selected_unit = None
            self.clear_all_highlights()
            self.command_history = []

            self.current_level_number = game_state_data.get("current_level_number", 1)
            map_info = game_state_data["map_data"]
            self.map_rows = map_info["rows"]
            self.map_cols = map_info["cols"]

            self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
            self.game_map.grid = []
            for r_idx, row_data in enumerate(map_info["grid_tiles"]):
                current_row = []
                for c_idx, tile_data in enumerate(row_data):
                    tile = Tile.from_dict(tile_data, self.tile_size)
                    current_row.append(tile)
                self.game_map.grid.append(current_row)

            self.game_map.units = []
            Unit._id_counter = game_state_data.get("next_unit_id", Unit._id_counter)
            for unit_data in game_state_data["units_data"]:
                unit = self.unit_factory.create_unit(
                    unit_data["unit_type"], unit_data["grid_x"], unit_data["grid_y"], unit_data["player_id"]
                )
                unit.id = unit_data["id"]
                unit.grid_x = unit_data["grid_x"];
                unit.grid_y = unit_data["grid_y"]
                unit.health = unit_data["health"]
                unit.max_health = unit_data.get("max_health", unit.max_health)
                unit.attack_power = unit_data.get("attack_power", unit.attack_power)
                unit.movement_range = unit_data.get("movement_range", unit.movement_range)
                unit.attack_range = unit_data.get("attack_range", unit.attack_range)
                if unit.player_id == PLAYER_AI_ID:
                    unit.color = (200, 50, 50)
                elif unit.player_id == PLAYER_HUMAN_ID:
                    unit.color = (50, 150, 50)
                state_name = unit_data.get("current_state_name", "IdleState")
                state_class = STATE_NAME_TO_CLASS_MAP.get(state_name, IdleState)
                unit.set_state(state_class(unit))
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)

            self.current_player_id = game_state_data["current_player_id"]
            self.game_over_flag = game_state_data.get("game_over_flag", False)
            self.ai_turn_processed = game_state_data.get("ai_turn_processed", (
                        self.current_player_id == PLAYER_AI_ID and not self.game_over_flag))

            print("Game loaded successfully!")
            return True
        except FileNotFoundError:
            print(f"Save file '{filename}' not found.")
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            import traceback;
            traceback.print_exc()
            return False

    def run(self):
        if not self.initialized_successfully:
            print("Game could not be initialized. Exiting or displaying error.")
            if pygame.get_init():
                # Hata mesajı __init__ içinde zaten çizdirilmeye çalışıldı
                # pygame.time.wait(3000) # Bekleme __init__'te yapıldı
                pygame.quit()
            return

        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            if not self.game_over_flag:
                if self.current_player_id == PLAYER_AI_ID and self.running and not self.ai_turn_processed:
                    self.process_ai_turn()
                self.update()
            self.render()

        # Döngü bittikten sonra (self.running = False olduğunda)
        print("Exiting game loop...")
        if pygame.get_init():  # Eğer Pygame hala çalışıyorsa kapat
            pygame.quit()

    def execute_command(self, command):
        if command and command.execute():
            self.command_history.append(command)
            self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
            if self.selected_unit:
                if not self.selected_unit.is_alive() or \
                        self.selected_unit.current_state_name != SelectedState.__name__:
                    self.clear_all_highlights()
                    self.selected_unit = None
            return True
        return False

    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()
        if unit and unit.is_alive() and unit.player_id == self.current_player_id:
            self.highlighted_tiles_for_move = unit.get_tiles_in_movement_range(self.game_map)

    def highlight_attackable_tiles(self, unit):
        self.clear_highlighted_attack_tiles()
        if unit and unit.is_alive() and unit.player_id == self.current_player_id:
            self.highlighted_tiles_for_attack = unit.get_tiles_in_attack_range(self.game_map)

    def clear_highlighted_tiles(self):
        self.highlighted_tiles_for_move = []

    def clear_highlighted_attack_tiles(self):
        self.highlighted_tiles_for_attack = []

    def clear_all_highlights(self):
        self.clear_highlighted_tiles()
        self.clear_highlighted_attack_tiles()

    def end_turn(self):
        self.show_feedback_message(f"Player {self.current_player_id} Ends Turn", self.feedback_message_duration // 2)
        if self.selected_unit:
            self.selected_unit.set_state(IdleState(self.selected_unit))
            self.selected_unit = None
        self.clear_all_highlights()

        if self.current_player_id == PLAYER_HUMAN_ID:
            self.current_player_id = PLAYER_AI_ID
            self.ai_turn_processed = False
        else:
            self.current_player_id = PLAYER_HUMAN_ID

        if not self.check_game_over():
            self.show_feedback_message(f"Player {self.current_player_id}'s Turn", self.feedback_message_duration)

    def check_game_over(self):
        human_units_alive = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_HUMAN_ID)
        ai_units_alive = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_AI_ID)
        game_over_message = ""
        level_cleared = False

        if not ai_units_alive and human_units_alive:
            game_over_message = f"LEVEL {self.current_level_number} CLEARED!"
            level_cleared = True
        elif not human_units_alive and ai_units_alive:
            game_over_message = f"LEVEL {self.current_level_number} FAILED! AI Wins!"
            self.game_over_flag = True
        elif not human_units_alive and not ai_units_alive:
            game_over_message = f"LEVEL {self.current_level_number} FAILED! Draw!"
            self.game_over_flag = True

        if game_over_message:
            print(game_over_message)
            self.show_feedback_message(game_over_message, duration_frames=180)
            if level_cleared:
                self.current_level_number += 1
                if self.current_level_number > MAX_LEVELS:
                    self.show_feedback_message("CONGRATULATIONS! You beat all levels!", 9999)
                    self.game_over_flag = True
                else:
                    pygame.display.flip()
                    time.sleep(2)
                    if not self._initialize_game_for_level(self.current_level_number):
                        self.game_over_flag = True
                        # self.running = False # _initialize_game_for_level başarısızsa zaten init_successful false olur
            return self.game_over_flag
        return False

    def process_ai_turn(self):
        if self.current_player_id == PLAYER_AI_ID and not self.ai_turn_processed and self.running and not self.game_over_flag:
            self.show_feedback_message("AI is thinking...", self.feedback_message_duration)
            pygame.display.flip()
            time.sleep(0.5)
            ai_units = [unit for unit in self.game_map.units if unit.player_id == PLAYER_AI_ID and unit.is_alive()]
            if not ai_units:
                self.end_turn()
                return
            processed_action_for_one_unit = False
            for ai_unit in ai_units:
                if not ai_unit.is_alive(): continue
                action_command = self.default_ai_strategy.choose_action(ai_unit,
                                                                        self)  # self.default_ai_strategy KULLANILIYOR
                if action_command:
                    self.show_feedback_message(f"AI: {action_command.description}", self.feedback_message_duration)
                    self.execute_command(action_command)
                    pygame.display.flip()
                    time.sleep(0.5)
                    processed_action_for_one_unit = True
                    break
            if not processed_action_for_one_unit:
                self.show_feedback_message("AI: No action taken.", self.feedback_message_duration)
            self.ai_turn_processed = True
            self.end_turn()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if not self.initialized_successfully:
                continue

            if self.game_over_flag:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.running = False
                continue

            if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        self.handle_mouse_click(mouse_pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    if self.current_player_id == PLAYER_HUMAN_ID and self.command_history and not self.game_over_flag:
                        last_command = self.command_history.pop()
                        last_command.undo()
                        self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
                        if self.selected_unit:
                            if not self.selected_unit.is_alive(): self.selected_unit = None
                        self.clear_all_highlights()
                        if self.selected_unit:
                            self.selected_unit.set_state(type(self.selected_unit.current_state)(self.selected_unit))
                            self.highlight_movable_tiles(self.selected_unit)
                            self.highlight_attackable_tiles(self.selected_unit)
                        self.show_feedback_message("Last Action Undone", self.feedback_message_duration)

                if event.key == pygame.K_e:
                    if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:
                        self.end_turn()

                if event.key == pygame.K_k:
                    if not self.game_over_flag:
                        self.save_game(SAVE_FILE_NAME)

                if event.key == pygame.K_y:
                    print("Y key pressed, attempting to load game...")  # Konsol logu
                    if self.load_game(SAVE_FILE_NAME):
                        self.show_feedback_message("Game Reloaded!",
                                                   self.feedback_message_duration)  # Zaten load_game içinde var
                        self.selected_unit = None
                        self.clear_all_highlights()
                    else:
                        self.show_feedback_message("Reload Failed. Check console.", self.feedback_message_duration)

    def handle_mouse_click(self, mouse_pos):
        if self.current_player_id != PLAYER_HUMAN_ID or self.game_over_flag:
            return
        clicked_tile = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1])
        active_unit_for_click = self.selected_unit
        if not active_unit_for_click and clicked_tile and clicked_tile.unit_on_tile:
            if clicked_tile.unit_on_tile.player_id == PLAYER_HUMAN_ID and clicked_tile.unit_on_tile.is_alive():
                active_unit_for_click = clicked_tile.unit_on_tile
        if active_unit_for_click:
            active_unit_for_click.handle_click(self, clicked_tile)
        elif clicked_tile:
            if self.selected_unit:
                self.selected_unit.handle_click(self, clicked_tile)
            else:
                self.clear_all_highlights()

    def update(self):
        if self.feedback_message_timer > 0:
            self.feedback_message_timer -= 1
            if self.feedback_message_timer == 0:
                self.feedback_message = ""
        if not self.game_over_flag:
            for unit in self.game_map.units:
                if unit.is_alive():
                    unit.update(self.dt)

    def render(self):
        if not self.initialized_successfully:
            if self.screen:
                self.screen.fill((50, 0, 0))
                error_surf = self.font_medium.render("GAME INIT FAILED. Check Console/Level Files.", True,
                                                     (255, 255, 255))
                rect = error_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(error_surf, rect)
                pygame.display.flip()
            return

        self.screen.fill((30, 30, 30))
        if hasattr(self, 'game_map') and self.game_map:
            self.game_map.draw(self.screen)

        for tile in self.highlighted_tiles_for_move:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((0, 255, 0, 80))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))
        for tile in self.highlighted_tiles_for_attack:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((255, 0, 0, 80))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        level_turn_text_str = f"Lvl: {self.current_level_number} | Turn: P{self.current_player_id} ({'Human' if self.current_player_id == PLAYER_HUMAN_ID else 'AI'})"
        if self.game_over_flag:
            # Oyun sonu mesajı feedback_message'dan alınabilir veya burada yeniden oluşturulabilir.
            # En son feedback_message neyse o gösterilsin.
            if "CONGRATULATIONS" in self.feedback_message:
                level_turn_text_str = "YOU WIN THE GAME!"
            elif "FAILED" in self.feedback_message or "AI Wins" in self.feedback_message:
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number}"
            elif "Draw" in self.feedback_message:
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number} (Draw)"
            else:  # Genel bir game over durumu
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number}"

        level_turn_surface = self.font_medium.render(level_turn_text_str, True, (255, 255, 255))
        self.screen.blit(level_turn_surface, (10, 10))

        command_text_str = "'E' End Turn | 'K' Save | 'Y' Load | 'U' Undo"
        command_surface = self.font_small.render(command_text_str, True, (255, 255, 255))
        self.screen.blit(command_surface, (self.screen_width - command_surface.get_width() - 10, 10))

        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            msg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            self.screen.blit(feedback_surf, msg_rect)

        pygame.display.flip()