import pyxel
import json


# Visuals
pyxel.colors[9] = 0xDD885D
pyxel.colors[13] = 0x505050
pyxel.colors[14] = 0x00072D

GRID_COLS = 8
GRID_ROWS = 6

BORDER_WIDTH = 50
TILE_SIZE = 64

BACKGROUND_COLOR = 0
COLOR_RED = 8
COLOR_ORANGE = 9
COLOR_YELLOW = 10
COLOR_GREEN = 11
COLOR_BLUE = 12
COLOR_PURPLE = 2
COLOR_EMPTY = 13
TUNNEL_COLOR = 14

SCREEN_WIDTH = (GRID_COLS * TILE_SIZE) + (BORDER_WIDTH * 2)
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) +  (BORDER_WIDTH * 2)
SCREEN_DIAGONAL = ((SCREEN_WIDTH ** 2) + (SCREEN_HEIGHT ** 2)) ** 0.5

PLAYER_X = SCREEN_WIDTH // 2
PLAYER_Y = SCREEN_WIDTH // 2
PLAYER_RADIUS = 8
PLAYER_COLOR = 7

TOWER_RADIUS = 8
TOWER_COLOR = 6
TOWER_UPGRADED_COLOR = 10
COLOR_UPGRADE = 10
COLOR_SUCCESS = 3
COLOR_ERROR = 8

TEXT_COLOR = 7


# Base Settings
with open("settings.json", "r") as file:
    data = json.load(file)
    PLAYER_LIVES = data["lives"]
    ENEMY_COUNT = data["enemies_per_round"]
    REGENERATOR_TILES = data["enemy_regenerator_tiles"]
    CHAMELEON_CHANCE = data["enemy_chameleon_frequency"]

PLAYER_FIRERATE = 0.9  # bullets per game tick (30 FPS)
BULLET_DAMAGE = 1
BULLET_SIZE = 5  # in pixels
BULLET_SPEED = SCREEN_DIAGONAL // 150  # pixels per game tick
BULLET_HITS = 1  # piercing behavior
BULLET_RANGE = SCREEN_DIAGONAL
TOWER_FIRERATE = 0.5
ENEMY_MOVE_DELAY = 60  # in game ticks
ENEMY_HITPOINTS = 1
ENEMY_EXP_YIELD = 1
FPS = 30

AIM_DISTANCE = 15  # initial distance of the bullet from the player
TOWER_COST = 5
TOWER_UPGRADE_COST = 5
