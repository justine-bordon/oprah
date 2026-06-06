from __future__ import annotations

from random import Random

from defaults import *
from classes import *
import json
import os

class GameModel:
    def __init__(self, rows: int, cols: int, rng: Random, player: Shooter, tower: Shooter, stage: Stage) -> None:
        self._rows = rows
        self._cols = cols
        self._rng = rng
        self._player = player
        self._tower = tower

        self._allow_upgrades = stage.allow_upgrades

        self._lives = stage.lives
        self._current_round = 0
        self._total_rounds = len(stage.rounds)
        self._exp = 0

        self._grid: list[list[Tile]] = [[GridTile() for _ in range(self.cols)] for _ in range(self.rows)]
        self._paths = stage.paths

        self._towers: dict[tuple[int, int], Shooter] = {}

        self._rounds = stage.rounds
        self._game_state = GameState.MAIN_MENU
        self._create_round()
        
        self._game_mode = None
        self._player_name = ""
        self._leaderboard = []

    @property
    def leaderboard(self) -> list:
        return self._leaderboard
    @property
    def game_mode(self) -> GameMode | None: 
        return self._game_mode
    @game_mode.setter
    def game_mode(self, mode: GameMode) -> None:
        self._game_mode = mode
    @property
    def game_state(self) -> GameState: 
        return self._game_state
    @game_state.setter
    def game_state(self, state: GameState) -> None:
        self._game_state = state
    @property
    def player_name(self) -> str:
        return self._player_name   
    @player_name.setter
    def player_name(self, name: str) -> None:
        self._player_name = name
    @property
    def rows(self) -> int: return self._rows
    @property
    def cols(self) -> int: return self._cols
    @property
    def player(self) -> Shooter: return self._player
    @property
    def towers(self) -> dict[tuple[int, int], Shooter]: return self._towers
    @property
    def game_state(self) -> GameState: return self._game_state
    @property
    def tick(self) -> int: return self._tick
    @property
    def grid(self) -> list[list[Tile]]: return self._grid
    @property
    def paths(self) -> list[Path]: return self._paths
    @property
    def projectile_list(self) -> list[Projectile]: return self._projectile_list
    @property
    def lives(self) -> int: return self._lives
    @property
    def exp(self) -> int: return self._exp
    @property
    def current_round(self) -> int: return self._current_round
    @property
    def total_rounds(self) -> int: return self._total_rounds
    @property
    def allow_upgrades(self) -> bool: return self._allow_upgrades


    def _create_round(self):
        round = self._rounds.pop(0)

        self._round = round
        self._enemy_to_spawn = round.enemy_list
        self._enemy_in_grid = 0
        self._enemy_colors = round.enemy_colors

        self._projectile_list: list[Projectile] = []
        self._player.randomize_color(self._enemy_colors)
        self._player.start_cooldown()

        for i, tower in self.towers.items():
            tower.randomize_color(self._enemy_colors)
            tower.start_cooldown()
            self._towers[i] = tower

        self._tick = 0

        self._create_paths(self._paths)

    def _create_paths(self, paths: list[Path]) -> None:
        self._paths: list[Path] = []
        for path in paths:
            path.contents = [PathTile() for _ in range(len(path.flow) + 1)]
            self._paths.append(path)
        self._update_grid()

    def round_start(self) -> None:
        self._game_state = GameState.ONGOING

    def update(self) -> None:
        if self.game_state == GameState.ONGOING:

            if (self._tick % self._round.enemy_move_delay) == 0:
                self._move_paths()
            self._update_grid()

            if not self._player.ready:
                self._player.cooldown_tick()

            for (r, c), tower in self._towers.items():
                if not tower.ready:
                    tower.cooldown_tick()
                self._towers[(r, c)] = tower

            if self._lives <= 0:
                self._game_state = GameState.LOSER
                return

            if (len(self._enemy_to_spawn) + self._enemy_in_grid) == 0:
                self._current_round += 1
                if self._current_round < self._total_rounds:
                    self._game_state = GameState.BETWEEN_ROUNDS
                    self._create_round()
                    return
                else:
                    if self._game_mode == GameMode.ENDLESS:
                        # for Endless Mode
                        self._total_rounds += 1
                        new_enemies = [self._rng.choice([DefaultEnemy, RegeneratorEnemy, ChameleonEnemy])() for _ in range(ENEMY_COUNT + self._current_round)] 
                        self._rounds.append(Round(self._enemy_colors, new_enemies))
                        self._game_state = GameState.BETWEEN_ROUNDS
                        self._create_round()
                        return
                    else:
                        # for Campaign Mode
                        self._current_round -= 1
                        self._game_state = GameState.WINNER
                        return

            self._tick += 1

    def _move_paths(self) -> None:
        self._rng.shuffle(self._paths)
        for i, path in enumerate(self._paths):
            if path.contents.pop().color is not None:
                self._lives = max(0, self._lives - 1)

            for j, tile in enumerate(path.contents):
                if isinstance(tile, DefaultEnemy):
                    tile.travel()
                    path.contents[j] = tile

            if self._enemy_to_spawn:
                round = self._round
                self._rng.shuffle(self._enemy_to_spawn)
                enemy = self._enemy_to_spawn.pop()
                enemy.initialize(round.enemy_colors, round.enemy_hitpoints, round.enemy_exp, self._rng)
                path.contents.insert(0, enemy)
            else:
                path.contents.insert(0, PathTile())

            self._paths[i] = path

    def _update_grid(self) -> None:
        colors: set[Color] = set()
        self._enemy_in_grid = 0
        for k, path in enumerate(self._paths):
            r = path.start_r
            c = path.start_c
            flow = path.flow
            for i in range(len(flow) + 1):
                if i > 0:
                    dir = flow[i-1].value
                    r += dir[0]
                    c += dir[1]
                tile = path.contents[i]
                if isinstance(tile, DefaultEnemy) and (tile.color is not None):
                    self._enemy_in_grid += 1
                    colors.add(tile.color)
                    tile.wait()
                    path.contents[i] = tile
                self._grid[r][c] = tile
            self._paths[k] = path
        if len(self._enemy_to_spawn) == 0:
            self._enemy_colors = list(colors)

    def aim(self, cursor_pos: tuple[float, float], wasd: Direction | None) -> None:
        self._player = self._aim(self._player, cursor_pos, wasd)
        for i, tower in self._towers.items():
            self._towers[i] = self._aim(tower, cursor_pos, wasd)

    def _aim(self, shooter: Shooter, cursor_pos: tuple[float, float], wasd: Direction | None) -> Shooter:
        x = cursor_pos[0]
        y = cursor_pos[1]
        match shooter.direction:
            case ShooterDirection.UPWARD:
                y, x = Direction.UP.value
                shooter.aim(x, y)
            case ShooterDirection.WASD:
                if wasd is not None:
                    y, x = wasd.value
                    shooter.aim(x, y)
            case ShooterDirection.CURSOR:
                vec_x = x - shooter.pos_x
                vec_y = y - shooter.pos_y
                shooter.aim(vec_x, vec_y)
        return shooter

    def shoot(self) -> bool:
        self._player, success = self._shoot(self._player)
        success = success or self.tower_shoot()
        return success

    def _shoot(self, shooter: Shooter) -> tuple[Shooter, bool]:
        if not shooter.ready:
            return shooter, False

        colors = [shooter.color, shooter.color2] if shooter.is_upgraded else [shooter.color]

        for pos, color in zip(shooter.bullet_positions, colors):
            bx, by = pos
            self._projectile_list.append(Projectile(bx, by, shooter.aim_x, shooter.aim_y, shooter.bullet, color))

        shooter.start_cooldown()
        shooter.randomize_color(self._enemy_colors)
        return shooter, True

    def tower_shoot(self) -> bool:
        success = False
        for i, tower in self._towers.items():
            tower, s = self._shoot(tower)
            self._towers[i] = tower
            if s:
                success = True
        return success

    def tower_place(self, r: int, c: int) -> None:
        if not self.tower_placeable(r, c):
            return
        self._exp -= TOWER_COST
        tower = self._tower.copy()
        x, y = grid_to_coordinate(r, c)
        tower.randomize_color(self._enemy_colors)
        tower.place(x, y)
        self._towers[(r, c)] = tower

    def tower_upgrade(self, r: int, c: int) -> None:
        if not self._allow_upgrades:
            return
        if (not self._tile_has_tower(r, c)) or (self.exp < TOWER_UPGRADE_COST):
            return
        tower = self._towers[(r, c)]
        if tower.is_upgraded:
            return
        self._exp -= TOWER_UPGRADE_COST
        tower.upgrade()

    def tower_placeable(self, r: int, c: int) -> bool:
        for path in self._paths:
            if path.rc_to_idx(r, c) in range(len(path.contents)):
                return False
        if (self._tile_has_tower(r, c)) or (self.exp < TOWER_COST):
            return False
        if (r in range(self.rows)) and (c in range(self.cols)):
            return True
        return False

    def _tile_has_tower(self, r: int, c: int) -> bool:
        for i in list(self.towers.keys()):
            if i == (r, c):
                return True
        return False

    def move_projectiles(self) -> bool:
        alive_projectiles: list[Projectile] = []
        kill = False

        for projectile in self._projectile_list:
            vec_x, vec_y = projectile.vec_x, projectile.vec_y
            projectile.pos_x += vec_x
            projectile.pos_y += vec_y
            projectile.bullet.range -= vec_len(vec_x, vec_y)
            projectile, k = self._check_for_collision(projectile)
            if k:
                kill = True
            if (projectile.bullet.range <= 0) or (projectile.bullet.hits <= 0):
                continue
            alive_projectiles.append(projectile)

        self._projectile_list = alive_projectiles
        return kill

    def _check_for_collision(self, projectile: Projectile) -> tuple[Projectile, bool]:
        x = projectile.pos_x
        y = projectile.pos_y
        for i, path in enumerate(self._paths):
            r = path.start_r
            c = path.start_c
            flow = path.flow
            for j in range(len(flow) + 1):
                if j > 0:
                    dir = flow[j-1].value
                    r += dir[0]
                    c += dir[1]
                size = projectile.bullet.size // 2
                tile = self.grid[r][c]
                (x1, y1), (x2, y2) = tile_corners(r, c)
                if (int(x) in range(x1 - size, x2 + size + 1)) and (int(y) in range(y1 - size, y2 + size + 1)):
                    if path.in_tunnel(j):
                        projectile.bullet.hits = 0
                        return projectile, False
                    if isinstance(tile, DefaultEnemy):
                        if tile.color != projectile.color:
                            continue
                        tile, kill = self._damage_enemy(tile, projectile.bullet.damage)
                        path.contents[j] = tile
                        self._paths[i] = path
                        projectile.bullet.hits -= 1
                        return projectile, kill
        return projectile, False

    def _damage_enemy(self, enemy: DefaultEnemy, amt: int) -> tuple[PathTile | DefaultEnemy, bool]:
        enemy.modify_hp(-amt)
        if enemy.current_hp <= 0:
            self._exp += enemy.exp_yield
            return PathTile(), True
        return enemy, False
        
    def load_leaderboard(self) -> None:
        if os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "r") as file:
                self._leaderboard = json.load(file)
        else:
            self._leaderboard = []

    def save_score(self) -> None:
        self.load_leaderboard()
        new_entry = {"name": self._player_name, "score": self.exp, "round": self.current_round + 1}
        self._leaderboard.append(new_entry)
        
        self._leaderboard = sorted(self._leaderboard, key=lambda x: x["score"], reverse=True)[:5]
        
        with open("leaderboard.json", "w") as file:
            json.dump(self._leaderboard, file)


    @classmethod
    def phase1(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.UPWARD, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.UPWARD, rng)

        flow = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT]
        path = Path(0, 0, flow, [], [])

        enemy_colors = [rng.choice([Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE])]
        rounds = [
            Round(enemy_colors, [DefaultEnemy() for _ in range(5)])
        ]

        stage = Stage([path], rounds, lives=2)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)

    @classmethod
    def phase2(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.WASD, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.UPWARD, rng)

        flow = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT]
        path = Path(0, 0, flow, [], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:2]
        rounds = [
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
        ]

        stage = Stage([path], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)
    
    @classmethod
    def phase3(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.UPWARD, rng)

        flow1 = [
            Direction.UP,
            Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, 
            Direction.RIGHT, Direction.RIGHT, Direction.RIGHT,
            Direction.DOWN
        ]
        path1 = Path(1, 0, flow1, [], [])

        flow2 = [
            Direction.DOWN,
            Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT,
            Direction.LEFT, Direction.LEFT, Direction.LEFT,
            Direction.UP
        ]
        path2 = Path(4, 7, flow2, [], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:3]
        rounds = [
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
        ]

        stage = Stage([path1, path2], rounds, allow_upgrades = True)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)

    @classmethod
    def phase4(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.WASD, rng)

        flow = [Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.UP, Direction.UP]
        path = Path(5, 0, flow, [Tunnel(10, 5), Tunnel(20, 5)], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:4]
        rounds = [
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
            Round(enemy_colors, [DefaultEnemy() for _ in range(ENEMY_COUNT)]),
        ]

        stage = Stage([path], rounds, allow_upgrades = True)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)
        
    @classmethod
    def phase5(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.WASD, rng)

        flow = [Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.UP, Direction.UP]
        path = Path(5, 0, flow, [Tunnel(10, 5), Tunnel(20, 5)], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:5]
        rounds = []
        
        for _ in range(5):
            enemy_list = []
            for _ in range(ENEMY_COUNT):
                enemy_type = rng.choice([
                    DefaultEnemy, 
                    DefaultEnemy,
                    RegeneratorEnemy, 
                    ChameleonEnemy
                ])
                enemy_list.append(enemy_type())
            
            rounds.append(Round(enemy_colors, enemy_list))

        stage = Stage([path], rounds, allow_upgrades = True)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)
        
    @classmethod
    def phase5(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR, rng)
        player.place(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        tower = Shooter.base_tower(ShooterDirection.WASD, rng)

        flow = [Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.UP, Direction.UP]
        path = Path(5, 0, flow, [Tunnel(10, 5), Tunnel(20, 5)], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:6]
        rounds = []
        
        for _ in range(12):
            enemy_list = []
            for _ in range(ENEMY_COUNT):
                enemy_type = rng.choice([
                    DefaultEnemy, 
                    DefaultEnemy,
                    RegeneratorEnemy, 
                    ChameleonEnemy
                ])
                enemy_list.append(enemy_type())
            
            rounds.append(Round(enemy_colors, enemy_list))

        stage = Stage([path], rounds, allow_upgrades = True)

        return cls(GRID_ROWS, GRID_COLS, rng, player, tower, stage)
        

