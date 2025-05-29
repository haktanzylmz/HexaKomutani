# src/main.py
from game_core.game import Game
import os  # os modülü, eğer ileride dosya yolu işlemleri için gerekirse diye kalabilir, şu an doğrudan kullanılmıyor.

if __name__ == "__main__":
    # Ekran ve oyun alanı boyutları
    # Bu değerler Game sınıfı içinde de tile_size'a göre hesaplanabilir veya
    # seviye dosyalarından okunabilir. Şimdilik burada sabit bırakıyoruz.
    # Örnek: 15 tile genişlik * 40 piksel/tile = 600 piksel genişlik
    # Örnek: 10 tile yükseklik * 40 piksel/tile = 400 piksel yükseklik
    game_width = 15 * 40  # 600
    game_height = 10 * 40  # 400

    # Oyunu başlatırken load_from_save_on_start=False veriyoruz,
    # çünkü oyun her zaman ana menü ile başlayacak ve yükleme işlemi
    # ana menüdeki "Oyun Yükle" butonu ile yapılacak.
    game_instance = Game(screen_width=game_width, screen_height=game_height, load_from_save_on_start=False)


    game_instance.run()