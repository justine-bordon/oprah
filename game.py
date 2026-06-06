from model import GameModel
from view import GameView
from controller import GameController

from defaults import *


if __name__ == '__main__':
    model = GameModel.phase5()
    view = GameView(SCREEN_WIDTH, SCREEN_HEIGHT)
    controller = GameController(model, view)
    controller.start()
