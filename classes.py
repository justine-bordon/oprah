from __future__ import annotations

from enum import IntEnum, Enum
from dataclasses import dataclass
from typing import Protocol

from random import Random

from defaults import *


class Direction(Enum):
    _value_: tuple[int, int]
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class Color(IntEnum):
    _value_: int
    RED = COLOR_RED
    ORANGE = COLOR_ORANGE
    YELLOW = COLOR_YELLOW
    GREEN = COLOR_GREEN
    BLUE = COLOR_BLUE
    PURPLE = COLOR_PURPLE

class ShooterDirection(Enum):
    UPWARD = 1
    WASD = 2
    CURSOR = 3

class GameState(Enum):
    MAIN_MENU = -1
    PREGAME = 0
    ONGOING = 1
    PAUSED = 1.5
    BETWEEN_ROUNDS = 2
    WINNER = 3
    LOSER = 4
    GAME_OVER = 5
    LEADERBOARD = 6

class GameMode(Enum):
    CAMPAIGN = 0
    ENDLESS = 1
    
class Tile(Protocol):
    @property
    def color(self) -> Color | None: ...

class GridTile:
    @property
    def color(self) -> Color | None: return None

class PathTile:
    @property
    def color(self) -> Color | None: return None


class DefaultEnemy:
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = 0) -> None:
        self._color = None
        self._special_rate = special_rate

    @property
    def color(self) -> Color | None: return self._color
    @property
    def current_hp(self) -> int: return self._current_hp
    @property
    def exp_yield(self) -> int: return self._exp_yield

    def initialize(self, color_options: list[Color], base_hp: int, exp_yield: int, rng: Random) -> None:
        self._rng = rng

        self._current_hp = base_hp
        self._exp_yield = exp_yield

        self._lifetime = 0  # in ticks (30 FPS)
        self._tiles_traveled = 0
        self._color_options = color_options
        self.randomize_color()

    def randomize_color(self) -> None:
        self._color = self._rng.choice(self._color_options)

    def travel(self) -> None:
        self._tiles_traveled += 1

    def wait(self) -> None:
        self._lifetime += 1

    def modify_hp(self, amt: int) -> None:
        self._current_hp = max(0, self._current_hp + amt)

class RegeneratorEnemy(DefaultEnemy):
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = REGENERATOR_TILES) -> None:
        super().__init__(color_options, base_hp, exp_yield, rng, special_rate)

    def travel(self) -> None:
        self._tiles_traveled += 1
        if (self._tiles_traveled > 0) & (self._tiles_traveled % self._special_rate == 0):
            self.modify_hp(1)
            self._tiles_traveled = 0

class ChameleonEnemy(DefaultEnemy):
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = CHAMELEON_CHANCE) -> None:
        super().__init__(color_options, base_hp, exp_yield, rng, special_rate)

    def wait(self) -> None:
        self._lifetime += 1
        if self._rng.randint(0, 3000) < self._special_rate:
            old = self._color
            while self._color == old:
                self.randomize_color()
            self._lifetime = 0


@dataclass
class Bullet:
    damage: int = BULLET_DAMAGE
    size: int = BULLET_SIZE
    speed: float = BULLET_SPEED
    hits: int = BULLET_HITS
    range: float = BULLET_RANGE

    @classmethod
    def copy(cls, bullet: Bullet) -> Bullet:
        return cls(damage = bullet.damage, size = bullet.size, speed = bullet.speed, hits = bullet.hits, range = bullet.range)

@dataclass
class Projectile:
    pos_x: float
    pos_y: float
    vec_x: float
    vec_y: float
    bullet: Bullet
    color: Color

