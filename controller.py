from model import GameModel
from view import GameView

from defaults import *
from classes import *


class GameController:
    def __init__(self, model: GameModel, view: GameView) -> None:
        self._model = model
        self._view = view

    def start(self) -> None:
        self._view.start(self, self)

    def update(self) -> None:
        model = self._model
        view = self._view

        match model.game_state:
            case GameState.PREGAME:
                if view.input_leftclick_hold():
                    model.round_start()
                    pyxel.play(1, 3, 0, True)
            case GameState.ONGOING:
                model.aim(view.cursor_pos(), view.input_wasd())
                if view.input_leftclick_hold():
                    if model.shoot():
                        pyxel.play(0,1)
            case GameState.BETWEEN_ROUNDS:
                x, y = view.cursor_pos()
                r, c = coordinate_to_grid(model.rows, model.cols, x, y)
                if (r, c) in model.towers.keys():
                    if view.input_leftclick():
                        model.tower_upgrade(r, c)
                elif view.input_leftclick():
                    model.tower_place(r, c)
                if view.input_leftclick_hold():
                    model.round_start()
            case _:
                pass

        if model.move_projectiles():
            pyxel.play(0, 4)
        model.update()

    def draw(self) -> None:
        model = self._model
        view = self._view

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

        view.draw_cursor()
