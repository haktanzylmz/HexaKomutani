# src/game_core/game.py
import pygame
from .map import Map
from .unit_factory import UnitFactory


class Game:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")
        self.clock = pygame.time.Clock()
        self.running = False
        self.selected_unit = None  # Hala genel bir seçili birim referansı tutabiliriz, state güncelleyecek.

        self.tile_size = 40
        self.map_cols = self.screen_width // self.tile_size
        self.map_rows = self.screen_height // self.tile_size

        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)
        self.unit_factory = UnitFactory()
        self.setup_initial_units()

    def setup_initial_units(self):
        unit1 = self.unit_factory.create_unit("Piyade", 2, 2)
        self.game_map.add_unit(unit1, 2, 2)

        unit2 = self.unit_factory.create_unit("Piyade", 5, 5)
        self.game_map.add_unit(unit2, 5, 5)

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

    def handle_mouse_click(self, mouse_pos):
        clicked_tile = self.game_map.get_tile_from_pixel_coords(mouse_pos[0], mouse_pos[1])

        # Eğer bir birim seçiliyse, tıklama olayını ona devret
        if self.selected_unit:
            # Önce seçili birimin kendi state'i üzerinden tıklamayı işlemesini sağla
            # Bu, seçimi kaldırma veya hareket etme gibi eylemleri tetikleyebilir.
            self.selected_unit.handle_click(self, clicked_tile)  # 'self' (game_instance) olarak gönderiyoruz

            # Eğer tıklama sonucu seçili birim değişmediyse ve boş bir tile'a tıklanmadıysa
            # ve tıklanan tile'da başka bir birim varsa, o zaman yeni birimi seçmeyi düşünebiliriz.
            # Ama bu mantık zaten SelectedState içinde ele alınmaya çalışıldı.
            # Şimdilik yukarıdaki yeterli olmalı.

        # Eğer hiçbir birim seçili değilse ve bir birimin olduğu hücreye tıklandıysa
        # o birime tıklama olayını göndererek seçilmesini sağla.
        elif clicked_tile and clicked_tile.unit_on_tile:
            clicked_tile.unit_on_tile.handle_click(self, clicked_tile)  # 'self' (game_instance)

        # Eğer boş bir tile'a tıklandıysa ve hiçbir birim seçili değilse, bir şey yapma.
        # Bu durum zaten yukarıdaki koşullara girmez.

    def update(self):
        # Tüm birimlerin durumlarını güncelle (örn: animasyonlar için)
        for unit in self.game_map.units:
            unit.update(self.dt)

    def render(self):
        self.screen.fill((50, 50, 50))
        self.game_map.draw(self.screen)
        pygame.display.flip()