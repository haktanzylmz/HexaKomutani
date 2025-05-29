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
from .constants import PLAYER_HUMAN_ID, PLAYER_AI_ID

# Sabitler ve Dosya Yolları
USERS_FILE_NAME_BASE = "users.json"
BASE_SAVE_FILENAME = "savegame.json"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # game_core dizini
SRC_DIR = os.path.dirname(SCRIPT_DIR)  # src dizini
PROJECT_ROOT_DIR = os.path.dirname(SRC_DIR)  # HexaKomutani ana dizini

LEVELS_DIR = os.path.join(SRC_DIR, "levels")
LEVEL_FILE_PREFIX = os.path.join(LEVELS_DIR, "level")
SAVES_DIR = os.path.join(PROJECT_ROOT_DIR, "saves")
USERS_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, USERS_FILE_NAME_BASE)

MAX_LEVELS = 2
STATE_NAME_TO_CLASS_MAP = {"IdleState": IdleState, "SelectedState": SelectedState}

GAME_STATE_MAIN_MENU = "main_menu"
GAME_STATE_GAMEPLAY = "gameplay"
GAME_STATE_LOGIN = "login_screen"
GAME_STATE_REGISTER = "register_screen"


class Game:
    def __init__(self, screen_width, screen_height, load_from_save_on_start=False):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")

        try:
            self.font_small = pygame.font.SysFont(None, 24)
            self.font_medium = pygame.font.SysFont(None, 30)
            self.font_large = pygame.font.SysFont(None, 50)
        except Exception as e:
            print(f"Font Yükleme Hatası: {e}. Varsayılan font kullanılacak.")
            self.font_small = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 30)
            self.font_large = pygame.font.Font(None, 50)

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
        self.initialized_successfully = False  # Gameplay için başlatma bayrağı

        self.unit_factory = UnitFactory()
        self.ai_strategies = {"SimpleAggressiveStrategy": SimpleAggressiveStrategy()}
        self.default_ai_strategy = self.ai_strategies["SimpleAggressiveStrategy"]

        self.main_menu_buttons = {}
        self.login_screen_elements = {}
        self.register_screen_elements = {}

        self.active_input_field = None
        self.input_texts = {key: "" for key in ["username_login", "password_login", "username_reg", "password_reg",
                                                "password_confirm_reg"]}
        self.current_user = None

        self.game_map = None
        self.map_cols = 0
        self.map_rows = 0
        self.current_player_id = PLAYER_HUMAN_ID
        self.ai_turn_processed_this_round = False

        self._ensure_data_dirs_exist()

        # load_from_save_on_start artık __init__ içinde doğrudan oyun yüklemiyor.
        # Oyun her zaman ana menü ile başlar. Yükleme menüden yapılır.
        # Bu bayrak, ileride komut satırı argümanları vb. için tutulabilir ama şu anki akışta gereksiz.

    def _ensure_data_dirs_exist(self):
        user_file_dir = os.path.dirname(USERS_FILE_NAME)
        if user_file_dir and not os.path.exists(user_file_dir):
            try:
                os.makedirs(user_file_dir, exist_ok=True)  # Ana dizin zaten var olmalı
            except OSError as e:
                print(f"Error creating directory for '{USERS_FILE_NAME}': {e}")

        if not os.path.exists(USERS_FILE_NAME):
            try:
                with open(USERS_FILE_NAME, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"'{USERS_FILE_NAME}' created at: {os.path.abspath(USERS_FILE_NAME)}")
            except IOError as e:
                print(f"Error creating '{USERS_FILE_NAME}': {e}")

        if not os.path.exists(SAVES_DIR):
            try:
                os.makedirs(SAVES_DIR, exist_ok=True)
                print(f"Saves directory '{SAVES_DIR}' created at: {os.path.abspath(SAVES_DIR)}")
            except OSError as e:
                print(f"Error creating saves directory '{SAVES_DIR}': {e}")

    def _get_user_save_filename(self):
        if self.current_user:
            safe_username = "".join(c if c.isalnum() else "_" for c in self.current_user)
            return os.path.join(SAVES_DIR, f"{safe_username.lower()}_{BASE_SAVE_FILENAME}")
        return None

    def _load_users(self):
        self._ensure_data_dirs_exist()
        try:
            with open(USERS_FILE_NAME, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                if not isinstance(users_data, dict): return {}
                return users_data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_users(self, users_data):
        try:
            with open(USERS_FILE_NAME, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

    def initialize_gameplay_state(self, level_to_load=1, is_new_game_session=True):
        print(f"Initializing gameplay state for level {level_to_load}, new session: {is_new_game_session}")
        self.selected_unit = None;
        self.command_history = []
        self.highlighted_tiles_for_move = [];
        self.highlighted_tiles_for_attack = []
        self.current_level_number = level_to_load
        if self._initialize_game_for_level(self.current_level_number, is_new_game_session=is_new_game_session):
            self.initialized_successfully = True;
            return True
        else:
            self.initialized_successfully = False
            self.show_feedback_message("Failed to initialize gameplay.", self.feedback_message_duration);
            return False

    def _initialize_game_for_level(self, level_number, is_new_game_session=False):
        self.current_level_number = level_number
        level_data = self.load_level_data(level_number)
        if not level_data:
            print(f"Could not load level {level_number} data. Init aborted for _initialize_game_for_level.");
            return False
        self.map_cols = level_data.get("map_cols", self.screen_width // self.tile_size)
        self.map_rows = level_data.get("map_rows", self.screen_height // self.tile_size)
        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size);
        self.game_map.create_grid()
        self.current_player_id = PLAYER_HUMAN_ID
        self.game_map.units = []
        self.selected_unit = None;
        self.clear_all_highlights()
        if is_new_game_session: Unit._id_counter = 0
        self.setup_units_from_level_data(level_data)
        self.game_over_flag = False
        self.reset_unit_actions_for_player(self.current_player_id)
        level_name = level_data.get('level_name', f'Lvl {level_number}')
        print(f"Level {level_number} ('{level_name}') initialized.");
        self.show_feedback_message(f"Level {level_number}: {level_name}", self.feedback_message_duration)
        return True

    def reset_unit_actions_for_player(self, player_id):
        if hasattr(self, 'game_map') and self.game_map and self.game_map.units:
            for unit in self.game_map.units:
                if unit.player_id == player_id: unit.has_acted_this_turn = False
        if player_id == PLAYER_AI_ID: self.ai_turn_processed_this_round = False

    def load_level_data(self, level_number):
        filename = f"{LEVEL_FILE_PREFIX}{level_number}.json"
        print(f"Attempting to load level data from: {filename}")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                level_data = json.load(f)
            print(f"Level {level_number} data loaded from {filename}");
            return level_data
        except FileNotFoundError:
            print(f"LEVEL FILE NOT FOUND AT: '{filename}'"); self.show_feedback_message(
                f"Lvl File Not Found: lvl{level_number}.json", 9999); return None
        except Exception as e:
            print(f"Error loading level data from {filename}: {e}"); self.show_feedback_message(
                f"Error Loading Lvl {level_number}!", 9999); return None

    def setup_units_from_level_data(self, level_data):
        if "player_units" in level_data:
            for unit_info in level_data["player_units"]:
                unit = self.unit_factory.create_unit(unit_info["type"], unit_info["x"], unit_info["y"],
                                                     unit_info["player_id"])
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)
        if "ai_units" in level_data:
            for unit_info in level_data["ai_units"]:
                unit = self.unit_factory.create_unit(unit_info["type"], unit_info["x"], unit_info["y"],
                                                     unit_info["player_id"])
                if unit and unit.player_id == PLAYER_AI_ID: unit.color = (200, 50, 50)
                self.game_map.add_unit(unit, unit.grid_x, unit.grid_y)

    def show_feedback_message(self, message, duration_frames):
        self.feedback_message = message;
        self.feedback_message_timer = duration_frames

    def save_game(self):
        if not self.current_user:
            self.show_feedback_message("Kaydetmek için giriş yapmalısınız!", self.feedback_message_duration);
            return
        if not self.initialized_successfully or not self.game_map:  # Gameplay aktif mi kontrolü
            self.show_feedback_message("Cannot save: Gameplay not active.", self.feedback_message_duration);
            return
        user_save_file = self._get_user_save_filename()
        if not user_save_file: print("Error: Could not determine user save file name for saving."); return
        print(f"Saving game to {user_save_file} for user {self.current_user}...")
        if self.selected_unit: self.selected_unit.is_graphically_selected = False
        game_state_data = {
            "user": self.current_user, "current_player_id": self.current_player_id,
            "current_level_number": self.current_level_number, "map_data": self.game_map.to_dict(),
            "units_data": [unit.to_dict() for unit in self.game_map.units if unit.is_alive()],
            "next_unit_id": Unit._id_counter, "game_over_flag": self.game_over_flag,
            "ai_turn_processed_this_round": self.ai_turn_processed_this_round
        }
        try:
            with open(user_save_file, 'w', encoding='utf-8') as f:
                json.dump(game_state_data, f, indent=4, ensure_ascii=False)
            print("Game saved successfully!");
            self.show_feedback_message(f"Game Saved for {self.current_user}!", self.feedback_message_duration)
        except IOError as e:
            print(f"Error saving game: {e}"); self.show_feedback_message("Error Saving Game!",
                                                                         self.feedback_message_duration)

    def load_game(self):
        user_save_file = self._get_user_save_filename()
        if not user_save_file: return False
        if not os.path.exists(user_save_file):
            print(f"Save file for user '{self.current_user}' not found at '{user_save_file}'.")
            return False
        print(f"Attempting to load game data from {user_save_file} for user {self.current_user}...")
        try:
            with open(user_save_file, 'r', encoding='utf-8') as f:
                game_state_data = json.load(f)
            self.command_history = []
            self.current_level_number = game_state_data.get("current_level_number", 1)
            map_info = game_state_data["map_data"]
            self.map_rows = map_info["rows"];
            self.map_cols = map_info["cols"]
            self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)  # game_map burada oluşturuluyor
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
                if unit.player_id == PLAYER_AI_ID:
                    unit.color = (200, 50, 50)
                elif unit.player_id == PLAYER_HUMAN_ID:
                    unit.color = (50, 150, 50)
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
            print("Game data parsed successfully for loading!");
            return True
        except FileNotFoundError:
            print(f"Save file '{user_save_file}' not found (should be caught by os.path.exists)."); return False
        except Exception as e:
            print(f"Error parsing game data from {user_save_file}: {e}"); import \
                traceback; traceback.print_exc(); return False

    def load_game_into_gameplay(self):
        if not self.current_user:
            self.show_feedback_message("Lütfen önce giriş yapın!", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_LOGIN
            self.active_input_field = "username_login";
            self.clear_input_fields()
            return False
        user_save_file = self._get_user_save_filename()
        if not user_save_file or not os.path.exists(user_save_file):
            self.show_feedback_message(f"{self.current_user} için kayıtlı oyun yok.", self.feedback_message_duration)
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
        self.screen.fill((40, 40, 60));
        title_surf = self.font_large.render("Hexa Komutanı", True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 4 - 20));
        self.screen.blit(title_surf, title_rect)
        user_message = f"Giriş Yapıldı: {self.current_user}" if self.current_user else "Giriş Yapılmadı"
        user_color = (180, 255, 180) if self.current_user else (255, 180, 180)
        user_surf = self.font_small.render(user_message, True, user_color);
        user_rect = user_surf.get_rect(center=(self.screen_width // 2, title_rect.bottom + 30));
        self.screen.blit(user_surf, user_rect)
        button_texts = ["Yeni Oyun", "Oyun Yükle"];
        button_texts.append("Çıkış Yap" if self.current_user else "Giriş / Kayıt");
        button_texts.append("Oyundan Çık")
        button_height = 50;
        button_width = 220;
        start_y = user_rect.bottom + 40;
        self.main_menu_buttons.clear()
        for i, text in enumerate(button_texts):
            button_y = start_y + i * (button_height + 15)
            button_rect = pygame.Rect((self.screen_width - button_width) // 2, button_y, button_width, button_height)
            self.main_menu_buttons[text] = button_rect;
            mouse_pos = pygame.mouse.get_pos()
            button_color = (90, 90, 110) if button_rect.collidepoint(mouse_pos) else (70, 70, 90)
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5);
            pygame.draw.rect(self.screen, (120, 120, 150), button_rect, 3, border_radius=5)
            text_surf = self.font_medium.render(text, True, (220, 220, 255));
            text_rect = text_surf.get_rect(center=button_rect.center);
            self.screen.blit(text_surf, text_rect)
        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            bg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 40));
            bg_rect.inflate_ip(20, 10)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA);
            bg_surface.fill((0, 0, 0, 180));
            self.screen.blit(bg_surface, bg_rect.topleft);
            self.screen.blit(feedback_surf, feedback_surf.get_rect(center=bg_rect.center))
        pygame.display.flip()

    def handle_main_menu_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for button_text, rect in self.main_menu_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        print(f"Main menu button clicked: {button_text}")
                        if button_text == "Yeni Oyun":
                            if not self.current_user:
                                self.show_feedback_message("Yeni oyun için lütfen giriş yapın.",
                                                           self.feedback_message_duration)
                                self.current_game_state = GAME_STATE_LOGIN
                                self.active_input_field = "username_login";
                                self.clear_input_fields();
                                return
                            if self.initialize_gameplay_state(level_to_load=1,
                                                              is_new_game_session=True): self.current_game_state = GAME_STATE_GAMEPLAY
                        elif button_text == "Oyun Yükle":
                            if self.load_game_into_gameplay(): self.current_game_state = GAME_STATE_GAMEPLAY
                        elif button_text == "Giriş / Kayıt":
                            self.current_game_state = GAME_STATE_LOGIN;
                            self.active_input_field = "username_login";
                            self.clear_input_fields();
                            self.show_feedback_message("Giriş Yapın veya Kayıt Olun", self.feedback_message_duration)
                        elif button_text == "Çıkış Yap":
                            self.show_feedback_message(f"{self.current_user} çıkış yaptı.",
                                                       self.feedback_message_duration);
                            self.current_user = None
                        elif button_text == "Oyundan Çık":
                            self.running = False
                        break

    def run(self):
        # __init__ içinde initialized_successfully kontrolü yapılıyor ve
        # eğer ana menüde değilsek ve başlangıç başarısızsa, __init__ zaten bir hata mesajı gösterip
        # bu run metodunun düzgün çalışmasını engelleyecek bir durumda olabilir.
        # Ancak yine de bir ön kontrol ekleyelim.
        if not self.initialized_successfully and self.current_game_state not in [GAME_STATE_MAIN_MENU, GAME_STATE_LOGIN,
                                                                                 GAME_STATE_REGISTER]:
            print("FATAL in run(): Game not initialized and not in a pre-game state. Exiting.")
            if self.screen and pygame.get_init():  # Ekran varsa ve pygame çalışıyorsa
                self.screen.fill((50, 0, 0))  # Koyu kırmızı bir arka plan
                error_surf = self.font_medium.render("FATAL ERROR IN RUN. Check Console.", True, (255, 255, 255))
                rect = error_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(error_surf, rect)
                pygame.display.flip()
                pygame.time.wait(3000)  # Mesajı 3 saniye göster
            if pygame.get_init():  # Pygame başlatıldıysa kapat
                pygame.quit()
            return  # run metodundan çık

        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0  # Delta time saniye cinsinden

            # Olayları bir kere al ve ilgili state'in event handler'ına yolla
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Genel feedback mesajı zamanlayıcısını güncelle (her state için geçerli)
            if self.feedback_message_timer > 0:
                self.feedback_message_timer -= 1
                if self.feedback_message_timer == 0:
                    self.feedback_message = ""

            # Oyun durumuna göre olayları, güncellemeyi ve çizimi yönlendir
            if self.current_game_state == GAME_STATE_MAIN_MENU:
                for event in events:  # Main menu eventlerini işle
                    self.handle_main_menu_input(event)
                # Main menu için update (örn: buton hover efektleri için değil ama feedback için)
                self.draw_main_menu()

            elif self.current_game_state == GAME_STATE_LOGIN:
                for event in events:  # Login ekranı eventlerini işle
                    self.handle_login_input(event)
                self.draw_login_screen()

            elif self.current_game_state == GAME_STATE_REGISTER:
                for event in events:  # Register ekranı eventlerini işle
                    self.handle_register_input(event)
                self.draw_register_screen()

            elif self.current_game_state == GAME_STATE_GAMEPLAY:
                if not self.initialized_successfully:
                    # Bu duruma normalde __init__ veya state geçişleri izin vermemeli
                    print("Error: Gameplay state entered but not properly initialized. Returning to main menu.")
                    self.current_game_state = GAME_STATE_MAIN_MENU
                    self.show_feedback_message("Gameplay initialization error.", self.feedback_message_duration)
                    continue  # Döngünün bu adımını atla, sonraki frame'de menü çizilecek

                # Gameplay için olaylar
                for event in events:
                    self.handle_gameplay_events(event)  # Gameplay'e özel event'leri işle

                if not self.game_over_flag:  # Oyun bitmediyse
                    # AI sırasıysa ve AI henüz o tur için tüm hamlelerini bitirmediyse
                    if self.current_player_id == PLAYER_AI_ID and self.running and not self.ai_turn_processed_this_round:
                        self.process_ai_turn()
                    self.update_gameplay()  # Gameplay'e özel güncellemeler

                self.render_gameplay()  # Gameplay ekranını çiz

            # Diğer oyun durumları (eğer eklenirse) buraya eklenebilir
            # elif self.current_game_state == ... :
            #     ...

        # Oyun döngüsü bittiğinde (self.running = False olduğunda)
        print("Exiting game loop...")
        if pygame.get_init():  # Eğer Pygame hala başlatılmışsa, düzgünce kapat
            pygame.quit()
            pygame.quit()

    def clear_input_fields(self):
        self.input_texts = {key: "" for key in self.input_texts};
        self.active_input_field = None

    def draw_login_screen(self):
        self.screen.fill((30, 30, 40));
        title_surf = self.font_large.render("Giriş Yap", True, (200, 220, 255))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 5));
        self.screen.blit(title_surf, title_rect)
        input_width = 300;
        input_height = 35;
        field_spacing = 15;
        label_color = (180, 180, 200);
        input_box_bg = (50, 50, 70);
        text_color = (220, 220, 255);
        active_border = (100, 150, 255);
        inactive_border = (80, 80, 100)
        current_y = self.screen_height // 2 - input_height - field_spacing - 10
        username_label_s = self.font_small.render("Kullanıcı Adı:", True, label_color);
        self.screen.blit(username_label_s, ((self.screen_width - input_width) // 2, current_y - 20))
        username_rect = pygame.Rect((self.screen_width - input_width) // 2, current_y, input_width, input_height);
        self.login_screen_elements["username_input"] = username_rect
        pygame.draw.rect(self.screen, input_box_bg, username_rect, border_radius=3);
        pygame.draw.rect(self.screen, active_border if self.active_input_field == "username_login" else inactive_border,
                         username_rect, 2, border_radius=3)
        username_text_s = self.font_medium.render(self.input_texts["username_login"], True, text_color);
        self.screen.blit(username_text_s,
                         (username_rect.x + 8, username_rect.y + (input_height - username_text_s.get_height()) // 2))
        current_y += input_height + field_spacing * 2
        password_label_s = self.font_small.render("Şifre:", True, label_color);
        self.screen.blit(password_label_s, ((self.screen_width - input_width) // 2, current_y - 20))
        password_rect = pygame.Rect((self.screen_width - input_width) // 2, current_y, input_width, input_height);
        self.login_screen_elements["password_input"] = password_rect
        pygame.draw.rect(self.screen, input_box_bg, password_rect, border_radius=3);
        pygame.draw.rect(self.screen, active_border if self.active_input_field == "password_login" else inactive_border,
                         password_rect, 2, border_radius=3)
        password_display = "*" * len(self.input_texts["password_login"]);
        password_text_s = self.font_medium.render(password_display, True, text_color);
        self.screen.blit(password_text_s,
                         (password_rect.x + 8, password_rect.y + (input_height - password_text_s.get_height()) // 2))
        current_y += input_height + field_spacing * 2 + 10
        btn_width = 140;
        btn_height = 40;
        btn_spacing = 20
        login_btn_rect = pygame.Rect(self.screen_width // 2 - btn_width - btn_spacing // 2, current_y, btn_width,
                                     btn_height);
        self.login_screen_elements["login_button"] = login_btn_rect
        pygame.draw.rect(self.screen,
                         (0, 150, 50) if login_btn_rect.collidepoint(pygame.mouse.get_pos()) else (0, 120, 40),
                         login_btn_rect, border_radius=5)
        login_text_s = self.font_medium.render("Giriş Yap", True, (255, 255, 255));
        self.screen.blit(login_text_s, login_text_s.get_rect(center=login_btn_rect.center))
        register_link_rect = pygame.Rect(self.screen_width // 2 + btn_spacing // 2, current_y, btn_width, btn_height);
        self.login_screen_elements["register_link_button"] = register_link_rect
        pygame.draw.rect(self.screen,
                         (0, 100, 150) if register_link_rect.collidepoint(pygame.mouse.get_pos()) else (0, 80, 120),
                         register_link_rect, border_radius=5)
        reg_text_s = self.font_medium.render("Kayıt Ol", True, (200, 220, 255));
        self.screen.blit(reg_text_s, reg_text_s.get_rect(center=register_link_rect.center))
        current_y += btn_height + 15
        back_btn_rect = pygame.Rect((self.screen_width - (btn_width * 1.5)) // 2, current_y, btn_width * 1.5,
                                    btn_height);
        self.login_screen_elements["back_button_login"] = back_btn_rect
        pygame.draw.rect(self.screen,
                         (150, 50, 50) if back_btn_rect.collidepoint(pygame.mouse.get_pos()) else (120, 40, 40),
                         back_btn_rect, border_radius=5)
        back_text_s = self.font_medium.render("Ana Menüye Dön", True, (255, 200, 200));
        self.screen.blit(back_text_s, back_text_s.get_rect(center=back_btn_rect.center))
        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            bg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 40));
            bg_rect.inflate_ip(20, 10)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA);
            bg_surface.fill((0, 0, 0, 180));
            self.screen.blit(bg_surface, bg_rect.topleft);
            self.screen.blit(feedback_surf, feedback_surf.get_rect(center=bg_rect.center))
        pygame.display.flip()

    def handle_login_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.login_screen_elements.get("username_input") and self.login_screen_elements[
                "username_input"].collidepoint(mouse_pos):
                self.active_input_field = "username_login"
            elif self.login_screen_elements.get("password_input") and self.login_screen_elements[
                "password_input"].collidepoint(mouse_pos):
                self.active_input_field = "password_login"
            elif self.login_screen_elements.get("login_button") and self.login_screen_elements[
                "login_button"].collidepoint(mouse_pos):
                self.attempt_login()
            elif self.login_screen_elements.get("register_link_button") and self.login_screen_elements[
                "register_link_button"].collidepoint(mouse_pos):
                self.current_game_state = GAME_STATE_REGISTER;
                self.active_input_field = "username_reg";
                self.clear_input_fields()
                self.show_feedback_message("Yeni Kullanıcı Kaydı", self.feedback_message_duration)
            elif self.login_screen_elements.get("back_button_login") and self.login_screen_elements[
                "back_button_login"].collidepoint(mouse_pos):
                self.current_game_state = GAME_STATE_MAIN_MENU;
                self.clear_input_fields()
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
                elif len(self.input_texts[self.active_input_field]) < 20:
                    if event.unicode.isalnum() or event.unicode in ['.', '_', '-']:
                        self.input_texts[self.active_input_field] += event.unicode
            if event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_MAIN_MENU; self.clear_input_fields()

    def attempt_login(self):
        username = self.input_texts["username_login"].strip();
        password = self.input_texts["password_login"]
        if not username or not password: self.show_feedback_message("Kullanıcı adı ve şifre giriniz!",
                                                                    self.feedback_message_duration); return
        users = self._load_users()
        if username in users and users[username] == password:
            self.current_user = username;
            self.show_feedback_message(f"Hoşgeldin, {self.current_user}!", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_MAIN_MENU;
            self.clear_input_fields()
        else:
            self.show_feedback_message("Hatalı kullanıcı adı veya şifre!", self.feedback_message_duration);
            self.input_texts["password_login"] = ""

    def draw_register_screen(self):
        self.screen.fill((50, 40, 60));
        title_surf = self.font_large.render("Kayıt Ol", True, (220, 200, 255))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 6));
        self.screen.blit(title_surf, title_rect)
        input_width = 300;
        input_height = 35;
        field_spacing = 10;
        label_color = (180, 180, 200);
        input_box_bg = (50, 50, 70);
        text_color = (220, 220, 255);
        active_border = (100, 150, 255);
        inactive_border = (80, 80, 100)
        current_y = title_rect.bottom + 30
        username_label_s = self.font_small.render("Yeni Kullanıcı Adı:", True, label_color);
        self.screen.blit(username_label_s, ((self.screen_width - input_width) // 2, current_y - 20))
        username_reg_rect = pygame.Rect((self.screen_width - input_width) // 2, current_y, input_width, input_height);
        self.register_screen_elements["username_input_reg"] = username_reg_rect
        pygame.draw.rect(self.screen, input_box_bg, username_reg_rect, border_radius=3);
        pygame.draw.rect(self.screen, active_border if self.active_input_field == "username_reg" else inactive_border,
                         username_reg_rect, 2, border_radius=3)
        username_reg_text_s = self.font_medium.render(self.input_texts["username_reg"], True, text_color);
        self.screen.blit(username_reg_text_s, (
        username_reg_rect.x + 8, username_reg_rect.y + (input_height - username_reg_text_s.get_height()) // 2))
        current_y += input_height + field_spacing * 2
        pass_reg_label_s = self.font_small.render("Şifre:", True, label_color);
        self.screen.blit(pass_reg_label_s, ((self.screen_width - input_width) // 2, current_y - 20))
        password_reg_rect = pygame.Rect((self.screen_width - input_width) // 2, current_y, input_width, input_height);
        self.register_screen_elements["password_input_reg"] = password_reg_rect
        pygame.draw.rect(self.screen, input_box_bg, password_reg_rect, border_radius=3);
        pygame.draw.rect(self.screen, active_border if self.active_input_field == "password_reg" else inactive_border,
                         password_reg_rect, 2, border_radius=3)
        password_reg_display = "*" * len(self.input_texts["password_reg"]);
        password_reg_text_s = self.font_medium.render(password_reg_display, True, text_color);
        self.screen.blit(password_reg_text_s, (
        password_reg_rect.x + 8, password_reg_rect.y + (input_height - password_reg_text_s.get_height()) // 2))
        current_y += input_height + field_spacing * 2
        pass_confirm_label_s = self.font_small.render("Şifre Tekrar:", True, label_color);
        self.screen.blit(pass_confirm_label_s, ((self.screen_width - input_width) // 2, current_y - 20))
        password_confirm_rect = pygame.Rect((self.screen_width - input_width) // 2, current_y, input_width,
                                            input_height);
        self.register_screen_elements["password_input_confirm_reg"] = password_confirm_rect
        pygame.draw.rect(self.screen, input_box_bg, password_confirm_rect, border_radius=3);
        pygame.draw.rect(self.screen,
                         active_border if self.active_input_field == "password_confirm_reg" else inactive_border,
                         password_confirm_rect, 2, border_radius=3)
        password_confirm_display = "*" * len(self.input_texts["password_confirm_reg"]);
        password_confirm_text_s = self.font_medium.render(password_confirm_display, True, text_color);
        self.screen.blit(password_confirm_text_s, (password_confirm_rect.x + 8, password_confirm_rect.y + (
                    input_height - password_confirm_text_s.get_height()) // 2))
        current_y += input_height + field_spacing * 2 + 10
        btn_width = 140;
        btn_height = 40;
        btn_spacing = 20
        register_btn_rect = pygame.Rect(self.screen_width // 2 - btn_width - btn_spacing // 2, current_y, btn_width,
                                        btn_height);
        self.register_screen_elements["register_button"] = register_btn_rect
        pygame.draw.rect(self.screen,
                         (0, 150, 50) if register_btn_rect.collidepoint(pygame.mouse.get_pos()) else (0, 120, 40),
                         register_btn_rect, border_radius=5)
        reg_btn_text_s = self.font_medium.render("Kayıt Ol", True, (255, 255, 255));
        self.screen.blit(reg_btn_text_s, reg_btn_text_s.get_rect(center=register_btn_rect.center))
        login_link_rect = pygame.Rect(self.screen_width // 2 + btn_spacing // 2, current_y, btn_width, btn_height);
        self.register_screen_elements["login_link_button_reg"] = login_link_rect
        pygame.draw.rect(self.screen,
                         (0, 100, 150) if login_link_rect.collidepoint(pygame.mouse.get_pos()) else (0, 80, 120),
                         login_link_rect, border_radius=5)
        login_link_text_s = self.font_medium.render("Giriş Yap", True, (200, 220, 255));
        self.screen.blit(login_link_text_s, login_link_text_s.get_rect(center=login_link_rect.center))
        current_y += btn_height + 15
        back_btn_menu_rect = pygame.Rect((self.screen_width - (btn_width * 1.5)) // 2, current_y, btn_width * 1.5,
                                         btn_height);
        self.register_screen_elements["back_button_menu_reg"] = back_btn_menu_rect
        pygame.draw.rect(self.screen,
                         (150, 50, 50) if back_btn_menu_rect.collidepoint(pygame.mouse.get_pos()) else (120, 40, 40),
                         back_btn_menu_rect, border_radius=5)
        back_menu_text_s = self.font_medium.render("Ana Menüye Dön", True, (255, 200, 200));
        self.screen.blit(back_menu_text_s, back_menu_text_s.get_rect(center=back_btn_menu_rect.center))
        if self.feedback_message_timer > 0 and self.feedback_message:
            feedback_surf = self.font_medium.render(self.feedback_message, True, (255, 200, 0))
            bg_rect = feedback_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 40));
            bg_rect.inflate_ip(20, 10)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA);
            bg_surface.fill((0, 0, 0, 180));
            self.screen.blit(bg_surface, bg_rect.topleft);
            self.screen.blit(feedback_surf, feedback_surf.get_rect(center=bg_rect.center))
        pygame.display.flip()

    def handle_register_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            # .get() ile güvenli erişim, özellikle register_screen_elements henüz tam dolmadıysa
            if self.register_screen_elements.get("username_input_reg") and self.register_screen_elements[
                "username_input_reg"].collidepoint(mouse_pos):
                self.active_input_field = "username_reg"
            elif self.register_screen_elements.get("password_input_reg") and self.register_screen_elements[
                "password_input_reg"].collidepoint(mouse_pos):
                self.active_input_field = "password_reg"
            elif self.register_screen_elements.get("password_input_confirm_reg") and self.register_screen_elements[
                "password_input_confirm_reg"].collidepoint(mouse_pos):
                self.active_input_field = "password_confirm_reg"
            elif self.register_screen_elements.get("register_button") and self.register_screen_elements[
                "register_button"].collidepoint(mouse_pos):
                self.attempt_registration()
            elif self.register_screen_elements.get("login_link_button_reg") and self.register_screen_elements[
                "login_link_button_reg"].collidepoint(mouse_pos):
                self.current_game_state = GAME_STATE_LOGIN;
                self.active_input_field = "username_login";
                self.clear_input_fields()
                self.show_feedback_message("Giriş Yapın", self.feedback_message_duration)
            elif self.register_screen_elements.get("back_button_menu_reg") and self.register_screen_elements[
                "back_button_menu_reg"].collidepoint(mouse_pos):
                self.current_game_state = GAME_STATE_MAIN_MENU;
                self.clear_input_fields()
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
                elif len(self.input_texts[self.active_input_field]) < 20:
                    if event.unicode.isalnum() or event.unicode in ['.', '_', '-']:
                        self.input_texts[self.active_input_field] += event.unicode
            if event.key == pygame.K_ESCAPE: self.current_game_state = GAME_STATE_LOGIN; self.active_input_field = "username_login"; self.clear_input_fields(); self.show_feedback_message(
                "Giriş Ekranı", self.feedback_message_duration)

    def attempt_registration(self):
        username = self.input_texts["username_reg"].strip();
        password = self.input_texts["password_reg"];
        password_confirm = self.input_texts["password_confirm_reg"]
        if not username or not password or not password_confirm: self.show_feedback_message("Tüm alanları doldurun!",
                                                                                            self.feedback_message_duration); return
        if len(username) < 3: self.show_feedback_message("Kullanıcı adı en az 3 karakter olmalı!",
                                                         self.feedback_message_duration); return
        if password != password_confirm: self.show_feedback_message("Şifreler eşleşmiyor!",
                                                                    self.feedback_message_duration); self.input_texts[
            "password_reg"] = ""; self.input_texts["password_confirm_reg"] = ""; return
        if len(password) < 3: self.show_feedback_message("Şifre en az 3 karakter olmalı!",
                                                         self.feedback_message_duration); return
        users = self._load_users()
        if username in users: self.show_feedback_message("Bu kullanıcı adı zaten alınmış!",
                                                         self.feedback_message_duration); return
        users[username] = password
        if self._save_users(users):
            self.show_feedback_message("Kayıt başarılı! Şimdi giriş yapabilirsiniz.", self.feedback_message_duration)
            self.current_game_state = GAME_STATE_LOGIN;
            self.clear_input_fields();
            self.active_input_field = "username_login"
            self.input_texts["username_login"] = username
        else:
            self.show_feedback_message("Kayıt sırasında bir hata oluştu!", self.feedback_message_duration)

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

    def execute_command(self, command):
        cs = False;
        if hasattr(command, 'unit') and command.unit: u = command.unit;
        if u.is_alive():
            if command.execute(): self.command_history.append(command);cs = True
        elif command:
            if command.execute(): cs = True
        if cs:
            self.game_map.units = [x for x in self.game_map.units if x.is_alive()];
            if self.selected_unit and (
                    not self.selected_unit.is_alive() or self.selected_unit.current_state_name != SelectedState.__name__ or (
                    hasattr(self.selected_unit, 'has_acted_this_turn') and self.selected_unit.has_acted_this_turn)):
                self.clear_all_highlights();
                self.selected_unit = None;
            return True
        return False

    def handle_gameplay_events(self, event):
        if self.game_over_flag:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: self.running = False; return
        if self.current_player_id == PLAYER_HUMAN_ID and not self.game_over_flag:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.handle_mouse_click(event.pos)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u and self.current_player_id == PLAYER_HUMAN_ID and self.command_history and not self.game_over_flag:
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
            if self.screen: self.screen.fill((50, 0, 0));s = self.font_medium.render("GAMEPLAY RENDER ERROR", True,
                                                                                     (255, 255, 255));r = s.get_rect(
                center=(self.screen_width // 2, self.screen_height // 2));self.screen.blit(s, r);pygame.display.flip()
            return
        self.screen.fill((30, 30, 30));
        self.game_map.draw(self.screen)
        for t, c in [(self.highlighted_tiles_for_move, (0, 255, 0, 80)),
                     (self.highlighted_tiles_for_attack, (255, 0, 0, 80))]:
            for tile in t: s = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA);s.fill(
                c);self.screen.blit(s, (tile.pixel_x, tile.pixel_y))
        tc = (0, 0, 0);
        lts = f"Lvl:{self.current_level_number} | Turn: P{self.current_player_id}({'Human' if self.current_player_id == PLAYER_HUMAN_ID else 'AI'})"
        if self.game_over_flag:
            cf = self.feedback_message
            if "CONGRATULATIONS" in cf:
                lts = "YOU WIN THE GAME!"
            elif "CLEARED" in cf:
                lts = f"LEVEL {self.current_level_number - 1 if self.current_level_number > MAX_LEVELS else self.current_level_number} CLEARED!"
            elif "FAILED" in cf or "AI Wins" in cf:
                lts = f"GAME OVER - Lvl {self.current_level_number}"
            elif "Draw" in cf:
                lts = f"GAME OVER - Lvl {self.current_level_number}(Draw)"
            else:
                lts = f"GAME OVER - Lvl {self.current_level_number}"
        lts_s = self.font_medium.render(lts, True, tc);
        self.screen.blit(lts_s, (10, 10))
        cts = "'E'End|'K'Save|'U'Undo|'ESC'Menu";
        cts_s = self.font_small.render(cts, True, tc);
        r = cts_s.get_rect(bottomright=(self.screen_width - 10, self.screen_height - 10));
        self.screen.blit(cts_s, r)
        if self.feedback_message_timer > 0 and self.feedback_message:
            fs = self.font_medium.render(self.feedback_message, True, (255, 200, 0));
            bgr = fs.get_rect(center=(self.screen_width // 2, self.screen_height - 30));
            bgr.inflate_ip(20, 10)
            bgs = pygame.Surface(bgr.size, pygame.SRCALPHA);
            bgs.fill((20, 20, 20, 200));
            self.screen.blit(bgs, bgr.topleft);
            self.screen.blit(fs, fs.get_rect(center=bgr.center))
        pygame.display.flip()

    def end_turn(self):
        self.show_feedback_message(f"P{self.current_player_id} Ends Turn", self.feedback_message_duration // 2)
        if self.selected_unit: self.selected_unit.set_state(IdleState(self.selected_unit),
                                                            self);self.selected_unit = None
        self.clear_all_highlights();
        self.command_history.clear()
        np_id = PLAYER_AI_ID if self.current_player_id == PLAYER_HUMAN_ID else PLAYER_HUMAN_ID;
        self.current_player_id = np_id
        self.reset_unit_actions_for_player(self.current_player_id)
        if self.current_player_id == PLAYER_AI_ID: self.ai_turn_processed_this_round = False
        if not self.check_game_over(): self.show_feedback_message(f"P{self.current_player_id}'s Turn",
                                                                  self.feedback_message_duration)

    def check_game_over(self):
        hu_a = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_HUMAN_ID)
        ai_a = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_AI_ID)
        gom = "";
        lc = False
        if not ai_a and hu_a:
            gom = f"LVL {self.current_level_number} CLEARED!";lc = True
        elif not hu_a and ai_a:
            gom = f"LVL {self.current_level_number} FAILED! AI Wins!";self.game_over_flag = True
        elif not hu_a and not ai_a:
            gom = f"LVL {self.current_level_number} FAILED! Draw!";self.game_over_flag = True
        if gom:
            print(gom);
            self.show_feedback_message(gom, 180)
            if lc:
                nl = self.current_level_number + 1
                if nl > MAX_LEVELS:
                    self.show_feedback_message("CONGRATS! All levels beat!", 9999);self.game_over_flag = True
                else:
                    pygame.display.flip();time.sleep(2);
                if not self._initialize_game_for_level(nl, is_new_game_session=False): self.game_over_flag = True
            return self.game_over_flag
        return False

    def process_ai_turn(self):
        if self.current_player_id == PLAYER_AI_ID and not self.ai_turn_processed_this_round and self.running and not self.game_over_flag:
            self.show_feedback_message("AI thinking...", self.feedback_message_duration // 2);
            pygame.display.flip();
            time.sleep(0.1)
            auts = [u for u in self.game_map.units if
                    u.player_id == PLAYER_AI_ID and u.is_alive() and not u.has_acted_this_turn]
            if not auts: print("AI no units/all acted.");self.ai_turn_processed_this_round = True;self.end_turn();return
            aatbat = False
            for au in auts:
                if not self.running or self.game_over_flag: break
                if not au.is_alive() or au.has_acted_this_turn: continue
                pygame.display.flip();
                time.sleep(0.3)
                ac = self.default_ai_strategy.choose_action(au, self)
                if ac:
                    self.show_feedback_message(f"AI:{ac.description}", self.feedback_message_duration)
                    if self.execute_command(ac): au.has_acted_this_turn = True;aatbat = True
                    pygame.display.flip();
                    time.sleep(0.6)
                else:
                    au.has_acted_this_turn = True;print(
                        f"AI Unit {au.id} (Player {au.player_id}) could not find a valid action.")
            if not aatbat and auts: self.show_feedback_message("AI:No valid actions found.",
                                                               self.feedback_message_duration)
            self.ai_turn_processed_this_round = True;
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