# src/main.py
from game_core.game import Game
import os
from game_core.game import SAVE_FILE_NAME # Kullanılmıyor ama kalabilir

if __name__ == "__main__":
    game_width = 15 * 40  # Örnek: 600
    game_height = 10 * 40 # Örnek: 400

    # Oyun her zaman ana menü ile başlasın
    # Eğer bir save dosyası varsa, menüdeki "Oyun Yükle" seçeneği ile yüklenecek.
    game_instance = Game(screen_width=game_width, screen_height=game_height, load_from_save_on_start=False)
    game_instance.run()