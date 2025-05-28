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
        self.command_history = []  # İleride undo için kullanılabilir
        self.highlighted_tiles_for_move = []  # Hareket için vurgulanan tile'lar

        self.tile_size = 40
        self.map_cols = self.screen_width // self.tile_size
        self.map_rows = self.screen_height // self.tile_size

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.unit_factory = UnitFactory()
        self.setup_initial_units()

    def setup_initial_units(self):
        unit1 = self.unit_factory.create_unit("Piyade", 2, 2)
        self.game_map.add_unit(unit1, 2, 2)

        unit2 = self.unit_factory.create_unit("Piyade", 5, 5)  # Farklı birimler de eklenebilir
        self.game_map.add_unit(unit2, 5, 5)

    def execute_command(self, command):
        if command.execute():
            self.command_history.append(command)  # Başarılı komutları tarihe ekle
            return True
        return False

    def highlight_movable_tiles(self, unit):
        self.clear_highlighted_tiles()  # Önceki vurguları temizle
        if unit:
            self.highlighted_tiles_for_move = unit.get_tiles_in_movement_range(self.game_map)

    def clear_highlighted_tiles(self):
        self.highlighted_tiles_for_move = []

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
                if event.button == 1:  # Sol tık
                    mouse_pos = pygame.mouse.get_pos()
                    self.handle_mouse_click(mouse_pos)
            # Örnek: 'U' tuşuna basıldığında son komutu geri al (UNDO)
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_u: # U tuşu
            #         if self.command_history:
            #             last_command = self.command_history.pop()
            #             last_command.undo()
            #             # Seçili birim varsa ve geri alınan komut onunla ilgiliyse durumunu güncelle
            #             if self.selected_unit:
            #                 self.clear_highlighted_tiles()
            #                 self.selected_unit.set_state(type(self.selected_unit.current_state)(self.selected_unit)) # State'i yeniden başlat
            #                 self.highlight_movable_tiles(self.selected_unit)

    def handle_mouse_click(self, mouse_pos):
        clicked_tile = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1])

        active_unit_for_click = self.selected_unit  # Eğer bir birim seçiliyse onunla işlem yap
        if not active_unit_for_click and clicked_tile and clicked_tile.unit_on_tile:
            active_unit_for_click = clicked_tile.unit_on_tile  # Değilse ve tile'da birim varsa onu aktif et

        if active_unit_for_click:
            active_unit_for_click.handle_click(self, clicked_tile)
        elif clicked_tile:  # Boş bir tile'a tıklandı ve seçili birim yoksa (örn: seçimi iptal etmek için)
            if self.selected_unit:  # Bu durum normalde selected_unit state'i tarafından ele alınmalı
                self.selected_unit.handle_click(self, clicked_tile)  # Yine de state'e delege et
            else:  # Hiçbir şey seçili değil ve boş tile'a tıklandı
                self.clear_highlighted_tiles()

    def update(self):
        for unit in self.game_map.units:
            unit.update(self.dt)

    def render(self):
        self.screen.fill((50, 50, 50))
        self.game_map.draw(self.screen)  # Harita normal çiziliyor

        # Hareket edilebilir tile'ları vurgula
        for tile in self.highlighted_tiles_for_move:
            # Vurgu için yarı saydam bir renk
            highlight_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            highlight_surf.fill((0, 255, 0, 100))  # Yeşil, %100 alpha ile (alpha ~39%)
            self.screen.blit(highlight_surf, (tile.pixel_x, tile.pixel_y))

        # Birimler harita çiziminden sonra (veya harita içinde) çizildiği için tekrar çizmeye gerek yok
        # game_map.draw() zaten birimleri de çiziyor.

        pygame.display.flip()