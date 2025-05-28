# src/game_core/game.py
import pygame
import time
import json
import os

from .map import Map
from .tile import Tile
from .unit_factory import UnitFactory
from .ai_strategy import SimpleAggressiveStrategy
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

# Oyun Durumları Sabitleri
GAME_STATE_MAIN_MENU = "main_menu"
GAME_STATE_GAMEPLAY = "gameplay"


# GAME_STATE_LOGIN = "login"
# GAME_STATE_REGISTER = "register"

class Game:
    def __init__(self, screen_width, screen_height, load_from_save_on_start=False):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")

        self.font_small = pygame.font.SysFont(None, 24)
        self.font_medium = pygame.font.SysFont(None, 30)
        self.font_large = pygame.font.SysFont(None, 50)

        self.clock = pygame.time.Clock()
        self.running = False
        self.current_game_state = GAME_STATE_MAIN_MENU

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
        self.ai_strategies = {"SimpleAggressiveStrategy": SimpleAggressiveStrategy()}
        self.default_ai_strategy = self.ai_strategies["SimpleAggressiveStrategy"]

        self.main_menu_buttons = {}

        self.game_map = None
        self.map_cols = 0
        self.map_rows = 0
        self.current_player_id = PLAYER_HUMAN_ID
        self.ai_turn_processed = False

        if load_from_save_on_start:
            if self.load_game_into_gameplay(SAVE_FILE_NAME):
                self.current_game_state = GAME_STATE_GAMEPLAY
            else:
                self.current_game_state = GAME_STATE_MAIN_MENU
                self.show_feedback_message("Load Failed. Showing Main Menu.", self.feedback_message_duration)

    def initialize_gameplay_state(self, level_to_load=1, is_new_game_session=True):
        print(f"Initializing gameplay state for level {level_to_load}, new session: {is_new_game_session}")
        self.selected_unit = None
        self.command_history = []
        self.highlighted_tiles_for_move = []  # Bunlar burada sıfırlanmalı
        self.highlighted_tiles_for_attack = []  # Bunlar burada sıfırlanmalı
        self.current_level_number = level_to_load

        if self._initialize_game_for_level(self.current_level_number, is_new_game_session=is_new_game_session):
            self.initialized_successfully = True
            return True
        else:
            self.initialized_successfully = False
            self.show_feedback_message("Failed to initialize gameplay.", self.feedback_message_duration)
            return False

    def _initialize_game_for_level(self, level_number, is_new_game_session=False):
        self.current_level_number = level_number
        level_data = self.load_level_data(level_number)
        if not level_data:
            print(f"Could not load level {level_number} data. Initialization aborted for _initialize_game_for_level.")
            return False

        self.map_cols = level_data.get("map_cols", self.screen_width // self.tile_size)
        self.map_rows = level_data.get("map_rows", self.screen_height // self.tile_size)

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.game_map.create_grid()

        self.current_player_id = PLAYER_HUMAN_ID
        self.game_map.units = []
        self.selected_unit = None
        self.clear_all_highlights()

        if is_new_game_session:
            Unit._id_counter = 0

        self.setup_units_from_level_data(level_data)

        self.ai_turn_processed = False
        self.game_over_flag = False
        print(f"Level {level_number} initialized for gameplay.")
        self.show_feedback_message(f"Level {level_number}: {level_data.get('level_name', 'Unknown Level')}",
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
        if not self.initialized_successfully or not self.game_map:
            self.show_feedback_message("Cannot save: Gameplay not active.", self.feedback_message_duration)
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
        print(f"Attempting to load game data from {filename}...")
        try:
            with open(filename, 'r') as f:
                game_state_data = json.load(f)
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
            self.selected_unit = None
            self.clear_all_highlights()  # !!! BU METODUN TANIMLANMIŞ OLMASI GEREKİR !!!
            print("Game data parsed successfully for loading!")
            return True
        except FileNotFoundError:
            print(f"Save file '{filename}' not found for load_game.")
            return False
        except Exception as e:
            print(f"Error parsing game data from {filename}: {e}")
            import traceback;
            traceback.print_exc()
            return False

    def load_game_into_gameplay(self, filename):
        if self.load_game(filename):
            self.initialized_successfully = True
            self.show_feedback_message("Game Loaded!", self.feedback_message_duration)
            return True
        else:
            self.initialized_successfully = False
            self.show_feedback_message("Load Failed. Returning to Menu.", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_MAIN_MENU
            return False

    def draw_main_menu(self):
        self.screen.fill((40, 40, 60))
        title_surf = self.font_large.render("Hexa Komutanı", True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
        self.screen.blit(title_surf, title_rect)
        button_texts = ["Yeni Oyun", "Oyun Yükle", "Çıkış"]
        button_height = 50
        button_width = 200
        start_y = self.screen_height // 2 - (len(button_texts) * (button_height + 15) - 15) // 2
        self.main_menu_buttons.clear()
        for i, text in enumerate(button_texts):
            button_rect = pygame.Rect(
                (self.screen_width - button_width) // 2,
                start_y + i * (button_height + 15),
                button_width,
                button_height
            )
            self.main_menu_buttons[text] = button_rect
            mouse_pos = pygame.mouse.get_pos()
            button_color = (90, 90, 110) if button_rect.collidepoint(mouse_pos) else (70, 70, 90)
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5)
            pygame.draw.rect(self.screen, (120, 120, 150), button_rect, 3, border_radius=5)
            text_surf = self.font_medium.render(text, True, (220, 220, 255))
            text_rect = text_surf.get_rect(center=button_rect.center)
            self.screen.blit(text_surf, text_rect)
        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            msg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
            self.screen.blit(feedback_surf, msg_rect)
        pygame.display.flip()

    def handle_main_menu_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for button_text, rect in self.main_menu_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        print(f"Main menu button clicked: {button_text}")
                        if button_text == "Yeni Oyun":
                            if self.initialize_gameplay_state(level_to_load=1, is_new_game_session=True):
                                self.current_game_state = GAME_STATE_GAMEPLAY
                        elif button_text == "Oyun Yükle":
                            if self.load_game_into_gameplay(SAVE_FILE_NAME):
                                self.current_game_state = GAME_STATE_GAMEPLAY
                        elif button_text == "Çıkış":
                            self.running = False
                        break

    def run(self):
        if not self.initialized_successfully and self.current_game_state != GAME_STATE_MAIN_MENU:
            print("Game could not be initialized properly. Exiting.")
            if pygame.get_init(): pygame.quit()
            return

        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if self.current_game_state == GAME_STATE_MAIN_MENU:
                for event in events:
                    self.handle_main_menu_input(event)
                if self.feedback_message_timer > 0:
                    self.feedback_message_timer -= 1
                    if self.feedback_message_timer == 0: self.feedback_message = ""
                self.draw_main_menu()

            elif self.current_game_state == GAME_STATE_GAMEPLAY:
                if not self.initialized_successfully:
                    print("Error: Gameplay state entered but not initialized. Returning to main menu.")
                    self.current_game_state = GAME_STATE_MAIN_MENU
                    continue

                for event in events:
                    self.handle_gameplay_events(event)

                if not self.game_over_flag:
                    if self.current_player_id == PLAYER_AI_ID and self.running and not self.ai_turn_processed:
                        self.process_ai_turn()
                    self.update_gameplay()

                self.render_gameplay()

        print("Exiting game loop...")
        if pygame.get_init(): pygame.quit()

    # --- HIGHLIGHT METODLARI ---
    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()  # Sadece hareket için olanı temizle
        if unit and unit.is_alive() and unit.player_id == self.current_player_id:
            self.highlighted_tiles_for_move = unit.get_tiles_in_movement_range(self.game_map)

    def highlight_attackable_tiles(self, unit):
        self.clear_highlighted_attack_tiles()  # Sadece saldırı için olanı temizle
        if unit and unit.is_alive() and unit.player_id == self.current_player_id:
            self.highlighted_tiles_for_attack = unit.get_tiles_in_attack_range(self.game_map)

    def clear_highlighted_tiles(self):  # Sadece hareket için
        self.highlighted_tiles_for_move = []

    def clear_highlighted_attack_tiles(self):  # Sadece saldırı için
        self.highlighted_tiles_for_attack = []

    def clear_all_highlights(self):  # İkisini de temizler
        self.clear_highlighted_tiles()
        self.clear_highlighted_attack_tiles()

    # --- GAMEPLAY İÇİN ÖZEL METODLAR ---
    def handle_gameplay_events(self, event):
        if self.game_over_flag:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.running = False
            return

        if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = event.pos
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
                print("Y key pressed in gameplay, attempting to load game...")
                if self.load_game_into_gameplay(SAVE_FILE_NAME):
                    self.current_game_state = GAME_STATE_GAMEPLAY

            if event.key == pygame.K_ESCAPE:
                if not self.game_over_flag:
                    self.show_feedback_message("Returning to Main Menu...", self.feedback_message_duration // 2)
                    if self.selected_unit:
                        self.selected_unit.set_state(IdleState(self.selected_unit))
                        self.selected_unit = None
                    self.clear_all_highlights()
                    self.current_game_state = GAME_STATE_MAIN_MENU

    def update_gameplay(self):
        if self.feedback_message_timer > 0:
            self.feedback_message_timer -= 1
            if self.feedback_message_timer == 0: self.feedback_message = ""

        if not self.game_over_flag and hasattr(self, 'game_map') and self.game_map:
            for unit in self.game_map.units:
                if unit.is_alive():
                    unit.update(self.dt)

    def render_gameplay(self):
        if not self.initialized_successfully or not hasattr(self, 'game_map') or not self.game_map:
            if self.screen:
                self.screen.fill((50, 0, 0))
                error_surf = self.font_medium.render("GAMEPLAY RENDER ERROR. Map not loaded.", True, (255, 255, 255))
                rect = error_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(error_surf, rect)
                pygame.display.flip()
            return

        self.screen.fill((30, 30, 30))
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
            current_feedback = self.feedback_message
            if "CONGRATULATIONS" in current_feedback:
                level_turn_text_str = "YOU WIN THE GAME!"
            elif "LEVEL CLEARED" in current_feedback:
                level_turn_text_str = f"LEVEL {self.current_level_number - 1 if self.current_level_number > 1 else 1} CLEARED!"
            elif "FAILED" in current_feedback or "AI Wins" in current_feedback:
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number}"
            elif "Draw" in current_feedback:
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number} (Draw)"
            else:
                level_turn_text_str = f"GAME OVER - Level {self.current_level_number}"

        level_turn_surface = self.font_medium.render(level_turn_text_str, True, (255, 255, 255))
        self.screen.blit(level_turn_surface, (10, 10))

        command_text_str = "'E' End Turn | 'K' Save | 'ESC' Menu"
        command_surface = self.font_small.render(command_text_str, True, (255, 255, 255))
        self.screen.blit(command_surface, (self.screen_width - command_surface.get_width() - 10, 10))

        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            msg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            self.screen.blit(feedback_surf, msg_rect)

        pygame.display.flip()

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
                action_command = self.default_ai_strategy.choose_action(ai_unit, self)
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