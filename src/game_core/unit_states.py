# src/game_core/unit_states.py
import pygame  # handle_click içinde game.game_map gibi erişimler için gerekebilir


class UnitState:
    """
    Birim durumları için soyut ana sınıf (veya arayüz gibi düşünebiliriz).
    """

    def __init__(self, unit):
        self.unit = unit

    def enter_state(self):
        """Bu duruma girildiğinde yapılacak işlemler."""
        # print(f"{self.unit.unit_type} entering {self.__class__.__name__}")
        pass

    def exit_state(self):
        """Bu durumdan çıkıldığında yapılacak işlemler."""
        # print(f"{self.unit.unit_type} exiting {self.__class__.__name__}")
        pass

    def handle_click(self, game_instance, clicked_tile):
        """Bu durumdayken bir tıklama olduğunda ne yapılacağını belirler."""
        pass

    def update(self, dt):
        """Bu durumdayken her frame'de yapılacak güncellemeler (örn: animasyon)."""
        pass


class IdleState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def handle_click(self, game_instance, clicked_tile):
        # Boşta duran birime tıklandıysa ve tıklanan hücrede bu birim varsa, onu Seçili duruma geçir.
        if clicked_tile and clicked_tile.unit_on_tile == self.unit:
            self.unit.set_state(SelectedState(self.unit))
            game_instance.selected_unit = self.unit  # Game'e seçili birimi bildir
            # print(f"{self.unit.unit_type} is now selected.")
        # Başka bir durum (örn: boş bir tile'a tıklama) IdleState'te bir şey yapmaz.


class SelectedState(UnitState):
    def __init__(self, unit):
        super().__init__(unit)

    def enter_state(self):
        super().enter_state()
        self.unit.is_graphically_selected = True  # Görsel seçim için

    def exit_state(self):
        super().exit_state()
        self.unit.is_graphically_selected = False  # Görsel seçimi kaldır

    def handle_click(self, game_instance, clicked_tile):
        if not clicked_tile:  # Harita dışına tıklanırsa seçimi iptal et
            self.unit.set_state(IdleState(self.unit))
            if game_instance.selected_unit == self.unit:
                game_instance.selected_unit = None
            return

        # Seçili birim varken:
        # 1. Kendi üzerine tekrar tıklanırsa: Seçimi kaldır (IdleState'e dön)
        if clicked_tile.unit_on_tile == self.unit:
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None  # Game'den seçili birimi kaldır
            # print(f"{self.unit.unit_type} is now idle.")

        # 2. Boş ve yürünebilir bir hücreye tıklanırsa: Hareket et
        elif clicked_tile.is_walkable and not clicked_tile.unit_on_tile:
            # Şimdilik basit hareket, menzil kontrolü yok
            # İleride Command Pattern ile burası daha gelişmiş bir hareket komutunu tetikleyebilir
            # ve MovingState'e geçilebilir.
            if game_instance.game_map.move_unit(self.unit, clicked_tile.x_grid, clicked_tile.y_grid):
                # print(f"{self.unit.unit_type} moved to ({clicked_tile.x_grid}, {clicked_tile.y_grid})")
                self.unit.set_state(IdleState(self.unit))  # Hareket sonrası Idle'a dön
                game_instance.selected_unit = None
            else:
                # Hareket başarısız olursa (örn: ulaşılamaz bir yer), seçili kalabilir veya idle'a dönebilir.
                # Şimdilik seçili kalsın.
                print(f"Could not move {self.unit.unit_type} to ({clicked_tile.x_grid}, {clicked_tile.y_grid})")

        # 3. Başka bir birimin olduğu hücreye tıklanırsa:
        elif clicked_tile.unit_on_tile and clicked_tile.unit_on_tile != self.unit:
            # Şimdilik bir şey yapma (belki saldırı?)
            # Ya da seçimi iptal edip diğer birimi seçebiliriz. Şimdilik sadece seçimi iptal et.
            print(f"Target tile occupied by {clicked_tile.unit_on_tile.unit_type}. Deselecting current unit.")
            self.unit.set_state(IdleState(self.unit))
            game_instance.selected_unit = None
            # İsteğe bağlı olarak, tıklanan diğer birimi seçebiliriz:
            # new_selected_unit = clicked_tile.unit_on_tile
            # new_selected_unit.set_state(SelectedState(new_selected_unit))
            # game_instance.selected_unit = new_selected_unit

# Gelecekte eklenecek durumlar:
# class MovingState(UnitState): ...
# class AttackingState(UnitState): ...