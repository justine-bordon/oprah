from model import GameModel
from view import GameView

from defaults import *
from classes import *

def get_char() -> str:
    for key in range(pyxel.KEY_A, pyxel.KEY_Z + 1):
        if pyxel.btnp(key):
            return chr(key - pyxel.KEY_A + 97)
    if pyxel.btnp(pyxel.KEY_SPACE): return " "
    if pyxel.btnp(pyxel.KEY_BACKSPACE): return "BACKSPACE"
    return ""
    

class GameController:
    def __init__(self, model: GameModel, view: GameView) -> None:
        self._model = model
        self._view = view

    def start(self) -> None:
        self._view.start(self, self)

    def reset_game(self) -> None:
        self._model = GameModel.phase6()

    def update(self) -> None:
        model = self._model
        view = self._view

        match model.game_state:
            case GameState.MAIN_MENU:
                if pyxel.btnp(pyxel.KEY_1):
                    model.game_mode = GameMode.CAMPAIGN
                    model.game_state = GameState.PREGAME
                elif pyxel.btnp(pyxel.KEY_2):
                    model.game_mode = GameMode.ENDLESS
                    model.game_state = GameState.PREGAME
                elif pyxel.btnp(pyxel.KEY_L):
                    model.load_leaderboard()
                    model.game_state = GameState.LEADERBOARD
                    
            case GameState.PREGAME:
                if view.input_space():
                    model.round_start()
                    pyxel.play(1, 3, 0, True)
                    
            case GameState.ONGOING:
                if view.input_space():
                    model.game_state = GameState.PAUSED
                    return
                    
                model.aim(view.cursor_pos(), view.input_wasd())
                if view.input_leftclick_hold():
                    if model.shoot():
                        pyxel.play(0,1)
                        
            case GameState.PAUSED:
                if view.input_space():
                    model.game_state = GameState.ONGOING
                    
            case GameState.BETWEEN_ROUNDS:
                x, y = view.cursor_pos()
                r, c = coordinate_to_grid(model.rows, model.cols, x, y)
                if (r, c) in model.towers.keys():
                    if view.input_leftclick():
                        model.tower_upgrade(r, c)
                elif view.input_leftclick():
                    model.tower_place(r, c)
                if view.input_space():
                    model.round_start()
                    
            case GameState.WINNER | GameState.LOSER:
                if view.input_space():
                    model.game_state = GameState.GAME_OVER
                    
            case GameState.GAME_OVER:
                char = get_typed_char()
                if char == "BACKSPACE":
                    model.player_name = model.player_name[:-1]
                elif char and len(model.player_name) < 10:
                    model.player_name += char
                    
                if pyxel.btnp(pyxel.KEY_RETURN):
                    if model.player_name.strip() == "":
                        model.player_name = "ANONYMOUS"
                    model.save_score()
                    model.load_leaderboard()
                    model.game_state = GameState.LEADERBOARD
                    
            case GameState.LEADERBOARD:
                if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_ESCAPE):
                    self.reset_game() 
                    
            case _:
                pass

        if model.move_projectiles():
            pyxel.play(0, 4)
        model.update()

    def draw(self) -> None:
        model = self._model
        view = self._view
        
        if model.game_state == GameState.MAIN_MENU:
            view.draw_main_menu()
            view.draw_cursor()
            return
            
        elif model.game_state == GameState.GAME_OVER:
            view.draw_game_over(model.player_name)
            return
            
        elif model.game_state == GameState.LEADERBOARD:
            view.draw_leaderboard(model.leaderboard)

        view.reset_screen()
        for path in model.paths:
            view.draw_path(path)
        view.draw_player(model.player)
        view.draw_towers(list(model.towers.values()))
        view.draw_border()
        view.draw_lives(model.lives)
        view.draw_rounds(model.current_round + 1, model.total_rounds)
        view.draw_exp(model.exp)

        match model.game_state:
            case GameState.PREGAME:
                view.draw_press_to_start()
            case GameState.ONGOING:
                for projectile in model.projectile_list:
                    view.draw_projectile(projectile)
            case GameState.BETWEEN_ROUNDS:
                x, y = view.cursor_pos()
                r, c = coordinate_to_grid(model.rows, model.cols, x, y)
                if (r in range(model.rows)) and (c in range(model.cols)):
                    if (r, c) in model.towers.keys() and model.allow_upgrades and not model.towers[(r, c)].is_upgraded:
                        color = COLOR_UPGRADE
                    elif model.tower_placeable(r, c):
                        color = COLOR_SUCCESS
                    else:
                        color = COLOR_ERROR
                    view.draw_tile_highlight(r, c, color)
                view.draw_press_to_start()
            case GameState.WINNER:
                view.draw_winner()
            case GameState.LOSER:
                view.draw_gameover()
                
        if model.game_state == GameState.PAUSED:
            view.draw_pause()

        view.draw_cursor()
