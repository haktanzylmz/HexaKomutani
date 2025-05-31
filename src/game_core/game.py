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
from .constants import PLAYER_HUMAN_ID, PLAYER_AI_ID
from .ai_strategy import SimpleAggressiveStrategy, DefensiveStrategy


USERS_FILE_NAME_BASE = "users.json"
BASE_SAVE_FILENAME = "savegame.json"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT_DIR = os.path.dirname(SRC_DIR)

LEVELS_DIR = os.path.join(SRC_DIR, "levels")
LEVEL_FILE_PREFIX = os.path.join(LEVELS_DIR, "level")
SAVES_DIR = os.path.join(PROJECT_ROOT_DIR, "saves")
USERS_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, USERS_FILE_NAME_BASE)

MAX_LEVELS = 5
STATE_NAME_TO_CLASS_MAP = {"IdleState": IdleState, "SelectedState": SelectedState}

GAME_STATE_MAIN_MENU = "main_menu"
GAME_STATE_GAMEPLAY = "gameplay"
GAME_STATE_LOGIN = "login_screen"
GAME_STATE_REGISTER = "register_screen"
GAME_STATE_THEME_SELECTION = "theme_selection"
GAME_STATE_SCOREBOARD = "scoreboard_screen"

# --- TEMA TANIMLARI ---
DEFAULT_THEME_COLORS = {
    "name": "Varsayılan", "id": "default",
    # ... (diğer anahtar-değerler aynı kalacak) ...
    "background_main_menu": (40, 40, 60), "button_main_menu_idle": (70, 70, 90),
    "button_main_menu_hover": (90, 90, 110), "button_main_menu_border": (120, 120, 150),
    "text_main_menu_button": (220, 220, 255), "title_main_menu": (200, 200, 255),
    "feedback_text_color": (255, 200, 0), "feedback_bg_color": (20, 20, 20, 200),
    "user_message_loggedin": (180, 255, 180), "user_message_loggedout": (255, 180, 180),
    "tile_walkable_default_color": (200, 200, 200), "tile_obstacle_color": (50, 50, 50),
    "tile_border_color": (0, 0, 0),

    # !!! BİRİM RENKLERİ GÜNCELLENDİ !!!
    "unit_human_piyade_color": (50, 150, 50),  # Yeşil Piyade
    "unit_human_tank_color": (70, 100, 180),  # Mavimsi Tank
    "unit_ai_piyade_color": (200, 50, 50),  # Kırmızı Piyade
    "unit_ai_tank_color": (180, 70, 70),  # Koyu Kırmızı Tank

    "unit_selected_border_color": (255, 255, 0),
    "health_bar_bg": (150, 0, 0), "health_bar_fg": (0, 200, 0),
    "highlight_move": (0, 255, 0, 80), "highlight_attack": (255, 0, 0, 80),
    "gameplay_info_text_color": (230, 230, 230),
    "gameplay_bg": (30, 30, 30),
    # ... (login ekranı renkleri aynı kalacak) ...
    "login_bg": (30, 30, 40), "login_title_color": (200, 220, 255), "login_label_color": (180, 180, 200),
    "login_input_bg_color": (50, 50, 70), "login_input_text_color": (220, 220, 255),
    "login_input_active_border_color": (100, 150, 255), "login_input_inactive_border_color": (80, 80, 100),
    "login_button_primary_idle_color": (0, 120, 40), "login_button_primary_hover_color": (0, 150, 50),
    "login_button_secondary_idle_color": (0, 80, 120), "login_button_secondary_hover_color": (0, 100, 150),
    "login_button_danger_idle_color": (120, 40, 40), "login_button_danger_hover_color": (150, 50, 50),
    "login_button_text_color": (255, 255, 255), "login_link_text_color": (200, 220, 255),
    "unit_human_topcu_color": (100, 100, 0),   # Sarımsı Topçu (İnsan)
    "unit_ai_topcu_color": (150, 150, 50),      # Koyu Sarı Topçu (AI)
    "unit_label_text_color": (255, 255, 255),   # Birim etiketleri için beyaz yazı (arka planları koyu olduğu için)
    "ai_threat_range_color": (128, 0, 128, 70), # Yarı saydam Mor
}

DARK_KNIGHT_THEME_COLORS = {
    "name": "Kara Şövalye", "id": "dark_knight",
    # ... (diğer anahtar-değerler aynı kalacak) ...
    "background_main_menu": (10, 10, 20), "button_main_menu_idle": (30, 30, 50), "button_main_menu_hover": (50, 50, 70),
    "button_main_menu_border": (80, 80, 100), "text_main_menu_button": (180, 180, 200),
    "title_main_menu": (160, 160, 210), "feedback_text_color": (230, 180, 0), "feedback_bg_color": (5, 5, 10, 190),
    "user_message_loggedin": (150, 220, 150), "user_message_loggedout": (220, 150, 150),
    "tile_walkable_default_color": (70, 70, 80), "tile_obstacle_color": (20, 20, 25), "tile_border_color": (40, 40, 50),

    "unit_human_piyade_color": (30, 100, 30),  # Koyu Yeşil Piyade
    "unit_human_tank_color": (50, 70, 120),  # Koyu Mavi Tank
    "unit_ai_piyade_color": (160, 30, 30),  # Koyu Kırmızı Piyade
    "unit_ai_tank_color": (120, 50, 50),  # Daha Koyu Kırmızı Tank

    "unit_selected_border_color": (200, 200, 0), "health_bar_bg": (100, 0, 0), "health_bar_fg": (0, 150, 0),
    "highlight_move": (0, 180, 0, 70), "highlight_attack": (180, 0, 0, 70), "gameplay_info_text_color": (210, 210, 210),
    "gameplay_bg": (10, 10, 15), "login_bg": (15, 15, 25), "login_title_color": (180, 200, 230),
    "login_label_color": (160, 160, 180), "login_input_bg_color": (30, 30, 50),
    "login_input_text_color": (200, 200, 220), "login_input_active_border_color": (80, 120, 200),
    "login_input_inactive_border_color": (60, 60, 80), "login_button_primary_idle_color": (0, 100, 30),
    "login_button_primary_hover_color": (0, 130, 40), "login_button_secondary_idle_color": (0, 70, 100),
    "login_button_secondary_hover_color": (0, 90, 130), "login_button_danger_idle_color": (100, 30, 30),
    "login_button_danger_hover_color": (130, 40, 40), "login_button_text_color": (230, 230, 230),
    "login_link_text_color": (180, 200, 230),
    "unit_human_topcu_color": (80, 80, 0),      # Koyu Sarımsı Topçu (İnsan)
    "unit_ai_topcu_color": (100, 100, 40),      # Daha Koyu Sarı Topçu (AI)
    "unit_label_text_color": (200, 200, 200),   # Açık gri yazı
    "ai_threat_range_color": (100, 0, 100, 70), # Koyu Mor
}

FOREST_GUARDIAN_THEME_COLORS = {
    "name": "Orman Muhafızı", "id": "forest_guardian",
    # ... (diğer anahtar-değerler aynı kalacak) ...
    "background_main_menu": (30, 60, 40), "button_main_menu_idle": (50, 90, 60),
    "button_main_menu_hover": (70, 110, 80), "button_main_menu_border": (90, 130, 100),
    "text_main_menu_button": (210, 230, 200), "title_main_menu": (190, 220, 180),
    "feedback_text_color": (255, 220, 100), "feedback_bg_color": (20, 40, 30, 200),
    "user_message_loggedin": (190, 240, 190), "user_message_loggedout": (240, 190, 190),
    "tile_walkable_default_color": (100, 150, 90), "tile_obstacle_color": (40, 70, 50),
    "tile_border_color": (20, 50, 30),

    "unit_human_piyade_color": (60, 160, 70),  # Orman Yeşili Piyade
    "unit_human_tank_color": (70, 120, 80),  # Haki Tank
    "unit_ai_piyade_color": (180, 80, 50),  # Turuncumsu Kırmızı Piyade
    "unit_ai_tank_color": (150, 60, 40),  # Koyu Turuncu Tank

    "unit_selected_border_color": (230, 230, 50), "health_bar_bg": (130, 50, 30), "health_bar_fg": (80, 180, 60),
    "highlight_move": (50, 255, 50, 80), "highlight_attack": (255, 80, 30, 80),
    "gameplay_info_text_color": (210, 220, 200), "gameplay_bg": (20, 50, 30), "login_bg": (20, 50, 30),
    "login_title_color": (180, 210, 170), "login_label_color": (170, 200, 160), "login_input_bg_color": (40, 70, 50),
    "login_input_text_color": (210, 230, 200), "login_input_active_border_color": (80, 180, 100),
    "login_input_inactive_border_color": (60, 100, 70), "login_button_primary_idle_color": (30, 110, 50),
    "login_button_primary_hover_color": (40, 140, 60), "login_button_secondary_idle_color": (30, 90, 110),
    "login_button_secondary_hover_color": (40, 110, 140), "login_button_danger_idle_color": (110, 60, 40),
    "login_button_danger_hover_color": (140, 70, 50), "login_button_text_color": (230, 240, 220),
    "login_link_text_color": (190, 210, 180),
    "unit_human_topcu_color": (120, 120, 50),  # Haki Sarı Topçu (İnsan)
    "unit_ai_topcu_color": (140, 140, 70),  # Daha Koyu Haki Sarı Topçu (AI)
    "unit_label_text_color": (230, 230, 180),  # Krem rengi yazı
    "ai_threat_range_color": (150, 50, 150, 70), # Açık Morumsu
}

ALL_THEMES = {  # Bu sözlük zaten vardı, içeriği yukarıdaki gibi olacak
    "default": DEFAULT_THEME_COLORS,
    "dark_knight": DARK_KNIGHT_THEME_COLORS,
    "forest_guardian": FOREST_GUARDIAN_THEME_COLORS
}


