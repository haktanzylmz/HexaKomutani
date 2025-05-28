# src/game_core/game.py
import pygame
from .map import Map
from .unit_factory import UnitFactory


# commands.py'ı import etmeye gerek yok, komutlar state'ler içinde oluşturulup game'e execute için verilecek

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
        self.highlighted_tiles_for_attack = []  # Saldırı için vurgulanan tile'lar

        self.tile_size = 40
        self.map_cols = self.screen_width // self.tile_size
        self.map_rows = self.screen_height // self.tile_size

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.unit_factory = UnitFactory()
        self.setup_initial_units()

    def setup_initial_units(self):
        # Birbirlerine saldırabilsinler diye farklı konumlara koyalım
        unit1 = self.unit_factory.create_unit("Piyade", 2, 2)  # Oyuncu 1
        self.game_map.add_unit(unit1, 2, 2)

        unit2 = self.unit_factory.create_unit("Piyade", 5, 2)  # Oyuncu 2 / Düşman
        # Farklı renk veya takım eklenebilir
        if unit2: unit2.color = (200, 50, 50)  # Kırmızımsı renk
        self.game_map.add_unit(unit2, 5, 2)

    def execute_command(self, command):
        if command.execute():
            self.command_history.append(command)
            # Komut sonrası haritadaki birim listesini güncelle (ölü birimler için)
            self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
            return True
        return False

    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()  # Önceki hareket vurgularını temizle
        if unit and unit.is_alive():
            self.highlighted_tiles_for_move = unit.get_tiles_in_movement_range(self.game_map)

    def highlight_attackable_tiles(self, unit):
        self.clear_highlighted_attack_tiles()  # Önceki saldırı vurgularını temizle
        if unit and unit.is_alive():
            self.highlighted_tiles_for_attack = unit.get_tiles_in_attack_range(self.game_map)

    def clear_highlighted_tiles(self):  # Sadece hareket
        self.highlighted_tiles_for_move = []

    def clear_highlighted_attack_tiles(self):  # Sadece saldırı
        self.highlighted_tiles_for_attack = []

    def clear_all_highlights(self):
        self.clear_highlighted_tiles()
        self.clear_highlighted_attack_tiles()

    def run(self):
        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update()
            self.render()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    self.handle_mouse_click(mouse_pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:  # U tuşu ile UNDO
                    if self.command_history:
                        last_command = self.command_history.pop()
                        last_command.undo()
                        # Undo sonrası seçimi ve vurguları temizle/güncelle
                        if self.selected_unit:
                            if not self.selected_unit.is_alive(): self.selected_unit = None  # Eğer seçili birim öldüyse
                        self.clear_all_highlights()
                        if self.selected_unit:
                            self.selected_unit.set_state(
                                type(self.selected_unit.current_state)(self.selected_unit))  # State'i sıfırla
                            self.highlight_movable_tiles(self.selected_unit)
                            self.highlight_attackable_tiles(self.selected_unit)
                        # Haritadaki birim listesini güncelle (canı geri gelen birim için)
                        # Bu kısım biraz daha karmaşık olabilir, şimdilik basit tutuyoruz.
                        # Örneğin, undo ile canlanan birim haritaya tekrar eklenmeli.
                        # Map.add_unit çağrısı burada kontrol edilebilir.
                        self.game_map.units = [u for u in self.game_map.units if u.is_alive()]
                        # Eğer undo edilen bir saldırı sonucu birim canlandıysa ve listede yoksa ekle
                        # Bu, AttackCommand.undo() içinde daha iyi yönetilebilir.

    def handle_mouse_click(self, mouse_pos):
        clicked_tile = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1])

        active_unit_for_click = self.selected_unit
        if not active_unit_for_click and clicked_tile and clicked_tile.unit_on_tile:
            if clicked_tile.unit_on_tile.is_alive():  # Sadece canlı birimler seçilebilir
                active_unit_for_click = clicked_tile.unit_on_tile

        if active_unit_for_click:
            active_unit_for_click.handle_click(self, clicked_tile)
        elif clicked_tile:
            if self.selected_unit:
                self.selected_unit.handle_click(self, clicked_tile)
            else:
                self.clear_all_highlights()

    def update(self):
        # Ölü birimleri haritadan ve ana listeden temizleme (execute_command içinde de yapılıyor)
        # Bu çift kontrol gibi olabilir ama bazen state değişiklikleri sonrası gerekebilir.
        # self.game_map.units = [u for u in self.game_map.units if u.is_alive()]

        for unit in self.game_map.units:
            unit.update(self.dt)

    def render(self):
        self.screen.fill((50, 50, 50))
        self.game_map.draw(self.screen)

        # Hareket edilebilir tile'ları vurgula (Yarı saydam yeşil)
        for tile in self.highlighted_tiles_for_move:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((0, 255, 0, 100))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        # Saldırılabilir tile'ları vurgula (Yarı saydam kırmızı)
        for tile in self.highlighted_tiles_for_attack:
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((255, 0, 0, 100))
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        pygame.display.flip()