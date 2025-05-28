# src/main.py
from game_core.game import Game # game_core paketinden Game sınıfını import et

if __name__ == "__main__":
    # Ekran boyutlarını burada belirleyebiliriz
    # Harita boyutlarına göre dinamik de ayarlanabilir
    screen_w = 600 # 15 cols * 40 tile_size
    screen_h = 400 # 10 rows * 40 tile_size

    # Eğer harita boyutu ve tile_size game.py içindeyse:
    # game_instance = Game(screen_width_param, screen_height_param)
    # Ya da Game constructor'ını parametresiz yapıp sabit değerler kullanabiliriz
    # Şimdilik Game içindeki değerleri kullanalım ve main.py'dan boyut gönderelim
    # Game.__init__ içinde bu parametreleri alıp map_cols ve map_rows'u hesaplayabiliriz.
    # Ya da direkt Game içinde map_cols*tile_size olarak set edebiliriz.

    # Game sınıfındaki map_cols ve tile_size ile uyumlu ekran boyutu
    # screen_width = 15 * 40 -> 600
    # screen_height = 10 * 40 -> 400

    game = Game(screen_width=15*40, screen_height=10*40) # Game sınıfındaki harita boyutlarına göre
    game.run()