from game_core.game import Game
import os

if __name__ == "__main__":
    game_width = 15 * 40
    game_height = 10 * 40

    game_instance = Game(screen_width=game_width, screen_height=game_height)

    game_instance.run()