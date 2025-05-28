# src/main.py
from game_core.game import Game
import os # Dosya varlığını kontrol etmek için
from game_core.game import SAVE_FILE_NAME # Kayıt dosya ismini game.py'dan alalım

if __name__ == "__main__":
    game_width = 15 * 40
    game_height = 10 * 40

    should_load = False
    if os.path.exists(SAVE_FILE_NAME):
        # Basit bir input ile sorabiliriz, ya da direkt yüklemeyi deneyebiliriz
        # choice = input(f"'{SAVE_FILE_NAME}' bulundu. Yüklensin mi? (e/h): ").lower()
        # if choice == 'e':
        #     should_load = True
        # Şimdilik, dosya varsa direkt yüklemeyi denesin diye bir mantık yok.
        # Kullanıcı 'Y' tuşuna basarak yükleyecek.
        # Ya da başlangıçta sormak için yukarıdaki input kullanılabilir.
        # Biz Game constructor'ına False verip, oyun içinde 'Y' ile yüklemeyi sağlayacağız.
        pass

    game = Game(screen_width=game_width, screen_height=game_height, load_from_save=False) # Başlangıçta yeni oyun
    game.run()