# --- TEMA TANIMLARI SONU ---

class Game:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width;
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height));
        self.unit_factory = UnitFactory()
        self.ai_strategies = {
            "SimpleAggressiveStrategy": SimpleAggressiveStrategy(),
            "DefensiveStrategy": DefensiveStrategy()  # !!! YENİ STRATEJİ EKLENDİ !!!
        }
        self.default_ai_strategy = self.ai_strategies["SimpleAggressiveStrategy"]
        pygame.display.set_caption("Hexa Komutanı")
        try:
            self.font_small = pygame.font.SysFont(None, 24); self.font_medium = pygame.font.SysFont(None,
                                                                                                    30); self.font_large = pygame.font.SysFont(
                None, 50)
        except:
            self.font_small = pygame.font.Font(None, 24); self.font_medium = pygame.font.Font(None,
                                                                                              30); self.font_large = pygame.font.Font(
                None, 50)
        self.clock = pygame.time.Clock();
        self.running = False;
        self.current_game_state = GAME_STATE_MAIN_MENU
        self.selected_unit = None;
        self.command_history = [];
        self.highlighted_tiles_for_move = [];
        self.highlighted_tiles_for_attack = []
        self.feedback_message = "";
        self.feedback_message_timer = 0;
        self.feedback_message_duration = 120
        self.game_over_flag = False;
        self.current_level_number = 1;
        self.turns_taken_this_level = 0
        self.tile_size = 40;
        self.initialized_successfully = False
        self.unit_factory = UnitFactory()
        self.ai_strategies = {
            "SimpleAggressiveStrategy": SimpleAggressiveStrategy(),
            "DefensiveStrategy": DefensiveStrategy()
        }
        self.default_ai_strategy = self.ai_strategies["SimpleAggressiveStrategy"]
        self.main_menu_buttons = {};
        self.login_screen_elements = {};
        self.register_screen_elements = {}
        self.theme_selection_elements = {};
        self.scoreboard_elements = {}
        self.active_input_field = None;
        self.input_texts = {key: "" for key in ["username_login", "password_login", "username_reg", "password_reg",
                                                "password_confirm_reg"]}
        self.current_user = None;
        self.available_themes = ALL_THEMES;
        self.active_theme_name = "default";
        self.active_theme = self.available_themes[self.active_theme_name]
        self.game_map = None;
        self.map_cols = 0;
        self.map_rows = 0;
        self.current_player_id = PLAYER_HUMAN_ID;
        self.ai_turn_processed_this_round = False
        self.ai_threat_tiles = set()  #  AI tarafından tehdit edilen (x,y) koordinatlarını tutacak set !!!
        self.show_ai_threat_display = False  # Bu gösterimin aktif olup olmadığını tutan bayrak !!!
        self._ensure_data_dirs_exist();
        self.load_user_preferences()

    def _ensure_data_dirs_exist(self):
        user_file_dir = os.path.dirname(USERS_FILE_NAME)
        if user_file_dir and not os.path.exists(user_file_dir):  # Ana dizinse bu zaten true olur
            try:
                os.makedirs(user_file_dir, exist_ok=True)
            except OSError as e:
                print(f"Error creating dir for '{USERS_FILE_NAME}':{e}")
        if not os.path.exists(USERS_FILE_NAME):
            try:
                with open(USERS_FILE_NAME, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"'{USERS_FILE_NAME}' created at:{os.path.abspath(USERS_FILE_NAME)}")
            except IOError as e:
                print(f"Error creating '{USERS_FILE_NAME}':{e}")
        if not os.path.exists(SAVES_DIR):
            try:
                os.makedirs(SAVES_DIR, exist_ok=True);print(f"Saves directory '{SAVES_DIR}' created.")
            except OSError as e:
                print(f"Error creating saves directory '{SAVES_DIR}':{e}")

    def _get_user_save_filename(self):
        if self.current_user: safe_username = "".join(
            c if c.isalnum() else "_" for c in self.current_user);return os.path.join(SAVES_DIR,
                                                                                      f"{safe_username.lower()}_{BASE_SAVE_FILENAME}")
        return None

    def _load_users(self):
        self._ensure_data_dirs_exist()
        try:
            with open(USERS_FILE_NAME, 'r', encoding='utf-8') as f:
                ud = json.load(f)
            if not isinstance(ud, dict): return {}
            return ud
        except(FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_users(self, users_data):
        try:
            with open(USERS_FILE_NAME, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

    def set_active_theme(self, theme_id):
        if theme_id in self.available_themes:
            self.active_theme_name = theme_id;
            self.active_theme = self.available_themes[theme_id]
            tdn = self.active_theme.get('name', theme_id)
            print(f"Tema '{tdn}' olarak değiştirildi.")
            self.show_feedback_message(f"Tema: {tdn}", self.feedback_message_duration // 2)
            if self.current_user:
                users = self._load_users();
                udo = users.get(self.current_user)
                if isinstance(udo, dict):
                    udo["theme"] = theme_id
                elif isinstance(udo, str):
                    users[self.current_user] = {"password": udo, "theme": theme_id, "scores": {}}
                else:
                    users[self.current_user] = {"password": "", "theme": theme_id, "scores": {}}
                self._save_users(users)
            if self.current_game_state == GAME_STATE_GAMEPLAY and self.initialized_successfully: self.apply_theme_to_game_elements()
        else:
            print(f"Uyarı: Tema ID '{theme_id}' bulunamadı. Varsayılan.");
            if self.active_theme_name != "default": self.active_theme_name = "default";self.active_theme = \
            self.available_themes["default"]

    def load_user_preferences(self):
        ttl = "default"
        if self.current_user:
            users = self._load_users();
            ud = users.get(self.current_user)
            if isinstance(ud, dict): ttl = ud.get("theme", "default")
        self.set_active_theme(ttl)

    def apply_theme_to_game_elements(self):
        if hasattr(self, 'game_map') and self.game_map and self.game_map.grid:
            print("Applying theme to game elements (draw methods use active_theme directly)...")
            pass

    def initialize_gameplay_state(self, level_to_load=1, is_new_game_session=True):
        print(f"Initializing gameplay state for level {level_to_load}, new session: {is_new_game_session}")
        self.selected_unit = None;
        self.command_history = []
        self.highlighted_tiles_for_move = [];
        self.highlighted_tiles_for_attack = []
        self.current_level_number = level_to_load;
        self.turns_taken_this_level = 0
        if self._initialize_game_for_level(self.current_level_number, is_new_game_session=is_new_game_session):
            self.initialized_successfully = True;
            self.apply_theme_to_game_elements();
            return True
        else:
            self.initialized_successfully = False;self.show_feedback_message("Failed to initialize gameplay.",
                                                                             self.feedback_message_duration);return False

    def _initialize_game_for_level(self, level_number, is_new_game_session=False):
        self.current_level_number = level_number;
        ld = self.load_level_data(level_number)
        if not ld: print(f"Could not load level {level_number} data. Init aborted.");return False
        self.map_cols = ld.get("map_cols", self.screen_width // self.tile_size);
        self.map_rows = ld.get("map_rows", self.screen_height // self.tile_size)
        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size);
        self.game_map.create_grid()
        self.current_player_id = PLAYER_HUMAN_ID;
        self.game_map.units = []
        self.selected_unit = None;
        self.clear_all_highlights()
        if is_new_game_session: Unit._id_counter = 0
        self.setup_units_from_level_data(ld)
        self.game_over_flag = False;
        self.reset_unit_actions_for_player(self.current_player_id)
        ln = ld.get('level_name', f'Lvl {level_number}')
        print(f"Level {level_number} ('{ln}') initialized.");
        self.show_feedback_message(f"Level {level_number}: {ln}", self.feedback_message_duration)
        return True

    def reset_unit_actions_for_player(self, player_id):  # !!! METOD TANIMI BURADA !!!
        if hasattr(self, 'game_map') and self.game_map and self.game_map.units:
            for unit in self.game_map.units:
                if unit.player_id == player_id: unit.has_acted_this_turn = False
        if player_id == PLAYER_AI_ID: self.ai_turn_processed_this_round = False

    def load_level_data(self, level_number):
        fn = f"{LEVEL_FILE_PREFIX}{level_number}.json"
        try:
            with open(fn, 'r', encoding='utf-8') as f:
                ld = json.load(f)
            return ld
        except FileNotFoundError:
            self.show_feedback_message(f"Lvl File Not Found: lvl{level_number}.json", 9999);return None
        except Exception:
            self.show_feedback_message(f"Error Loading Lvl {level_number}!", 9999);return None

    def setup_units_from_level_data(self, level_data):
        if "player_units" in level_data:
            for unit_info in level_data["player_units"]:
                # JSON'dan "grid_pos" listesini oku
                grid_x = unit_info["grid_pos"][0]
                grid_y = unit_info["grid_pos"][1]
                player_id = unit_info["player_id"]
                unit_type = unit_info["type"]

                unit = self.unit_factory.create_unit(
                    unit_type,
                    grid_x,
                    grid_y,
                    player_id
                )
                if unit:  # Birim başarıyla oluşturulduysa haritaya ekle
                    self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)
                else:
                    print(f"Error: Could not create player unit from info: {unit_info}")

        if "ai_units" in level_data:
            for unit_info in level_data["ai_units"]:
                # JSON'dan "grid_pos" listesini oku
                grid_x = unit_info["grid_pos"][0]
                grid_y = unit_info["grid_pos"][1]
                player_id = unit_info["player_id"]
                unit_type = unit_info["type"]

                unit = self.unit_factory.create_unit(
                    unit_type,
                    grid_x,
                    grid_y,
                    player_id
                )
                if unit:
                    if unit.player_id == PLAYER_AI_ID:  # Sadece AI birimleri için strateji ata
                        strategy_id = unit_info.get("strategy_id", "SimpleAggressiveStrategy")  # Varsayılan strateji
                        unit.ai_strategy_instance = self.ai_strategies.get(strategy_id, self.default_ai_strategy)
                        if not unit.ai_strategy_instance:
                            print(f"Warning: Unknown strategy_id '{strategy_id}' for AI unit. Using default.")
                            unit.ai_strategy_instance = self.default_ai_strategy
                        # print(f"DEBUG: AI Unit ID {unit.id} (Player {unit.player_id}) created with strategy: {unit.ai_strategy_instance.__class__.__name__}") # Bu log zaten var
                    self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)
                else:
                    print(f"Error: Could not create AI unit from info: {unit_info}")

    def show_feedback_message(self, message, duration_frames):
        self.feedback_message = message;
        self.feedback_message_timer = duration_frames

    def save_game(self):
        if not self.current_user: self.show_feedback_message("Kaydetmek için giriş yapmalısınız!",
                                                             self.feedback_message_duration);return
        if not self.initialized_successfully or not self.game_map: self.show_feedback_message(
            "Cannot save: Gameplay not active.", self.feedback_message_duration);return
        usf = self._get_user_save_filename()
        if not usf: print("Error: Could not determine user save file for saving.");return
        print(f"Saving game to {usf} for user {self.current_user}...")
        if self.selected_unit: self.selected_unit.is_graphically_selected = False
        gsd = {"user": self.current_user, "current_player_id": self.current_player_id,
               "current_level_number": self.current_level_number, "map_data": self.game_map.to_dict(),
               "units_data": [u.to_dict() for u in self.game_map.units if u.is_alive()],
               "next_unit_id": Unit._id_counter, "game_over_flag": self.game_over_flag,
               "ai_turn_processed_this_round": self.ai_turn_processed_this_round,
               "active_theme_name": self.active_theme_name, "turns_taken_this_level": self.turns_taken_this_level}
        try:
            with open(usf, 'w', encoding='utf-8') as f:
                json.dump(gsd, f, indent=4, ensure_ascii=False)
            self.show_feedback_message(f"Game Saved for {self.current_user}!", self.feedback_message_duration)
        except IOError as e:
            print(f"Error saving game:{e}");self.show_feedback_message("Error Saving Game!",
                                                                       self.feedback_message_duration)

    def load_game(self):
        user_save_file = self._get_user_save_filename()
        if not user_save_file: return False
        if not os.path.exists(user_save_file): return False
        print(f"Attempting to load game data from {user_save_file} for user {self.current_user}...")
        try:
            with open(user_save_file, 'r', encoding='utf-8') as f:
                game_state_data = json.load(f)
            self.command_history = []
            loaded_theme_name = game_state_data.get("active_theme_name", "default")
            self.set_active_theme(loaded_theme_name)
            self.current_level_number = game_state_data.get("current_level_number", 1)
            self.turns_taken_this_level = game_state_data.get("turns_taken_this_level", 0)
            map_info = game_state_data["map_data"]
            self.map_rows = map_info["rows"];
            self.map_cols = map_info["cols"]
            self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
            self.game_map.grid = []
            for r_idx, row_data in enumerate(map_info["grid_tiles"]):
                current_row = [];
                self.game_map.grid.append(current_row)
                for c_idx, tile_data in enumerate(row_data): current_row.append(
                    Tile.from_dict(tile_data, self.tile_size))
            self.game_map.units = []
            Unit._id_counter = game_state_data.get("next_unit_id", Unit._id_counter)
            for unit_data in game_state_data["units_data"]:
                unit = self.unit_factory.create_unit(unit_data["unit_type"], unit_data["grid_x"], unit_data["grid_y"],
                                                     unit_data["player_id"])
                unit.id = unit_data["id"];
                unit.grid_x = unit_data["grid_x"];
                unit.grid_y = unit_data["grid_y"]
                unit.health = unit_data["health"];
                unit.max_health = unit_data.get("max_health", unit.max_health)
                unit.attack_power = unit_data.get("attack_power", unit.attack_power);
                unit.movement_range = unit_data.get("movement_range", unit.movement_range)
                unit.attack_range = unit_data.get("attack_range", unit.attack_range);
                unit.has_acted_this_turn = unit_data.get("has_acted_this_turn", False)
                state_name = unit_data.get("current_state_name", "IdleState");
                state_class = STATE_NAME_TO_CLASS_MAP.get(state_name, IdleState)
                unit.set_state(state_class(unit), self);
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)
            self.current_player_id = game_state_data["current_player_id"];
            self.game_over_flag = game_state_data.get("game_over_flag", False)
            self.ai_turn_processed_this_round = game_state_data.get("ai_turn_processed_this_round", (
                        self.current_player_id == PLAYER_AI_ID and not self.game_over_flag))
            self.selected_unit = None;
            self.clear_all_highlights()
            if not self.game_over_flag: self.reset_unit_actions_for_player(self.current_player_id)
            self.apply_theme_to_game_elements()
            print("Game data parsed successfully for loading!");
            return True
        except FileNotFoundError:
            print(f"Save file '{user_save_file}' not found."); return False
        except Exception as e:
            print(f"Error parsing game data from {user_save_file}: {e}"); import \
                traceback; traceback.print_exc(); return False

    def load_game_into_gameplay(self):
        if not self.current_user:
            self.show_feedback_message("Lütfen önce giriş yapın!", self.feedback_message_duration);
            self.current_game_state = GAME_STATE_LOGIN
            self.active_input_field = "username_login";
            self.clear_input_fields();
            return False
        user_save_file = self._get_user_save_filename()
        if not user_save_file or not os.path.exists(user_save_file):
            self.show_feedback_message(f"{self.current_user} için kayıtlı oyun yok.", self.feedback_message_duration);
            return False
        if self.load_game():
            self.initialized_successfully = True;
            self.show_feedback_message(f"Game Loaded for {self.current_user}!", self.feedback_message_duration);
            return True
        else:
            self.initialized_successfully = False;
            self.show_feedback_message("Load Failed. Returning to Menu.", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_MAIN_MENU;
            return False

    def draw_main_menu(self):
        self.screen.fill(self.active_theme.get("background_main_menu", (40, 40, 60)));
        ts = self.font_large.render("Hexa Komutanı", 1, self.active_theme.get("title_main_menu", (200, 200, 255)));
        tr = ts.get_rect(center=(self.screen_width // 2, self.screen_height // 5));
        self.screen.blit(ts, tr);
        um = f"Giriş Yapıldı: {self.current_user}" if self.current_user else "Giriş Yapılmadı";
        uck = "user_message_loggedin" if self.current_user else "user_message_loggedout";
        uc = self.active_theme.get(uck, (255, 255, 255));
        us = self.font_small.render(um, 1, uc);
        ur = us.get_rect(center=(self.screen_width // 2, tr.bottom + 25));
        self.screen.blit(us, ur);
        bts = ["Yeni Oyun", "Oyun Yükle"];
        bts.append("Çıkış Yap" if self.current_user else "Giriş / Kayıt");
        bts.append("Temalar");
        bts.append("Skor Tablosu");
        bts.append("Oyundan Çık")
        bh = 40;
        bw = 230;
        sy = ur.bottom + 25;
        self.main_menu_buttons.clear()
        for i, t in enumerate(bts):
            by = sy + i * (bh + 10);
            b_rect = pygame.Rect((self.screen_width - bw) // 2, by, bw, bh);
            self.main_menu_buttons[t] = b_rect;
            mp = pygame.mouse.get_pos();
            ic = self.active_theme.get("button_main_menu_idle");
            hc = self.active_theme.get("button_main_menu_hover");
            bc = self.active_theme.get("button_main_menu_border");
            trc = self.active_theme.get("text_main_menu_button");
            cc = hc if b_rect.collidepoint(mp) else ic;
            pygame.draw.rect(self.screen, cc, b_rect, 0, 5);
            pygame.draw.rect(self.screen, bc, b_rect, 3, 5);
            ts_b = self.font_medium.render(t, 1, trc);
            txtr_b = ts_b.get_rect(center=b_rect.center);
            self.screen.blit(ts_b, txtr_b)
        if self.feedback_message_timer > 0 and self.feedback_message: fbs = self.font_medium.render(
            self.feedback_message, 1, self.active_theme.get("feedback_text_color"));bgr = fbs.get_rect(
            center=(self.screen_width // 2, self.screen_height - 40));bgr.inflate_ip(20, 10);bgs = pygame.Surface(
            bgr.size, pygame.SRCALPHA);bgs.fill(self.active_theme.get("feedback_bg_color"));self.screen.blit(bgs,
                                                                                                             bgr.topleft);self.screen.blit(
            fbs, fbs.get_rect(center=bgr.center));
        pygame.display.flip()

    def handle_main_menu_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for bt, rect in self.main_menu_buttons.items():
                if rect.collidepoint(mp):
                    print(f"Main menu button clicked:{bt}")
                    if bt == "Yeni Oyun":
                        if not self.current_user: self.show_feedback_message("Yeni oyun için giriş yapın.",
                                                                             self.feedback_message_duration);self.current_game_state = GAME_STATE_LOGIN;self.active_input_field = "username_login";self.clear_input_fields();return
                        if self.initialize_gameplay_state(1, True): self.current_game_state = GAME_STATE_GAMEPLAY
                    elif bt == "Oyun Yükle":
                        if self.load_game_into_gameplay(): self.current_game_state = GAME_STATE_GAMEPLAY
                    elif bt == "Giriş / Kayıt":
                        self.current_game_state = GAME_STATE_LOGIN;self.active_input_field = "username_login";self.clear_input_fields();self.show_feedback_message(
                            "Giriş Yapın veya Kayıt Olun", self.feedback_message_duration)
                    elif bt == "Çıkış Yap":
                        self.show_feedback_message(f"{self.current_user} çıkış yaptı.",
                                                   self.feedback_message_duration);self.current_user = None;self.set_active_theme(
                            "default")
                    elif bt == "Temalar":
                        self.current_game_state = GAME_STATE_THEME_SELECTION;self.show_feedback_message(
                            "Bir tema seçin", self.feedback_message_duration)
                    elif bt == "Skor Tablosu":
                        self.current_game_state = GAME_STATE_SCOREBOARD;self.show_feedback_message("", 0)
                    elif bt == "Oyundan Çık":
                        self.running = False
                    break

    def clear_input_fields(self):
        self.input_texts = {key: "" for key in self.input_texts};
        self.active_input_field = None

    def draw_login_screen(self):
        theme = self.active_theme;
        self.screen.fill(theme.get("login_bg", (30, 30, 40)));
        ts = self.font_large.render("Giriş Yap", 1, theme.get("login_title_color", (200, 220, 255)));
        tr = ts.get_rect(center=(self.screen_width // 2, self.screen_height // 5));
        self.screen.blit(ts, tr);
        iw = 300;
        ih = 35;
        fs = 15;
        lc = theme.get("login_label_color");
        ibg = theme.get("login_input_bg_color");
        tc = theme.get("login_input_text_color");
        ab = theme.get("login_input_active_border_color");
        ib = theme.get("login_input_inactive_border_color");
        cy = self.screen_height // 2 - ih - fs - 10;
        uls = self.font_small.render("Kullanıcı Adı:", 1, lc);
        self.screen.blit(uls, ((self.screen_width - iw) // 2, cy - 20));
        ur = pygame.Rect((self.screen_width - iw) // 2, cy, iw, ih);
        self.login_screen_elements["username_input"] = ur;
        pygame.draw.rect(self.screen, ibg, ur, 0, 3);
        pygame.draw.rect(self.screen, ab if self.active_input_field == "username_login" else ib, ur, 2, 3);
        uts = self.font_medium.render(self.input_texts["username_login"], 1, tc);
        self.screen.blit(uts, (ur.x + 8, ur.y + (ih - uts.get_height()) // 2));
        cy += ih + fs * 2;
        pls = self.font_small.render("Şifre:", 1, lc);
        self.screen.blit(pls, ((self.screen_width - iw) // 2, cy - 20));
        pr = pygame.Rect((self.screen_width - iw) // 2, cy, iw, ih);
        self.login_screen_elements["password_input"] = pr;
        pygame.draw.rect(self.screen, ibg, pr, 0, 3);
        pygame.draw.rect(self.screen, ab if self.active_input_field == "password_login" else ib, pr, 2, 3);
        pd = "*" * len(self.input_texts["password_login"]);
        pts = self.font_medium.render(pd, 1, tc);
        self.screen.blit(pts, (pr.x + 8, pr.y + (ih - pts.get_height()) // 2));
        cy += ih + fs * 2 + 10;
        bw = 140;
        bh = 40;
        bs = 20;
        mph = pygame.mouse.get_pos();
        lbr = pygame.Rect(self.screen_width // 2 - bw - bs // 2, cy, bw, bh);
        self.login_screen_elements["login_button"] = lbr;
        pygame.draw.rect(self.screen,
                         theme.get("login_button_primary_hover_color") if lbr.collidepoint(mph) else theme.get(
                             "login_button_primary_idle_color"), lbr, 0, 5);
        lts = self.font_medium.render("Giriş Yap", 1, theme.get("login_button_text_color"));
        self.screen.blit(lts, lts.get_rect(center=lbr.center));
        rlr = pygame.Rect(self.screen_width // 2 + bs // 2, cy, bw, bh);
        self.login_screen_elements["register_link_button"] = rlr;
        pygame.draw.rect(self.screen,
                         theme.get("login_button_secondary_hover_color") if rlr.collidepoint(mph) else theme.get(
                             "login_button_secondary_idle_color"), rlr, 0, 5);
        rts = self.font_medium.render("Kayıt Ol", 1, theme.get("login_link_text_color"));
        self.screen.blit(rts, rts.get_rect(center=rlr.center));
        cy += bh + 15;
        bbr = pygame.Rect((self.screen_width - (bw * 1.5)) // 2, cy, bw * 1.5, bh);
        self.login_screen_elements["back_button_login"] = bbr;
        pygame.draw.rect(self.screen,
                         theme.get("login_button_danger_hover_color") if bbr.collidepoint(mph) else theme.get(
                             "login_button_danger_idle_color"), bbr, 0, 5);
        bts = self.font_medium.render("Ana Menüye Dön", 1, theme.get("login_button_text_color"));
        self.screen.blit(bts, bts.get_rect(center=bbr.center));
        if self.feedback_message_timer > 0 and self.feedback_message: fbs = self.font_medium.render(
            self.feedback_message, 1, self.active_theme.get("feedback_text_color"));bgr = fbs.get_rect(
            center=(self.screen_width // 2, self.screen_height - 40));bgr.inflate_ip(20, 10);bgs = pygame.Surface(
            bgr.size, pygame.SRCALPHA);bgs.fill(self.active_theme.get("feedback_bg_color"));self.screen.blit(bgs,
                                                                                                             bgr.topleft);self.screen.blit(
            fbs, fbs.get_rect(center=bgr.center));
        pygame.display.flip()

    def handle_login_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            if self.login_screen_elements.get("username_input") and self.login_screen_elements[
                "username_input"].collidepoint(mp):
                self.active_input_field = "username_login"
            elif self.login_screen_elements.get("password_input") and self.login_screen_elements[
                "password_input"].collidepoint(mp):
                self.active_input_field = "password_login"
            elif self.login_screen_elements.get("login_button") and self.login_screen_elements[
                "login_button"].collidepoint(mp):
                self.attempt_login()
            elif self.login_screen_elements.get("register_link_button") and self.login_screen_elements[
                "register_link_button"].collidepoint(mp):
                self.current_game_state = GAME_STATE_REGISTER;self.active_input_field = "username_reg";self.clear_input_fields();self.show_feedback_message(
                    "Yeni Kullanıcı Kaydı", self.feedback_message_duration)
            elif self.login_screen_elements.get("back_button_login") and self.login_screen_elements[
                "back_button_login"].collidepoint(mp):
                self.current_game_state = GAME_STATE_MAIN_MENU;self.clear_input_fields()
            else:
                self.active_input_field = None
        if event.type == pygame.KEYDOWN:
            if self.active_input_field and self.active_input_field in self.input_texts:
                if event.key == pygame.K_BACKSPACE:
                    self.input_texts[self.active_input_field] = self.input_texts[self.active_input_field][:-1]
                elif event.key == pygame.K_TAB:
                    if self.active_input_field == "username_login":
                        self.active_input_field = "password_login"
                    elif self.active_input_field == "password_login":
                        self.active_input_field = "username_login"
                elif event.key == pygame.K_RETURN:
                    if self.active_input_field == "password_login":
                        self.attempt_login()
                    elif self.active_input_field == "username_login":
                        self.active_input_field = "password_login"
                elif len(self.input_texts[self.active_input_field]) < 20 and (
                        event.unicode.isalnum() or event.unicode in ['.', '_', '-']):
                    self.input_texts[self.active_input_field] += event.unicode
            if event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_MAIN_MENU;self.clear_input_fields()

    def attempt_login(self):
        un = self.input_texts["username_login"].strip();
        pw = self.input_texts["password_login"]
        if not un or not pw: self.show_feedback_message("Kullanıcı adı ve şifre giriniz!",
                                                        self.feedback_message_duration);return
        users = self._load_users();
        udo = users.get(un);
        ls = False
        if udo and isinstance(udo, dict) and udo.get("password") == pw:
            ls = True
        elif udo and isinstance(udo, str) and udo == pw:
            ls = True;users[un] = {"password": pw, "theme": "default", "scores": {}};self._save_users(users)
        if ls:
            self.current_user = un;self.show_feedback_message(f"Hoşgeldin, {self.current_user}!",
                                                              self.feedback_message_duration);self.load_user_preferences();self.current_game_state = GAME_STATE_MAIN_MENU;self.clear_input_fields()
        else:
            self.show_feedback_message("Hatalı kullanıcı adı veya şifre!", self.feedback_message_duration);
            self.input_texts["password_login"] = ""

    def draw_register_screen(self):
        theme = self.active_theme;
        self.screen.fill(theme.get("login_bg", (50, 40, 60)));
        ts = self.font_large.render("Kayıt Ol", True, theme.get("login_title_color", (220, 200, 255)));
        tr = ts.get_rect(center=(self.screen_width // 2, self.screen_height // 6));
        self.screen.blit(ts, tr);
        iw = 300;
        ih = 35;
        fs = 10;
        lc = theme.get("login_label_color");
        ibg = theme.get("login_input_bg_color");
        tc = theme.get("login_input_text_color");
        ab = theme.get("login_input_active_border_color");
        ib = theme.get("login_input_inactive_border_color");
        bpi = theme.get("login_button_primary_idle_color");
        bph = theme.get("login_button_primary_hover_color");
        bsi = theme.get("login_button_secondary_idle_color");
        bsh = theme.get("login_button_secondary_hover_color");
        bdi = theme.get("login_button_danger_idle_color");
        bdh = theme.get("login_button_danger_hover_color");
        btc = theme.get("login_button_text_color");
        ltc = theme.get("login_link_text_color");
        cy = tr.bottom + 30;
        uls = self.font_small.render("Yeni Kullanıcı Adı:", 1, lc);
        self.screen.blit(uls, ((self.screen_width - iw) // 2, cy - 20));
        urr = pygame.Rect((self.screen_width - iw) // 2, cy, iw, ih);
        self.register_screen_elements["username_input_reg"] = urr;
        pygame.draw.rect(self.screen, ibg, urr, 0, 3);
        pygame.draw.rect(self.screen, ab if self.active_input_field == "username_reg" else ib, urr, 2, 3);
        urts = self.font_medium.render(self.input_texts["username_reg"], 1, tc);
        self.screen.blit(urts, (urr.x + 8, urr.y + (ih - urts.get_height()) // 2));
        cy += ih + fs * 2;
        prls = self.font_small.render("Şifre:", 1, lc);
        self.screen.blit(prls, ((self.screen_width - iw) // 2, cy - 20));
        prr = pygame.Rect((self.screen_width - iw) // 2, cy, iw, ih);
        self.register_screen_elements["password_input_reg"] = prr;
        pygame.draw.rect(self.screen, ibg, prr, 0, 3);
        pygame.draw.rect(self.screen, ab if self.active_input_field == "password_reg" else ib, prr, 2, 3);
        prd = "*" * len(self.input_texts["password_reg"]);
        prts = self.font_medium.render(prd, 1, tc);
        self.screen.blit(prts, (prr.x + 8, prr.y + (ih - prts.get_height()) // 2));
        cy += ih + fs * 2;
        pcls = self.font_small.render("Şifre Tekrar:", 1, lc);
        self.screen.blit(pcls, ((self.screen_width - iw) // 2, cy - 20));
        pcr = pygame.Rect((self.screen_width - iw) // 2, cy, iw, ih);
        self.register_screen_elements["password_input_confirm_reg"] = pcr;
        pygame.draw.rect(self.screen, ibg, pcr, 0, 3);
        pygame.draw.rect(self.screen, ab if self.active_input_field == "password_confirm_reg" else ib, pcr, 2, 3);
        pcd = "*" * len(self.input_texts["password_confirm_reg"]);
        pcts = self.font_medium.render(pcd, 1, tc);
        self.screen.blit(pcts, (pcr.x + 8, pcr.y + (ih - pcts.get_height()) // 2));
        cy += ih + fs * 2 + 10;
        bw = 140;
        bh = 40;
        bs = 20;
        mph = pygame.mouse.get_pos();
        rbr = pygame.Rect(self.screen_width // 2 - bw - bs // 2, cy, bw, bh);
        self.register_screen_elements["register_button"] = rbr;
        pygame.draw.rect(self.screen, bph if rbr.collidepoint(mph) else bpi, rbr, 0, 5);
        rbts = self.font_medium.render("Kayıt Ol", 1, btc);
        self.screen.blit(rbts, rbts.get_rect(center=rbr.center));
        llr = pygame.Rect(self.screen_width // 2 + bs // 2, cy, bw, bh);
        self.register_screen_elements["login_link_button_reg"] = llr;
        pygame.draw.rect(self.screen, bsh if llr.collidepoint(mph) else bsi, llr, 0, 5);
        llts = self.font_medium.render("Giriş Yap", 1, ltc);
        self.screen.blit(llts, llts.get_rect(center=llr.center));
        cy += bh + 15;
        bbmr = pygame.Rect((self.screen_width - (bw * 1.5)) // 2, cy, bw * 1.5, bh);
        self.register_screen_elements["back_button_menu_reg"] = bbmr;
        pygame.draw.rect(self.screen, bdh if bbmr.collidepoint(mph) else bdi, bbmr, 0, 5);
        bmts = self.font_medium.render("Ana Menüye Dön", 1,
                                       theme.get("login_button_text_color_danger", (255, 200, 200)));
        self.screen.blit(bmts, bmts.get_rect(center=bbmr.center));
        if self.feedback_message_timer > 0 and self.feedback_message: fbs = self.font_medium.render(
            self.feedback_message, 1, self.active_theme.get("feedback_text_color"));bgr = fbs.get_rect(
            center=(self.screen_width // 2, self.screen_height - 40));bgr.inflate_ip(20, 10);bgs = pygame.Surface(
            bgr.size, pygame.SRCALPHA);bgs.fill(self.active_theme.get("feedback_bg_color"));self.screen.blit(bgs,
                                                                                                             bgr.topleft);self.screen.blit(
            fbs, fbs.get_rect(center=bgr.center));
        pygame.display.flip()

    def handle_register_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            if self.register_screen_elements.get("username_input_reg") and self.register_screen_elements[
                "username_input_reg"].collidepoint(mp):
                self.active_input_field = "username_reg"
            elif self.register_screen_elements.get("password_input_reg") and self.register_screen_elements[
                "password_input_reg"].collidepoint(mp):
                self.active_input_field = "password_reg"
            elif self.register_screen_elements.get("password_input_confirm_reg") and self.register_screen_elements[
                "password_input_confirm_reg"].collidepoint(mp):
                self.active_input_field = "password_confirm_reg"
            elif self.register_screen_elements.get("register_button") and self.register_screen_elements[
                "register_button"].collidepoint(mp):
                self.attempt_registration()
            elif self.register_screen_elements.get("login_link_button_reg") and self.register_screen_elements[
                "login_link_button_reg"].collidepoint(mp):
                self.current_game_state = GAME_STATE_LOGIN;self.active_input_field = "username_login";self.clear_input_fields();self.show_feedback_message(
                    "Giriş Yapın", self.feedback_message_duration)
            elif self.register_screen_elements.get("back_button_menu_reg") and self.register_screen_elements[
                "back_button_menu_reg"].collidepoint(mp):
                self.current_game_state = GAME_STATE_MAIN_MENU;self.clear_input_fields()
            else:
                self.active_input_field = None
        if event.type == pygame.KEYDOWN:
            if self.active_input_field and self.active_input_field in self.input_texts:
                if event.key == pygame.K_BACKSPACE:
                    self.input_texts[self.active_input_field] = self.input_texts[self.active_input_field][:-1]
                elif event.key == pygame.K_TAB:
                    if self.active_input_field == "username_reg":
                        self.active_input_field = "password_reg"
                    elif self.active_input_field == "password_reg":
                        self.active_input_field = "password_confirm_reg"
                    elif self.active_input_field == "password_confirm_reg":
                        self.active_input_field = "username_reg"
                elif event.key == pygame.K_RETURN:
                    if self.active_input_field == "password_confirm_reg":
                        self.attempt_registration()
                    elif self.active_input_field == "username_reg":
                        self.active_input_field = "password_reg"
                    elif self.active_input_field == "password_reg":
                        self.active_input_field = "password_confirm_reg"
                elif len(self.input_texts[self.active_input_field]) < 20 and (
                        event.unicode.isalnum() or event.unicode in ['.', '_', '-']):
                    self.input_texts[self.active_input_field] += event.unicode
            if event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_LOGIN;self.active_input_field = "username_login";self.clear_input_fields();self.show_feedback_message(
                "Giriş Ekranı", self.feedback_message_duration)

    def attempt_registration(self):
        un = self.input_texts["username_reg"].strip();
        pw = self.input_texts["password_reg"];
        pc = self.input_texts["password_confirm_reg"]
        if not un or not pw or not pc: self.show_feedback_message("Tüm alanları doldurun!",
                                                                  self.feedback_message_duration);return
        if len(un) < 3: self.show_feedback_message("Kullanıcı adı en az 3 karakter olmalı!",
                                                   self.feedback_message_duration);return
        if pw != pc: self.show_feedback_message("Şifreler eşleşmiyor!", self.feedback_message_duration);
        self.input_texts["password_reg"] = "";self.input_texts["password_confirm_reg"] = "";return
        if len(pw) < 3: self.show_feedback_message("Şifre en az 3 karakter olmalı!",
                                                   self.feedback_message_duration);return
        users = self._load_users()
        if un in users: self.show_feedback_message("Bu kullanıcı adı zaten alınmış!",
                                                   self.feedback_message_duration);return
        users[un] = {"password": pw, "theme": "default", "scores": {}}
        if self._save_users(users):
            self.show_feedback_message("Kayıt başarılı! Şimdi giriş yapabilirsiniz.", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_LOGIN;
            self.clear_input_fields();
            self.active_input_field = "username_login"
            self.input_texts["username_login"] = un
        else:
            self.show_feedback_message("Kayıt sırasında bir hata oluştu!", self.feedback_message_duration)

    # !!! ANA OYUN DÖNGÜSÜ - RUN METODU !!!
    def run(self):
        if not self.initialized_successfully and self.current_game_state not in [GAME_STATE_MAIN_MENU, GAME_STATE_LOGIN,
                                                                                 GAME_STATE_REGISTER,
                                                                                 GAME_STATE_THEME_SELECTION,
                                                                                 GAME_STATE_SCOREBOARD]:
            print(
                "Game could not be initialized properly (e.g. level files missing). Exiting or displaying error on screen.")
            if self.screen and pygame.get_init():
                self.screen.fill((50, 0, 0))
                error_surf = self.font_medium.render("FATAL: INIT FAILED. Check Console/Level Files.", True,
                                                     (255, 255, 255))
                rect = error_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(error_surf, rect)
                pygame.display.flip()
                pygame.time.wait(3000)
            if pygame.get_init():
                pygame.quit()
            return

        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if self.feedback_message_timer > 0:
                self.feedback_message_timer -= 1
                if self.feedback_message_timer == 0:
                    self.feedback_message = ""

            if self.current_game_state == GAME_STATE_MAIN_MENU:
                for event in events:
                    self.handle_main_menu_input(event)
                self.draw_main_menu()

            elif self.current_game_state == GAME_STATE_LOGIN:
                for event in events:
                    self.handle_login_input(event)
                self.draw_login_screen()

            elif self.current_game_state == GAME_STATE_REGISTER:
                for event in events:
                    self.handle_register_input(event)
                self.draw_register_screen()

            elif self.current_game_state == GAME_STATE_THEME_SELECTION:
                for event in events:
                    self.handle_theme_selection_input(event)
                self.draw_theme_selection_screen()

            elif self.current_game_state == GAME_STATE_SCOREBOARD:
                for event in events:
                    self.handle_scoreboard_input(event)
                self.draw_scoreboard_screen()

            elif self.current_game_state == GAME_STATE_GAMEPLAY:
                if not self.initialized_successfully:
                    print("Error: Gameplay state entered but not properly initialized. Returning to main menu.")
                    self.current_game_state = GAME_STATE_MAIN_MENU
                    self.show_feedback_message("Oyun başlatılamadı. Menüye dönülüyor.", self.feedback_message_duration)
                    continue

                for event in events:
                    self.handle_gameplay_events(event)

                if not self.game_over_flag:
                    if self.current_player_id == PLAYER_AI_ID and self.running and not self.ai_turn_processed_this_round:
                        self.process_ai_turn()
                    self.update_gameplay()

                self.render_gameplay()

        print("Exiting game loop...")
        if pygame.get_init():
            pygame.quit()

    # --- YENİ: TEMA VE SKOR TABLOSU EKRANI METODLARI ---
    def draw_theme_selection_screen(self):
        theme = self.active_theme;
        self.screen.fill(theme.get("background_main_menu", (20, 20, 30)));
        ts = self.font_large.render("Tema Seçimi", 1, theme.get("title_main_menu", (200, 220, 255)));
        tr = ts.get_rect(center=(self.screen_width // 2, self.screen_height // 6));
        self.screen.blit(ts, tr);
        bh = 45;
        bw = 280;
        aks = list(self.available_themes.keys());
        nt = len(aks);
        tlh = nt * bh + (nt - 1) * 10;
        sy = tr.bottom + 40;
        if sy + tlh > self.screen_height - (bh + 50): sy = (self.screen_height - tlh - (bh + 30)) // 2 + tr.bottom - 50;
        if sy < tr.bottom + 20: sy = tr.bottom + 20
        self.theme_selection_elements.clear();
        mp = pygame.mouse.get_pos()
        for i, tidk in enumerate(aks):
            td = self.available_themes[tidk];
            tdn = td.get("name", tidk.replace("_", " ").title());
            by = sy + i * (bh + 10);
            br = pygame.Rect((self.screen_width - bw) // 2, by, bw, bh);
            self.theme_selection_elements[tidk] = {"rect": br, "name": tdn, "id": tidk};
            ish = br.collidepoint(mp);
            isa = (self.active_theme_name == tidk);
            ic = theme.get("button_main_menu_idle");
            hc = theme.get("button_main_menu_hover");
            ac = theme.get("login_button_primary_hover_color");
            bc = theme.get("button_main_menu_border");
            trc = theme.get("text_main_menu_button");
            cc = ic;
            if isa:
                cc = ac
            elif ish:
                cc = hc
            pygame.draw.rect(self.screen, cc, br, 0, 5);
            pygame.draw.rect(self.screen, bc, br, 3 if isa else 2, 5);
            tss = self.font_medium.render(tdn, 1, trc);
            txtr = tss.get_rect(center=br.center);
            self.screen.blit(tss, txtr)
        bby = sy + nt * (bh + 10) + 30;
        if bby + bh > self.screen_height - 20: bby = self.screen_height - bh - 20
        bbr = pygame.Rect((self.screen_width - bw) // 2, bby, bw, bh);
        self.theme_selection_elements["back_to_main_menu"] = {"rect": bbr, "name": "Ana Menüye Dön",
                                                              "id": "back_to_main_menu"};
        bic = theme.get("login_button_danger_idle_color");
        bhc = theme.get("login_button_danger_hover_color");
        bbc = bhc if bbr.collidepoint(mp) else bic;
        pygame.draw.rect(self.screen, bbc, bbr, 0, 5);
        pygame.draw.rect(self.screen, bc, bbr, 2, 5);
        bts = self.font_medium.render("Ana Menüye Dön", 1, theme.get("login_button_text_color"));
        self.screen.blit(bts, bts.get_rect(center=bbr.center));
        if self.feedback_message_timer > 0 and self.feedback_message: fbs = self.font_medium.render(
            self.feedback_message, 1, self.active_theme.get("feedback_text_color"));bgr = fbs.get_rect(
            center=(self.screen_width // 2, self.screen_height - 40));bgr.inflate_ip(20, 10);bgs = pygame.Surface(
            bgr.size, pygame.SRCALPHA);bgs.fill(self.active_theme.get("feedback_bg_color"));self.screen.blit(bgs,
                                                                                                             bgr.topleft);self.screen.blit(
            fbs, fbs.get_rect(center=bgr.center));
        pygame.display.flip()

    def handle_theme_selection_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for eidk, data in self.theme_selection_elements.items():
                if data["rect"].collidepoint(mp):
                    if eidk == "back_to_main_menu":
                        self.current_game_state = GAME_STATE_MAIN_MENU;self.show_feedback_message("", 0)
                    else:
                        self.set_active_theme(eidk)
                    break
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_MAIN_MENU;self.show_feedback_message(
            "", 0)

    def draw_scoreboard_screen(self):
        theme = self.active_theme;
        self.screen.fill(theme.get("background_main_menu", (25, 25, 35)))
        title_surf = self.font_large.render("Skor Tablosu", True, theme.get("title_main_menu", (200, 220, 255)))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 8))
        self.screen.blit(title_surf, title_rect)
        all_users_data = self._load_users();
        level_scores = {}
        for username, user_data_obj in all_users_data.items():
            if isinstance(user_data_obj, dict):
                user_scores = user_data_obj.get("scores", {})
                for level_id_str, score in user_scores.items():
                    if level_id_str not in level_scores: level_scores[level_id_str] = []
                    level_scores[level_id_str].append((score, username))
        current_y = title_rect.bottom + 20;
        line_height = 28;
        score_text_color = theme.get("text_main_menu_button", (220, 220, 255));
        level_title_color = theme.get("title_main_menu", (200, 200, 255));
        max_scores_display = 5
        if not level_scores:
            no_scores_surf = self.font_medium.render("Henüz hiç skor kaydedilmemiş.", True, score_text_color)
            self.screen.blit(no_scores_surf, no_scores_surf.get_rect(center=(self.screen_width // 2, current_y + 50)))
        else:
            sorted_level_ids = sorted(level_scores.keys(), key=lambda x: int(x.replace("level", "")))
            for level_id_str in sorted_level_ids:
                if current_y + line_height * (max_scores_display + 2) > self.screen_height - 80: break
                level_display_num = level_id_str.replace("level", "")
                level_title_surf = self.font_medium.render(f"--- Seviye {level_display_num} En İyiler ---", True,
                                                           level_title_color)
                self.screen.blit(level_title_surf,
                                 level_title_surf.get_rect(center=(self.screen_width // 2, current_y)));
                current_y += line_height
                sorted_scores = sorted(level_scores[level_id_str], key=lambda x: x[0], reverse=True)[
                                :max_scores_display]
                if not sorted_scores:
                    no_score_level_surf = self.font_small.render("Bu seviye için skor yok.", True, score_text_color)
                    self.screen.blit(no_score_level_surf,
                                     no_score_level_surf.get_rect(center=(self.screen_width // 2, current_y)));
                    current_y += line_height - 10
                else:
                    for rank, (score, username) in enumerate(sorted_scores):
                        if current_y + line_height > self.screen_height - 80: break
                        score_line = f"{rank + 1}. {username}: {score} Puan"
                        score_surf = self.font_small.render(score_line, True, score_text_color)
                        self.screen.blit(score_surf, score_surf.get_rect(center=(self.screen_width // 2, current_y)));
                        current_y += line_height - 8
                current_y += 15
        button_width = 230;
        button_height = 45
        back_button_rect = pygame.Rect((self.screen_width - button_width) // 2, self.screen_height - button_height - 30,
                                       button_width, button_height)
        self.scoreboard_elements["back_to_main_menu"] = {"rect": back_button_rect, "name": "Ana Menüye Dön"}
        mouse_pos = pygame.mouse.get_pos();
        back_idle_color = theme.get("login_button_danger_idle_color", (120, 40, 40));
        back_hover_color = theme.get("login_button_danger_hover_color", (150, 50, 50))
        back_button_color = back_hover_color if back_button_rect.collidepoint(mouse_pos) else back_idle_color
        pygame.draw.rect(self.screen, back_button_color, back_button_rect, border_radius=5);
        pygame.draw.rect(self.screen, theme.get("button_main_menu_border", (120, 120, 150)), back_button_rect, 2,
                         border_radius=5)
        back_text_surf = self.font_medium.render("Ana Menüye Dön", True,
                                                 theme.get("login_button_text_color", (255, 255, 255)));
        self.screen.blit(back_text_surf, back_text_surf.get_rect(center=back_button_rect.center))
        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True,
                                                    self.active_theme.get("feedback_text_color", (255, 200, 0)))
            bg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 80));
            bg_rect.inflate_ip(20, 10)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA);
            bg_surface.fill(self.active_theme.get("feedback_bg_color", (0, 0, 0, 180)))
            self.screen.blit(bg_surface, bg_rect.topleft);
            self.screen.blit(feedback_surf, feedback_surf.get_rect(center=bg_rect.center))
        pygame.display.flip()

    def handle_scoreboard_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.scoreboard_elements.get("back_to_main_menu", {}).get("rect", pygame.Rect(0, 0, 0, 0)).collidepoint(
                    mouse_pos):
                self.current_game_state = GAME_STATE_MAIN_MENU;
                self.show_feedback_message("", 0)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_MAIN_MENU; self.show_feedback_message(
            "", 0)

    # --- Kalan Gameplay Metodları ---
    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()
        if unit and unit.is_alive() and unit.player_id == self.current_player_id and not unit.has_acted_this_turn:
            self.highlighted_tiles_for_move = unit.get_tiles_in_movement_range(self.game_map)

    def highlight_attackable_tiles(self, unit):
        self.clear_highlighted_attack_tiles()
        if unit and unit.is_alive() and unit.player_id == self.current_player_id and not unit.has_acted_this_turn:
            self.highlighted_tiles_for_attack = unit.get_tiles_in_attack_range(self.game_map)

    def clear_highlighted_tiles(self):
        self.highlighted_tiles_for_move = []

    def clear_highlighted_attack_tiles(self):
        self.highlighted_tiles_for_attack = []

    def clear_all_highlights(self):
        self.clear_highlighted_tiles(); self.clear_highlighted_attack_tiles()

    def execute_command(self, command):  # !!! DÜZELTİLMİŞ HALİ !!!
        command_successful = False
        acting_unit = None
        if command and hasattr(command, 'unit') and command.unit:
            acting_unit = command.unit

        if acting_unit:
            if acting_unit.is_alive():
                if command.execute():
                    self.command_history.append(command)
                    command_successful = True
            # else: Hata mesajı execute içinde verilebilir veya burada da eklenebilir
        elif command and hasattr(command, 'execute'):  # Birimsiz genel komut
            if command.execute():
                command_successful = True

        if command_successful:
            self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
            if self.selected_unit:
                s_unit = self.selected_unit  # Okunurluk için
                if not s_unit.is_alive() or \
                        (hasattr(s_unit, 'has_acted_this_turn') and s_unit.has_acted_this_turn) or \
                        s_unit.current_state_name != SelectedState.__name__:
                    self.clear_all_highlights()
                    self.selected_unit = None
            return True
        return False

    def handle_gameplay_events(self, event):
        if self.game_over_flag:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: self.running = False; return

        if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self.handle_mouse_click(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u and self.current_player_id == PLAYER_HUMAN_ID and self.command_history and not self.game_over_flag:
                # ... (undo kodu aynı) ...
                lc = self.command_history.pop();
                uu = None
                if hasattr(lc, 'unit') and lc.unit: uu = lc.unit;uu.has_acted_this_turn = False;print(
                    f"Undo: {uu.id} can act.")
                lc.undo();
                self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
                self.selected_unit = None;
                self.clear_all_highlights();
                self.show_feedback_message(f"Action Undone{(f' for {uu.unit_type}' if uu else '')}",
                                           self.feedback_message_duration)

            if event.key == pygame.K_e and self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag: self.end_turn()
            if event.key == pygame.K_k and not self.game_over_flag: self.save_game()

            if event.key == pygame.K_r and self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:  # !!! YENİ: 'R' TUŞU İLE GÖSTER/GİZLE !!!
                self.show_ai_threat_display = not self.show_ai_threat_display
                if self.show_ai_threat_display:
                    self._calculate_ai_threat_tiles()  # Açıksa yeniden hesapla (AI hareket etmiş olabilir)
                    self.show_feedback_message("AI Tehdit Alanı Gösteriliyor", self.feedback_message_duration // 2)
                else:
                    self.show_feedback_message("AI Tehdit Alanı Gizlendi", self.feedback_message_duration // 2)

            if event.key == pygame.K_ESCAPE and not self.game_over_flag:
                self.show_feedback_message("Returning to Main Menu...", self.feedback_message_duration // 2)
                if self.selected_unit: self.selected_unit.set_state(IdleState(self.selected_unit),
                                                                    self);self.selected_unit = None
                self.clear_all_highlights();
                self.current_game_state = GAME_STATE_MAIN_MENU
    def update_gameplay(self):
        if not self.game_over_flag and hasattr(self, 'game_map') and self.game_map:
            for unit in self.game_map.units:
                if unit.is_alive(): unit.update(self.dt)

    def render_gameplay(self):
        if not self.initialized_successfully or not hasattr(self, 'game_map') or not self.game_map:
            # ... (hata çizimi aynı) ...
            return

        self.screen.fill(self.active_theme.get("gameplay_bg", (30, 30, 30)))
        if self.game_map: self.game_map.draw(self.screen, self.active_theme, self.font_small)  # font_small'u yolla

        # Hareket ve Saldırı menzili vurguları (öncekiyle aynı)
        move_highlight_color = self.active_theme.get("highlight_move", (0, 255, 0, 80))
        attack_highlight_color = self.active_theme.get("highlight_attack", (255, 0, 0, 80))
        for tile in self.highlighted_tiles_for_move:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA);
            highlight_surf.fill(move_highlight_color)
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))
        for tile in self.highlighted_tiles_for_attack:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA);
            highlight_surf.fill(attack_highlight_color)
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        # !!! YENİ: AI Tehdit Alanını Çizdirme !!!
        if self.show_ai_threat_display:
            #print(
                #f"DEBUG: render_gameplay - show_ai_threat_display: {self.show_ai_threat_display}, content of ai_threat_tiles: {self.ai_threat_tiles}")
            ai_threat_color = self.active_theme.get("ai_threat_range_color", (128, 0, 128, 70))
            #if not self.ai_threat_tiles:  # Ekstra kontrol: Eğer set boşsa bir şey çizme
                #print("DEBUG: ai_threat_tiles is empty, nothing to draw for AI threat.")

            for gx, gy in self.ai_threat_tiles:
                tile = self.game_map.get_tile_at_grid_coords(gx, gy)
                if tile:
                    threat_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    threat_surf.fill(ai_threat_color)
                    self.screen.blit(threat_surf, (tile.pixel_x, tile.pixel_y))

        text_color = self.active_theme.get("gameplay_info_text_color", (230, 230, 230))
        level_turn_text_str = f"Lvl:{self.current_level_number} | Turn: P{self.current_player_id}({'Human' if self.current_player_id == PLAYER_HUMAN_ID else 'AI'}) | Turns: {self.turns_taken_this_level}"
        if self.game_over_flag:  # ... (oyun sonu mesajı) ...
            cf = self.feedback_message;
            lts = level_turn_text_str
            if "CONGRATULATIONS" in cf:
                lts = "YOU WIN THE GAME!"
            elif "CLEARED" in cf:
                lts = f"LEVEL {self.current_level_number - 1 if self.current_level_number > MAX_LEVELS else self.current_level_number} CLEARED!"
            elif "FAILED" in cf or "Wins" in cf:
                lts = f"GAME OVER - Lvl {self.current_level_number}"
            elif "Draw" in cf:
                lts = f"GAME OVER - Lvl {self.current_level_number}(Draw)"
            else:
                lts = f"GAME OVER - Lvl {self.current_level_number}"
            level_turn_text_str = lts
        level_turn_surface = self.font_medium.render(level_turn_text_str, True, text_color);
        self.screen.blit(level_turn_surface, (10, 10))
        cts = "'E'End|'K'Save|'U'Undo|'R'Threat|'ESC'Menu";
        cts_s = self.font_small.render(cts, True, text_color);
        r = cts_s.get_rect(bottomright=(self.screen_width - 10, self.screen_height - 10));
        self.screen.blit(cts_s, r)  # 'R' Threat EKLENDİ
        if self.feedback_message_timer > 0 and self.feedback_message and not (
                self.game_over_flag and level_turn_text_str == self.feedback_message):
            fs = self.font_medium.render(self.feedback_message, True,
                                         self.active_theme.get("feedback_text_color", (255, 200, 0)));
            bgr = fs.get_rect(center=(self.screen_width // 2, self.screen_height - 30));
            bgr.inflate_ip(20, 10)
            bgs = pygame.Surface(bgr.size, pygame.SRCALPHA);
            bgs.fill(self.active_theme.get("feedback_bg_color", (20, 20, 20, 200)));
            self.screen.blit(bgs, bgr.topleft);
            self.screen.blit(fs, fs.get_rect(center=bgr.center))
        pygame.display.flip()

    def end_turn(self):
        if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag: self.turns_taken_this_level += 1; print(
            f"DEBUG: Human ending turn. Turns: {self.turns_taken_this_level}")
        self.show_feedback_message(f"P{self.current_player_id} Ends Turn", self.feedback_message_duration // 2)
        if self.selected_unit: self.selected_unit.set_state(IdleState(self.selected_unit),
                                                            self);self.selected_unit = None
        self.clear_all_highlights();
        self.command_history.clear()
        np_id = PLAYER_AI_ID if self.current_player_id == PLAYER_HUMAN_ID else PLAYER_HUMAN_ID;
        self.current_player_id = np_id
        self.reset_unit_actions_for_player(self.current_player_id)
        if self.current_player_id == PLAYER_AI_ID: self.ai_turn_processed_this_round = False
        elif self.current_player_id == PLAYER_HUMAN_ID:  # !!! İNSAN SIRASI BAŞLADIĞINDA !!!
            self._calculate_ai_threat_tiles()  # AI tehdit alanını hesapla/güncelle
            # self.show_ai_threat_display = True # İstersen her tur başında otomatik açılsın
            # ya da oyuncu kendi tuşuyla açsın
        if not self.check_game_over(): self.show_feedback_message(f"P{self.current_player_id}'s Turn",
                                                                  self.feedback_message_duration)

    def check_game_over(self):
        if not hasattr(self, 'game_map') or not self.game_map:
            # Eğer game_map yoksa (örn: oyun düzgün başlatılamadıysa) erken çık
            if self.initialized_successfully:  # Ama oyunun başladığını düşünüyorsak hata ver
                print("ERROR: check_game_over called without a valid game_map after successful init!")
            return False

        human_units_alive_list = [u for u in self.game_map.units if u.player_id == PLAYER_HUMAN_ID and u.is_alive()]
        ai_units_alive = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_AI_ID)

        human_has_units = len(human_units_alive_list) > 0

        game_over_message = ""
        level_cleared_by_human = False

        # current_level_number, o an oynanan seviyedir. Eğer bu seviye temizlenirse, skor bu seviye için kaydedilir.
        level_just_finished = self.current_level_number

        if human_has_units and not ai_units_alive:  # İnsan kazandı
            game_over_message = f"LEVEL {level_just_finished} CLEARED!"
            level_cleared_by_human = True
        elif not human_has_units and ai_units_alive:  # AI kazandı
            game_over_message = f"LEVEL {level_just_finished} FAILED! AI Wins!"
            self.game_over_flag = True  # Oyun genel olarak bitti (kayıp)
        elif not human_has_units and not ai_units_alive and len(
                self.game_map.units) == 0 and self.initialized_successfully:  # Harita tamamen boşaldıysa (beraberlik)
            game_over_message = f"LEVEL {level_just_finished} FAILED! Draw!"
            self.game_over_flag = True

        if game_over_message:  # Eğer bir sonuç mesajı oluştuysa (kazanma, kaybetme, beraberlik)
            print(game_over_message)
            self.show_feedback_message(game_over_message, 180)  # Mesajı ekranda göster

            if level_cleared_by_human:
                # Skoru, seviye bittiğindeki tur sayısı ve kalan birimlerle hesapla
                turns_for_this_level = self.turns_taken_this_level  # O seviyede harcanan tur
                remaining_units_count = len(human_units_alive_list)  # Kalan insan birimi sayısı

                # _calculate_score metoduna doğru parametreleri yolla
                calculated_score = self._calculate_score(turns_for_this_level, remaining_units_count)
                # _record_score metoduna hesaplanan skoru ve bitirilen seviye numarasını yolla
                self._record_score(calculated_score, level_just_finished)

                next_level_to_load = level_just_finished + 1
                if next_level_to_load > MAX_LEVELS:
                    self.show_feedback_message("CONGRATULATIONS! You beat all levels!", 9999)
                    self.game_over_flag = True  # Tüm oyun bitti
                else:
                    # Bir sonraki seviyeye geçmeden önce oyuncuya zaman tanıyalım
                    pygame.display.flip()  # "LEVEL CLEARED" mesajını göster
                    time.sleep(2)  # 2 saniye bekle

                    # Bir sonraki seviyeyi başlat
                    # initialize_gameplay_state, current_level_number'ı next_level_to_load yapacak
                    # ve turns_taken_this_level'ı sıfırlayacak.
                    if not self.initialize_gameplay_state(next_level_to_load,
                                                          is_new_game_session=False):  # is_new_game_session=False olmalı
                        self.game_over_flag = True  # Yeni seviye yüklenemezse oyunu bitir

            return self.game_over_flag  # Oyunun genel bitiş durumunu döndür

        return False  # Oyun devam ediyor

    def _record_score(self, score_to_record, level_number_cleared):  # PARAMETRE ALIYOR
        """Hesaplanan skoru mevcut kullanıcı için kaydeder."""
        if not self.current_user:
            print("DEBUG: _record_score - No current_user to record score for.")
            return

        level_id_str = f"level{level_number_cleared}"
        # current_score (score_to_record) zaten parametre olarak geliyor.
        print(
            f"DEBUG: _record_score - User: {self.current_user}, Level Cleared: {level_id_str}, Score to Record: {score_to_record}")

        users = self._load_users()
        user_data_container = users.get(self.current_user)

        if not isinstance(user_data_container, dict):
            user_data_container = {"password": "", "theme": "default", "scores": {}}
            users[self.current_user] = user_data_container
            print(f"DEBUG: _record_score - User data for {self.current_user} initialized as dict.")

        if "scores" not in user_data_container:
            user_data_container["scores"] = {}
            print(f"DEBUG: _record_score - 'scores' dict created for {self.current_user}.")

        previous_best_score = user_data_container["scores"].get(level_id_str, 0)
        print(f"DEBUG: _record_score - Previous best for {self.current_user} on {level_id_str}: {previous_best_score}")

        score_updated = False
        if score_to_record > previous_best_score:
            user_data_container["scores"][level_id_str] = score_to_record
            self.show_feedback_message(f"Yeni Yüksek Skor Lvl {level_number_cleared}: {score_to_record}!",
                                       self.feedback_message_duration)
            score_updated = True
            print(f"DEBUG: _record_score - New high score recorded: {score_to_record}")
        elif previous_best_score == 0 and score_to_record > 0:
            user_data_container["scores"][level_id_str] = score_to_record
            self.show_feedback_message(f"Skor Lvl {level_number_cleared}: {score_to_record}!",
                                       self.feedback_message_duration)
            score_updated = True
            print(f"DEBUG: _record_score - First score recorded: {score_to_record}")
        else:
            print(
                f"DEBUG: _record_score - Score {score_to_record} not higher than {previous_best_score}. Not overwriting.")

        if score_updated:
            if self._save_users(users):
                print(f"DEBUG: _record_score - Users data saved for {self.current_user}.")
            else:
                print(f"DEBUG: _record_score - FAILED to save users data for {self.current_user}.")
        else:
            print(f"DEBUG: _record_score - No score update needed for {self.current_user} on {level_id_str}.")

    def _calculate_score(self, turns_for_level, num_remaining_human_units):  # PARAMETRE ALIYOR
        """Belirli bir seviye için oyuncunun skorunu hesaplar."""
        print(
            f"DEBUG: _calculate_score - Turns for level: {turns_for_level}, Remaining human units: {num_remaining_human_units}")

        base_score = 5000  # Seviyeyi bitirme bazı
        score = base_score
        print(f"DEBUG: _calculate_score - Base score: {score}")

        unit_bonus = num_remaining_human_units * 100
        score += unit_bonus
        print(f"DEBUG: _calculate_score - Unit bonus: {unit_bonus}, Score after unit bonus: {score}")

        turn_penalty = turns_for_level * 20
        score -= turn_penalty
        print(f"DEBUG: _calculate_score - Turn penalty: {turn_penalty}, Score after penalty: {score}")

        final_score = max(0, score)  # Minimum skor 0
        print(f"DEBUG: _calculate_score - Final calculated score: {final_score}")
        return final_score

    def process_ai_turn(self):
        if self.current_player_id == PLAYER_AI_ID and not self.ai_turn_processed_this_round and self.running and not self.game_over_flag:
            self.show_feedback_message("AI thinking...", self.feedback_message_duration // 2);
            pygame.display.flip();
            time.sleep(0.1)
            ai_units_to_act = [u for u in self.game_map.units if
                               u.player_id == PLAYER_AI_ID and u.is_alive() and not u.has_acted_this_turn]
            if not ai_units_to_act: print(
                "AI no units/all acted.");self.ai_turn_processed_this_round = True;self.end_turn();return

            any_action_taken_by_ai_this_turn = False
            for ai_unit in ai_units_to_act:
                if not self.running or self.game_over_flag: break
                if not ai_unit.is_alive() or ai_unit.has_acted_this_turn: continue
                pygame.display.flip();
                time.sleep(0.3)

                # !!! DEĞİŞİKLİK: Her birim kendi stratejisini kullanıyor !!!
                strategy_to_use = ai_unit.ai_strategy_instance if ai_unit.ai_strategy_instance else self.default_ai_strategy
                print(f"DEBUG: AI Unit ID {ai_unit.id} using strategy: {strategy_to_use.__class__.__name__}")
                action_command = strategy_to_use.choose_action(ai_unit, self)

                if action_command:
                    self.show_feedback_message(f"AI: {action_command.description}", self.feedback_message_duration)
                    if self.execute_command(
                            action_command):  # execute_command artık birimin eylem yapıp yapmadığını kontrol ETMİYOR
                        ai_unit.has_acted_this_turn = True  # AI birimi eylemini yaptı olarak işaretle
                        any_action_taken_by_ai_this_turn = True
                    pygame.display.flip();
                    time.sleep(0.6)
                else:  # Eylem bulamadıysa da o birim için eylem hakkı bitmiş sayılır.
                    ai_unit.has_acted_this_turn = True
                    print(
                        f"AI Unit {ai_unit.id} (Player {ai_unit.player_id}) using {strategy_to_use.__class__.__name__} could not find/execute a valid action.")

            if not any_action_taken_by_ai_this_turn and ai_units_to_act:
                self.show_feedback_message("AI: No valid actions found this turn.", self.feedback_message_duration)

            self.ai_turn_processed_this_round = True  # AI'nın bu tur için tüm birimleriyle işi bitti
            self.end_turn()

    def handle_mouse_click(self, mouse_pos):
        if self.current_player_id != PLAYER_HUMAN_ID or self.game_over_flag: return
        ct = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1]);
        aufc = self.selected_unit
        if not aufc and ct and ct.unit_on_tile:
            if ct.unit_on_tile.player_id == PLAYER_HUMAN_ID and ct.unit_on_tile.is_alive() and not ct.unit_on_tile.has_acted_this_turn: aufc = ct.unit_on_tile
        if aufc:
            aufc.handle_click(self, ct)
        elif ct and not self.selected_unit:
            self.clear_all_highlights()

    def _calculate_ai_threat_tiles(self):
        self.ai_threat_tiles.clear()
        if not hasattr(self, 'game_map') or not self.game_map:
            return

        # print("DEBUG: Calculating AI potential attack zone...") # YORUMA ALINDI veya SİLİNDİ
        any_zone_found = False
        for unit in self.game_map.units:
            if unit.player_id == PLAYER_AI_ID and unit.is_alive():
                zone_coords = unit.get_attack_zone_coordinates(self.game_map)
                if zone_coords:
                    any_zone_found = True
                    # print(f"DEBUG: AI Unit ID {unit.id} at ({unit.grid_x},{unit.grid_y}) can attack coords: {zone_coords}") # YORUMA ALINDI veya SİLİNDİ
                    self.ai_threat_tiles.update(zone_coords)

        # if not any_zone_found: # YORUMA ALINDI veya SİLİNDİ
        # print("DEBUG: No AI units have any potential attack zones currently.") # YORUMA ALINDI veya SİLİNDİ
        # print(f"DEBUG: Final calculated AI threat zone coordinates: {self.ai_threat_tiles}") # YORUMA ALINDI veya SİLİNDİ