# src/main.py
from game_core.game import Game

if __name__ == "__main__":
    # Ekran boyutlarını Game sınıfı artık kendi içinde tile_size'a göre ayarlayabilir
    # ya da sabit bir boyut verebiliriz.
    # Game constructor'ı artık map_cols ve map_rows'u kendi hesaplıyor.

    # Game sınıfındaki map_cols ve tile_size ile uyumlu ekran boyutu
    # Örnek: 15 tile genişlik * 40 piksel/tile = 600 piksel genişlik
    # Örnek: 10 tile yükseklik * 40 piksel/tile = 400 piksel yükseklik
    game_width = 15 * 40
    game_height = 10 * 40

    game = Game(screen_width=game_width, screen_height=game_height)
    game.run()