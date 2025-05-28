# src/game_core/game.py
import pygame
from .map import Map # Aynı klasördeki map.py'dan Map sınıfını import et

class Game:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hexa Komutanı")
        self.clock = pygame.time.Clock()
        self.running = False

        # Harita ayarları
        self.tile_size = 40 # Her bir hücrenin boyutu (piksel)
        self.map_rows = 10
        self.map_cols = 15
        self.game_map = Map(self.map_rows, self.map_cols, self.tile_size)

    def run(self):
        self.running = True
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0 # Delta time saniye cinsinden

            self.handle_events()
            self.update()
            self.render()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        # Şimdilik burada güncellenecek bir şey yok
        pass

    def render(self):
        self.screen.fill((50, 50, 50))  # Arka plan rengi
        self.game_map.draw(self.screen) # Haritayı çiz
        pygame.display.flip() # Ekrana yansıt