class Shooter:
    def __init__ (self, fire_rate: float, direction: ShooterDirection, rng: Random, bullet: Bullet = Bullet()):
        self._rng = rng
        self._fire_rate = fire_rate
        self._bullet = bullet
        self._direction = direction
        self._color = Color.RED
        self._color2 = Color.RED
        self._aim_x = 0
        self._aim_y = -bullet.speed
        self._cooldown = 0
        self._is_upgraded: bool = False  # shoots two bullets when upgraded, one if its not

    @property
    def fire_rate(self) -> float: return self._fire_rate
    @property
    def base_cooldown(self) -> int: return int(FPS // self.fire_rate)
    @property
    def ready(self) -> bool: return (self._cooldown == 0)
    @property
    def bullet(self) -> Bullet: return Bullet.copy(self._bullet)
    @property
    def direction(self) -> ShooterDirection: return self._direction
    @property
    def color(self) -> Color: return self._color
    @property
    def aim_x(self) -> float: return self._aim_x
    @property
    def aim_y(self) -> float: return self._aim_y
    @property
    def pos_x(self) -> float: return self._pos_x
    @property
    def pos_y(self) -> float: return self._pos_y
    @property
    def bullet_pos(self) -> tuple[float, float]:
        relative_pos = normalize(self.aim_x, self.aim_y, AIM_DISTANCE)
        x = self.pos_x + relative_pos[0]
        y = self.pos_y + relative_pos[1]
        return x, y
    @property
    def color2(self) -> Color: return self._color2
    @property
    def is_upgraded(self) -> bool: return self._is_upgraded
    @property
    def bullet_positions(self) -> list[tuple[float, float]]:
        x, y = self.bullet_pos
        if not self._is_upgraded:
            return [(x, y)]
        else:
            ax, ay = self.aim_x, self.aim_y
            perp = normalize(-ay, ax, 5)

            return [
                (x + perp[0], y + perp[1]),
                (x - perp[0], y - perp[1])
            ]

    def place(self, x: float, y: float) -> None:
        self._pos_x = x
        self._pos_y = y

    def aim(self, vec_x: float, vec_y: float) -> None:
        aim = normalize(vec_x, vec_y, self.bullet.speed)
        self._aim_x = aim[0]
        self._aim_y = aim[1]

    def start_cooldown(self) -> None:
        self._cooldown = self.base_cooldown

    def cooldown_tick(self) -> None:
        self._cooldown -= 1

    def randomize_color(self, color_list: list[Color]) -> None:
        self._color = self._rng.choice(color_list)
        if self._is_upgraded and len(color_list) > 1:
            old = self._color
            while self._color2 == old:
                self._color2 = self._rng.choice(color_list)
        else:
            self._color2 = self._rng.choice(color_list)

    def copy(self) -> Shooter:
        return Shooter(self.fire_rate, self.direction, self._rng, self.bullet)
    
    def upgrade(self) -> None:
        self._is_upgraded = True

    @classmethod
    def base_player(cls, direction: ShooterDirection, rng: Random) -> Shooter:
        return cls(PLAYER_FIRERATE, direction, rng)

    @classmethod
    def base_tower(cls, direction: ShooterDirection, rng: Random) -> Shooter:
        return cls(TOWER_FIRERATE, direction, rng)

@dataclass
class Tunnel:
    start_idx: int
    length: int

@dataclass
class Path:
    start_r: int
    start_c: int
    flow: list[Direction]
    tunnels: list[Tunnel]
    contents: list[PathTile | DefaultEnemy]

    def in_tunnel(self, idx: int) -> bool:
        for tunnel in self.tunnels:
            start = tunnel.start_idx
            end = start + tunnel.length
            if idx in range(start, end):
                return True
        return False

    def rc_to_idx(self, r: int, c: int) -> int:
        _r = self.start_r
        _c = self.start_c
        for i in range(len(self.flow) + 1):
            if i > 0:
                dir = self.flow[i-1].value
                _r += dir[0]
                _c += dir[1]
            if (_r, _c) == (r, c):
                return i
        return -1

@dataclass
class Stage:
    paths: list[Path]
    rounds: list[Round]
    lives: int = PLAYER_LIVES
    player_x: int = SCREEN_WIDTH // 2
    player_y: int = SCREEN_HEIGHT // 2
    allow_upgrades: bool = False

@dataclass
class Round:
    enemy_colors: list[Color]
    enemy_list: list[DefaultEnemy]
    enemy_hitpoints: int = ENEMY_HITPOINTS
    enemy_exp: int = ENEMY_EXP_YIELD
    enemy_move_delay: int = ENEMY_MOVE_DELAY

def vec_len(vec_x: float, vec_y: float) -> float:
    return ((vec_x ** 2) + (vec_y ** 2)) ** 0.5

def normalize(vec_x: float, vec_y: float, norm: float = 1) -> tuple[float, float]:
    len = vec_len(vec_x, vec_y)
    return (norm * vec_x) / len, (norm * vec_y) / len

def grid_to_coordinate(r: int, c: int) -> tuple[int, int]:
    (x, y), _ = tile_corners(r, c)
    return x + (TILE_SIZE // 2), y + (TILE_SIZE // 2)

def coordinate_to_grid(rows: int, cols: int, x: int, y: int) -> tuple[int, int]:
    for i in range(rows):
        for j in range(cols):
            (x1, y1), (x2, y2) = tile_corners(i, j)
            if (x in range(x1, x2)) and (y in range(y1, y2)):
                return i, j
    return -1, -1

def tile_corners(r: int, c: int) -> tuple[tuple[int, int], tuple[int, int]]:
        x1 = BORDER_WIDTH + (c * TILE_SIZE)
        y1 = BORDER_WIDTH + (r * TILE_SIZE)
        x2 = x1 + TILE_SIZE
        y2 = y1 + TILE_SIZE
        return (x1, y1), (x2, y2)
