# src/game_core/tile.py
import pygame

class Tile:
    def __init__(self, x, y, size, color=(200, 200, 200)): # x, y piksel konumu değil, ızgara konumu
        self.x_grid = x  # Izgaradaki x konumu
        self.y_grid = y  # Izgaradaki y konumu
        self.size = size # Hücrenin boyutu (piksel cinsinden)
        self.color = color
        # Şimdilik hexagonal çizimi basitleştirmek için kare hücreler çizelim
        # Gerçek piksel konumu harita tarafından hesaplanabilir veya burada tutulabilir
        self.rect = pygame.Rect(self.x_grid * self.size, self.y_grid * self.size, self.size, self.size)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 1) # Kenarlık