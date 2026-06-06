import pyxel

from typing import Protocol

from defaults import *
from classes import *


class UpdateHandler(Protocol):
    def update(self): ...

class DrawHandler(Protocol):
    def draw(self): ...


class GameView:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def start(self, update_handler: UpdateHandler, draw_handler: DrawHandler) -> None:
        self.update_handler = update_handler
        self.draw_handler = draw_handler

        pyxel.init(self.width, self.height, title='Zuma: Tower Defense', fps=FPS)
        pyxel.load("effects.pyxres")
        # pyxel.play(1, 0, 0, True)
        pyxel.run(update_handler.update, draw_handler.draw)

    def stop(self) -> None:
        pyxel.stop()

    def cursor_pos(self) -> tuple[int, int]: return pyxel.mouse_x, pyxel.mouse_y
    def input_leftclick(self) -> bool:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return True  
        else:
            return False
    def input_leftclick_hold(self) -> bool: 
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT, 1, 1):
            return True  
        else:
            return False
    def input_space(self) -> bool: return True if pyxel.btnp(pyxel.KEY_SPACE) else False
    def input_wasd(self) -> Direction | None:
        if pyxel.btnp(pyxel.KEY_W):
            return Direction.UP
        if pyxel.btnp(pyxel.KEY_D):
            return Direction.RIGHT
        if pyxel.btnp(pyxel.KEY_A):
            return Direction.LEFT
        if pyxel.btnp(pyxel.KEY_S):
            return Direction.DOWN
        return None

    def reset_screen(self) -> None:
        pyxel.cls(BACKGROUND_COLOR)

    def draw_cursor(self) -> None:
        pyxel.mouse(True)

    def draw_border(self) -> None:
        pyxel.rectb(BORDER_WIDTH, BORDER_WIDTH, GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE, TEXT_COLOR)

    def draw_tile_highlight(self, r: int, c: int, color: int) -> None:
        (x, y), _ = tile_corners(r, c)
        pyxel.rectb(x, y, TILE_SIZE, TILE_SIZE, color)

    def draw_path(self, path: Path) -> None:
        r = path.start_r
        c = path.start_c
        for i in range(len(path.flow) + 1):
            if i > 0:
                dir = path.flow[i - 1].value
                r += dir[0]
                c += dir[1]
            tile = path.contents[i]
            (x, y), _ = tile_corners(r, c)
            tile_color = (COLOR_EMPTY if tile.color is None else tile.color)
            if not isinstance(tile, DefaultEnemy):
                pyxel.rect(x, y, TILE_SIZE, TILE_SIZE, tile_color)
            if isinstance(tile, DefaultEnemy):
                pyxel.pal(15, tile_color)
                if type(tile) is DefaultEnemy:
                    pyxel.blt(x+24, y+24, 0, 0, 0, TILE_SIZE//4, TILE_SIZE//4, 0, scale = 4)
                elif type(tile) is RegeneratorEnemy:
                    pyxel.blt(x+24, y+24, 0, 16, 0, TILE_SIZE//4, TILE_SIZE//4, 0, scale = 4)
                    
                    acquired_hp = tile.current_hp - ENEMY_HITPOINTS
                    for hps in range(acquired_hp):
                        overlay_x = x + 6 + (hps * 8)
                        overlay_y = y + TILE_SIZE - 12
                        
                        pyxel.pal()
                        pyxel.blt(overlay_x, overlay_y, 0, 0, 16, 8, 8, 0)
                        pyxel.pal(15, tile_color)
                elif type(tile) is ChameleonEnemy:
                    pyxel.blt(x+24, y+24, 0, 32, 0, TILE_SIZE//4, TILE_SIZE//4, 0, scale = 4)
                    
                pyxel.pal()
                
            if path.in_tunnel(i):
                pyxel.dither(0.5)
                pyxel.rect(x, y, TILE_SIZE, TILE_SIZE, TUNNEL_COLOR)
                pyxel.dither(1)

    def draw_towers(self, towers: list[Shooter]):
        for tower in towers:
            x, y = tower.bullet_pos
            pyxel.circ(tower.pos_x, tower.pos_y, TOWER_RADIUS, TOWER_UPGRADED_COLOR if tower.is_upgraded else TOWER_COLOR)
            pyxel.circ(x, y, tower.bullet.size, tower.color)
            colors = [tower.color, tower.color2] if tower.is_upgraded else [tower.color]
            for pos, color in zip(tower.bullet_positions, colors):
                x, y = pos
                pyxel.circ(x, y, tower.bullet.size, color)

    def draw_player(self, player: Shooter) -> None:
        pyxel.circ(player.pos_x, player.pos_y, PLAYER_RADIUS, PLAYER_COLOR)
        colors = [player.color, player.color2] if player.is_upgraded else [player.color]
        for pos, color in zip(player.bullet_positions, colors):
            x, y = pos
            pyxel.circ(x, y, player.bullet.size, color)

    def draw_projectile(self, projectile: Projectile) -> None:
        pyxel.circ(projectile.pos_x, projectile.pos_y, projectile.bullet.size, projectile.color)

    def draw_press_to_start(self) -> None:
        pyxel.text((self.width / 2) - 43, self.height - (BORDER_WIDTH / 2) - 3, "Press [SPACE] to Start", TEXT_COLOR)

    def draw_lives(self, amt: int) -> None:
        pyxel.text(BORDER_WIDTH / 2, (BORDER_WIDTH / 2) + 5, f"Lives: {amt}", TEXT_COLOR)

    def draw_rounds(self, current: int, total: int) -> None:
        pyxel.text(BORDER_WIDTH / 2, (BORDER_WIDTH / 2) - 8, f"Round: {current} / {total}", TEXT_COLOR)

    def draw_exp(self, amt: int) -> None:
        pyxel.text(self.width - BORDER_WIDTH + 1, (BORDER_WIDTH / 2) - 8, f"EXP: {amt}", TEXT_COLOR)

    def draw_winner(self) -> None:
        width = 50
        height = 50
        pyxel.rect((self.width - width) / 2, (self.height - height) / 2, width, height, BACKGROUND_COLOR)
        pyxel.text((self.width / 2) - 15, (self.height / 2) - 2, "YOU WIN!", TEXT_COLOR)

    def draw_gameover(self) -> None:
        width = 50
        height = 50
        pyxel.rect((self.width - width) / 2, (self.height - height) / 2, width, height, BACKGROUND_COLOR)
        pyxel.text((self.width / 2) - 17, (self.height / 2) - 2, "GAME OVER", TEXT_COLOR)
        
    def draw_main_menu(self) -> None:
        self.reset_screen()
        pyxel.text((self.width / 2) - 40, (self.height / 2) - 20, "ZUMA TOWER DEFENSE", TEXT_COLOR)
        pyxel.text((self.width / 2) - 40, (self.height / 2) + 10, "[1] CAMPAIGN MODE", COLOR_SUCCESS)
        pyxel.text((self.width / 2) - 40, (self.height / 2) + 25, "[2] ENDLESS MODE", COLOR_ERROR)
        pyxel.text((self.width / 2) - 40, (self.height / 2) + 40, "[L] LEADERBOARD", COLOR_UPGRADE)
        

    def draw_pause(self) -> None:
        pyxel.dither(0.5)
        pyxel.rect(0, 0, self.width, self.height, BACKGROUND_COLOR)
        pyxel.dither(1)
        pyxel.text((self.width / 2) - 15, self.height / 2, "PAUSED", TEXT_COLOR)

    def draw_name_input(self, current_name: str) -> None:
        self.reset_screen()
        pyxel.text((self.width / 2) - 40, (self.height / 2) - 20, "ENTER YOUR NAME:", TEXT_COLOR)
        pyxel.text((self.width / 2) - 15, (self.height / 2), current_name + "_", COLOR_SUCCESS)
        pyxel.text((self.width / 2) - 60, (self.height / 2) + 30, "PRESS [ENTER] TO SUBMIT", TEXT_COLOR)

    def draw_leaderboard(self, leaderboard_data: list) -> None:
        self.reset_screen()
        pyxel.text((self.width / 2) - 25, BORDER_WIDTH, "TOP SCORES", COLOR_UPGRADE)
        
        y_offset = BORDER_WIDTH + 30
        for i, entry in enumerate(leaderboard_data):
            text = f"{i+1}. {entry['name'].upper()} - Score: {entry['score']} (Rnd: {entry['round']})"
            pyxel.text(BORDER_WIDTH + 20, y_offset, text, TEXT_COLOR)
            y_offset += 15

    def draw_test(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) - 8, txt, TEXT_COLOR)
    def draw_test2(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) - 2, txt, TEXT_COLOR)
    def draw_test3(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) + 5, txt, TEXT_COLOR)
