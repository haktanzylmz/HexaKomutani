# src/game_core/game.py
import pygame
import time  # AI'nın hamlesini görmek için küçük bir gecikme ekleyebiliriz
from .map import Map
from .unit_factory import UnitFactory
from .ai_strategy import SimpleAggressiveStrategy  # AI Stratejisini import et

PLAYER_HUMAN_ID = 1
PLAYER_AI_ID = 2


class Game:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")
        self.clock = pygame.time.Clock()
        self.running = False
        self.selected_unit = None
        self.command_history = []
        self.highlighted_tiles_for_move = []
        self.highlighted_tiles_for_attack = []

        self.tile_size = 40
        self.map_cols = self.screen_width // self.tile_size
        self.map_rows = self.screen_height // self.tile_size

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.unit_factory = UnitFactory()
        self.ai_strategy = SimpleAggressiveStrategy()  # AI için strateji belirle

        self.current_player_id = PLAYER_HUMAN_ID  # İnsan oyuncu başlar
        self.setup_initial_units()
        self.ai_turn_processed = False  # AI'nın o tur için hamle yapıp yapmadığı

    def setup_initial_units(self):
        # Oyuncu 1 (İnsan)
        unit1 = self.unit_factory.create_unit("Piyade", 2, 2, PLAYER_HUMAN_ID)
        self.game_map.add_unit(unit1, 2, 2)

        # Oyuncu 2 (AI)
        unit2 = self.unit_factory.create_unit("Piyade", self.map_cols - 3, self.map_rows - 3, PLAYER_AI_ID)
        if unit2: unit2.color = (200, 50, 50)  # AI birimi için farklı renk
        self.game_map.add_unit(unit2, self.map_cols - 3, self.map_rows - 3)

        unit3 = self.unit_factory.create_unit("Piyade", self.map_cols - 4, self.map_rows - 4, PLAYER_AI_ID)
        if unit3: unit3.color = (220, 80, 80)
        self.game_map.add_unit(unit3, self.map_cols - 4, self.map_rows - 4)

    def execute_command(self, command):
        if command and command.execute():  # None gelirse diye kontrol
            self.command_history.append(command)
            self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
            # Eğer birim hareket ettiyse veya saldırdıysa, seçimi ve vurguları temizle
            if self.selected_unit:
                if self.selected_unit.current_state.__class__.__name__ != 'SelectedState' or not self.selected_unit.is_alive():
                    self.clear_all_highlights()
                    self.selected_unit = None
            return True
        return False

    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()
        if unit and unit.is_alive() and unit.player_id == self.current_player_id:  # Sadece aktif oyuncunun birimi için
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
        print(f"Player {self.current_player_id} ends turn.")
        if self.selected_unit:
            # Sıra bittiğinde seçili birim varsa seçimini iptal et ve Idle'a döndür
            self.selected_unit.set_state(
                type(self.selected_unit.current_state)(self.selected_unit))  # State'i sıfırla/yeniden gir
            if self.selected_unit.current_state.__class__.__name__ == 'SelectedState':  # Hala seçiliyse Idle yap
                from .unit_states import IdleState  # Döngüsel importu önlemek için burada import
                self.selected_unit.set_state(IdleState(self.selected_unit))
            self.selected_unit = None
        self.clear_all_highlights()

        if self.current_player_id == PLAYER_HUMAN_ID:
            self.current_player_id = PLAYER_AI_ID
            self.ai_turn_processed = False  # AI'nın hamle yapması için sıfırla
            print("AI's turn.")
        else:
            self.current_player_id = PLAYER_HUMAN_ID
            print("Human's turn.")

        # Oyun sonu kontrolü
        self.check_game_over()

    def check_game_over(self):
        human_units_alive = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_HUMAN_ID)
        ai_units_alive = any(u.is_alive() for u in self.game_map.units if u.player_id == PLAYER_AI_ID)

        if not human_units_alive:
            print("GAME OVER! AI Wins!")
            self.running = False  # Oyunu durdur
        elif not ai_units_alive:
            print("GAME OVER! Human Wins!")
            self.running = False  # Oyunu durdur

    def process_ai_turn(self):
        if self.current_player_id == PLAYER_AI_ID and not self.ai_turn_processed:
            print("Processing AI turn...")
            ai_units = [unit for unit in self.game_map.units if unit.player_id == PLAYER_AI_ID and unit.is_alive()]

            if not ai_units:  # AI'nın birimi kalmadıysa
                self.end_turn()
                return

            # Şimdilik AI her tur sadece bir birimiyle bir eylem yapsın
            # Daha karmaşık AI, tüm birimlerini sırayla oynatabilir.

            # Basitçe listedeki ilk canlı AI birimini seçelim (ya da rastgele)
            # Veya bir önceliklendirme yapılabilir.
            processed_action_for_one_unit = False
            for ai_unit in sorted(ai_units,
                                  key=lambda u: u.health):  # Önce canı az olanları oynatmayı deneyebilir (basit taktik)
                if not ai_unit.is_alive(): continue

                action_command = self.ai_strategy.choose_action(ai_unit, self)
                if action_command:
                    print(f"AI is executing: {action_command.description}")
                    self.execute_command(action_command)
                    pygame.display.flip()  # AI hamlesini görmek için ekranı hemen güncelle
                    time.sleep(0.5)  # AI hamlesini görmek için 0.5 saniye bekle
                    processed_action_for_one_unit = True
                    break  # Bu tur için bir AI birimi hamle yaptı, yeterli.

            if not processed_action_for_one_unit:
                print("AI could not perform any action this turn.")

            self.ai_turn_processed = True  # AI bu tur için hamlesini yaptı (veya yapamadı)
            self.end_turn()  # AI sırasını bitir

    def run(self):
        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0

            self.handle_events()  # Önce olayları işle

            if self.current_player_id == PLAYER_AI_ID and self.running:  # Oyun bitmediyse AI sırasını işle
                self.process_ai_turn()

            self.update()  # Sonra oyun durumunu güncelle
            self.render()  # En son çiz

        print("Exiting game...")
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.current_player_id == PLAYER_HUMAN_ID:  # Sadece insan oyuncu sırasındayken fare tıklamalarını işle
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        self.handle_mouse_click(mouse_pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    # Undo sadece insan oyuncu sırasındayken ve onun komutları için mantıklı olabilir
                    if self.current_player_id == PLAYER_HUMAN_ID and self.command_history:
                        # Sadece son komut insan oyuncuya aitse geri al (daha karmaşık kontrol gerekebilir)
                        last_command = self.command_history.pop()  # Basitçe son komutu alıyoruz
                        last_command.undo()
                        if self.selected_unit:
                            if not self.selected_unit.is_alive(): self.selected_unit = None
                        self.clear_all_highlights()
                        if self.selected_unit:
                            self.selected_unit.set_state(type(self.selected_unit.current_state)(self.selected_unit))
                            self.highlight_movable_tiles(self.selected_unit)
                            self.highlight_attackable_tiles(self.selected_unit)
                        self.game_map.units = [u for u in self.game_map.units if u.is_alive()]

                if event.key == pygame.K_e:  # 'E' tuşu ile sırayı bitir
                    if self.current_player_id == PLAYER_HUMAN_ID:
                        self.end_turn()

    def handle_mouse_click(self, mouse_pos):
        if self.current_player_id != PLAYER_HUMAN_ID:  # İnsan oyuncu sırası değilse bir şey yapma
            return

        clicked_tile = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1])

        active_unit_for_click = self.selected_unit
        # Eğer birim seçili değilse ve tıklanan tile'da KENDİ birimi varsa onu seç
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
        for unit in self.game_map.units:  # Tüm birimler için (animasyon vb. için)
            unit.update(self.dt)

        # Oyun sonu kontrolü her update'te veya her tur sonunda yapılabilir.
        # self.check_game_over() # end_turn içine taşıdık

    def render(self):
        self.screen.fill((30, 30, 30))  # Biraz daha koyu bir arka plan
        self.game_map.draw(self.screen)

        for tile in self.highlighted_tiles_for_move:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((0, 255, 0, 80))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        for tile in self.highlighted_tiles_for_attack:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((255, 0, 0, 80))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        # Sıra kimde olduğunu gösteren basit bir yazı
        font = pygame.font.SysFont(None, 30)
        turn_text_str = f"Turn: Player {self.current_player_id} ({'Human' if self.current_player_id == PLAYER_HUMAN_ID else 'AI'})"
        turn_surface = font.render(turn_text_str, True, (255, 255, 255))
        self.screen.blit(turn_surface, (10, 10))

        # 'E' to End Turn
        end_turn_font = pygame.font.SysFont(None, 24)
        end_turn_surface = end_turn_font.render("'E' to End Turn", True, (200, 200, 200))
        self.screen.blit(end_turn_surface, (self.screen_width - end_turn_surface.get_width() - 10, 10))

        pygame.display.flip()