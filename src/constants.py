"""
Mago Defence - Constants and Configuration
Organized and well-documented constants for the game.
"""
import os
import sys

def resolve_path(relative_path):
    """Universal path resolver for web and desktop platforms."""
    if sys.platform == 'emscripten':
        return relative_path.replace("\\", "/")
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path).replace("\\", "/")


# =============================================================================
# SCREEN CONFIGURATION
# =============================================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


# =============================================================================
# GAME STATES
# =============================================================================
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSE = 2
STATE_GAMEOVER = 3
STATE_TRANSITION = 4
STATE_UPGRADE_SELECT = 5
STATE_CHARACTER_SELECT = 6
STATE_SHOP = 7
STATE_BOSS_REWARD = 8
STATE_DEBUG_MENU = 9
STATE_VICTORY = 10


# =============================================================================
# DIFFICULTY MODES
# =============================================================================
MODE_NORMAL = 0
MODE_HARD = 1


# =============================================================================
# COLORS (ARGB format where applicable)
# =============================================================================
# Basic colors
BLACK = (10, 10, 20)
WHITE = (255, 255, 255)

# Character colors
MAGE_BLUE = (100, 100, 255)
CYAN_MAGIC = (0, 255, 255)
ORANGE_FIRE = (255, 100, 0)
RED_LIFE = (255, 50, 50)
GREEN_BARRIER = (50, 255, 50)
PURPLE_DARK = (138, 43, 226)
PURPLE_CHARGED = (75, 0, 130)
GOLD_POWER = (255, 215, 0)
HEART_COLOR = (255, 0, 127)

# UI colors
CARD_GRAY = (50, 50, 60)
BORDER_GRAY = (100, 100, 120)
BLUE_RAY = (200, 230, 255)
GOLD_PROJECTILE = (255, 255, 100)
GREEN_VENOM = (100, 255, 100)
RED_BLOOD = (200, 0, 0)
WHITE_ICE = (200, 255, 255)
MAGENTA_ARC = (255, 100, 255)
GREEN_HUNTER = (50, 180, 50)
ELITE_GRAY = (180, 180, 190)
ORBITAL_RED = (255, 80, 80)
HOMING_BLUE = (80, 150, 255)
FROZEN_BLUE = (100, 255, 255)
BARRIER_FULL = (50, 255, 50)
BARRIER_MEDIUM = (200, 200, 50)
BARRIER_LOW = (255, 50, 50)
HUD_BG = (10, 10, 30, 200)

# UI buttons
RED_DELETE = (200, 40, 40)
RED_DELETE_HOVER = (255, 0, 0)
GREEN_PLAY = (40, 180, 40)
DISABLED_GRAY = (80, 80, 80)
BUTTON_GRAY = (60, 60, 70)
SELECTION_YELLOW = (255, 215, 0)
XP_GREEN = (150, 255, 100)
GOLD_BRIGHT = (255, 215, 0)
FLUOR_GREEN = (150, 255, 50)

# Environmental colors
FIREFLY_COLOR = (200, 255, 150)
MAGIC_MOTA = (100, 200, 255)
FOG_COLOR = (200, 220, 230)


# =============================================================================
# BIOMES COLOR PALETTES
# =============================================================================
BIOMES = {
    0: {"grass": (20, 35, 20), "var1": (25, 45, 25), "var2": (15, 30, 15),
        "tree_bg": (5, 20, 5), "tree_fg": (10, 40, 10)},
    1: {"grass": (194, 178, 128), "var1": (210, 180, 140), "var2": (180, 160, 110),
        "tree_bg": (139, 69, 19), "tree_fg": (160, 82, 45)},
    2: {"grass": (200, 200, 220), "var1": (220, 220, 240), "var2": (180, 180, 200),
        "tree_bg": (50, 50, 80), "tree_fg": (70, 70, 100)}
}


# =============================================================================
# ROGUELIKE BALANCING
# =============================================================================
XP_PER_ENEMY = 1
XP_BASE_REQUIRED = 20
XP_SCALING_FACTOR = 1.50
ATTACK_SPEED_SCALING = 0.98
DASH_SPEED = 18
DASH_DURATION = 150


# =============================================================================
# BASE ATTACK SETTINGS
# =============================================================================
BASE_ATTACK_COOLDOWN = 500  # milliseconds


# =============================================================================
# CHARACTER CONFIGURATION
# =============================================================================
CHARACTER_CONFIGS = {
    "MAGO": {
        "name": "MAGO",
        "description": "Equilibrado.",
        "detail": "Ideal para empezar.",
        "color": MAGE_BLUE,
        "sprite": "assets/mago.png",
        "sprite_shoot": "assets/mago_disparo.png",
        "sprite_front": "assets/mago_frente.png",
        "base_lives": 3,
        "max_lives": 3,
        "base_damage": 10,
        "damage_multiplier": 1.0,
        "damage_scaling": 0.5,
        "cooldown_ms": 400,
        "cooldown_scaling": 0.96,
        "projectile_speed": 9.0,
        "extra_projectiles": 0,
        "spread_angle": 10,
        "move_speed": 6.0,
        "dash_speed": 18,
        "dash_duration_ms": 150,
        "dash_cooldown_ms": 1200,
        "crit_chance": 0.05,
        "crit_damage": 1.5,
        "special_ability": None,
        "initial_modifiers": [],
        # Snake-specific
        "charge_time_ms": 1000,
        "max_charge_damage": 0.15,
        "min_charge_damage": 0.02,
        "charge_speed_multi": 1.0,
        "charge_velocity": 2.8,
    },
    "piromante": {
        "name": "PIROMANTE",
        "description": "Daño explosivo.",
        "detail": "Lento pero letal.",
        "color": ORANGE_FIRE,
        "sprite": "assets/mago_piromante.png",
        "sprite_shoot": "assets/mago_piromante_disparo.png",
        "sprite_front": "assets/piromante_frente.png",
        "base_lives": 4,
        "max_lives": 4,
        "base_damage": 20,
        "damage_multiplier": 1.5,
        "damage_scaling": 0.3,
        "cooldown_ms": 50,
        "cooldown_scaling": 0.90,
        "projectile_speed": 8.0,
        "extra_projectiles": 0,
        "spread_angle": 15,
        "move_speed": 4.5,
        "dash_speed": 15,
        "dash_duration_ms": 150,
        "dash_cooldown_ms": 1500,
        "crit_chance": 0.05,
        "crit_damage": 2.0,
        "special_ability": "explosion_burn",
        "explosion_damage": 0.7,
        "explosion_radius": 70,
        "initial_modifiers": ["explosivo"],
    },
    "cazador": {
        "name": "CAZADOR",
        "description": "Doble disparo.",
        "detail": "Rápido y preciso.",
        "color": GREEN_HUNTER,
        "sprite": "assets/mago_cazador.png",
        "sprite_shoot": "assets/mago_cazador_disparo.png",
        "sprite_front": "assets/cazador_frente.png",
        "base_lives": 3,
        "max_lives": 3,
        "base_damage": 5,
        "damage_multiplier": 0.5,
        "damage_scaling": 0.4,
        "cooldown_ms": 250,
        "cooldown_scaling": 0.94,
        "projectile_speed": 10.0,
        "extra_projectiles": 1,
        "spread_angle": 8,
        "move_speed": 7.5,
        "dash_speed": 20,
        "dash_duration_ms": 150,
        "dash_cooldown_ms": 1000,
        "crit_chance": 0.10,
        "crit_damage": 2.0,
        "special_ability": None,
        "initial_modifiers": [],
    },
    "el_loco": {
        "name": "EL LOCO",
        "description": "Cadencia extrema.",
        "detail": "Muchos disparos débiles.",
        "color": (200, 255, 0),
        "sprite": "assets/mago_loco.png",
        "sprite_shoot": "assets/mago_loco_disparo.png",
        "sprite_front": "assets/mago_loco_frente.png",
        "base_lives": 2,
        "max_lives": 2,
        "base_damage": 1,
        "damage_multiplier": 0.1,
        "damage_scaling": 0.1,
        "cooldown_ms": 2600,
        "cooldown_scaling": 0.99,
        "projectile_speed": 5.0,
        "extra_projectiles": 0,
        "spread_angle": 20,
        "move_speed": 7.5,
        "dash_speed": 22,
        "dash_duration_ms": 150,
        "dash_cooldown_ms": 800,
        "crit_chance": 0.03,
        "crit_damage": 1.25,
        "special_ability": None,
        "initial_modifiers": [],
    },
    "snake": {
        "name": "SNAKE",
        "description": "Rayo cargado.",
        "detail": "Disparo lento que atraviesa todo.",
        "color": (255, 0, 150),
        "sprite": "assets/mago_snake.png",
        "sprite_shoot": "assets/mago_snake_disparo.png",
        "sprite_front": "assets/mago_snake_frente.png",
        "base_lives": 2,
        "max_lives": 2,
        "base_damage": 0.05,
        "damage_multiplier": 1.0,
        "damage_scaling": 0.05,
        "cooldown_ms": 800,
        "cooldown_scaling": 0.98,
        "projectile_speed": 2.0,
        "extra_projectiles": 0,
        "spread_angle": 0,
        "move_speed": 4.0,
        "dash_speed": 18,
        "dash_duration_ms": 150,
        "dash_cooldown_ms": 1200,
        "crit_chance": 0.05,
        "crit_damage": 1.5,
        "special_ability": None,
        "initial_modifiers": [],
        "charge_time_ms": 1000,
        "max_charge_damage": 0.15,
        "min_charge_damage": 0.02,
        "charge_speed_multi": 1.0,
        "charge_velocity": 2.8,
    }
}


# =============================================================================
# ENEMY TYPES
# =============================================================================
ENEMY_NORMAL = 0
ENEMY_FAST = 1
ENEMY_TANK = 2
ENEMY_TREASURE = 3
ENEMY_ELITE = 4

ENEMY_COLORS = {
    0: (50, 200, 50),
    1: (200, 200, 50),
    2: (200, 100, 50),
    3: (200, 50, 50)
}

POINTS_PER_ROW = {0: 10, 1: 30, 2: 60, 3: 150}
HP_PER_ROW = {0: 15, 1: 30, 2: 45, 3: 55}
LIFE_MULTIPLIER = 0.15

ENEMY_BORDER_COLORS = {
    "tank": (100, 100, 100),
    "elite": (255, 215, 0),
    "treasure": (255, 255, 0)
}
ENEMY_GLOW = (200, 0, 255)
ENEMY_PROJECTILE_COLOR = (150, 0, 255)


# =============================================================================
# BOSS SETTINGS
# =============================================================================
BOSS_FREQUENCY = 5
BASE_BOSS_HP = 750
BOSS_MAX_SPEED_X = 4.0
BOSS_MAX_SPEED_Y = 2.0
BOSS_LOWER_LIMIT = 300
BOSS_SPEED_MULT_HARD = 1.9

BOSS_ARCO_CD = 2000
BOSS_RAFAGA_CD = 5500
BOSS_CHARGED_CD = 8000
BOSS_TELEGRAPH_TIME = 1500

BOSS_TYPE_NORMAL = 0
BOSS_TYPE_ICE = 1
BOSS_TYPE_TOXIC = 2
BOSS_TYPE_FIRE = 3
BOSS_TYPE_SNAKE = 4

BOSS_SNAKE_HP = 4500
BOSS_FIRE_COLOR = (255, 69, 0)


# =============================================================================
# SHOOTING PROBABILITIES
# =============================================================================
BASE_SHOT_CHANCE = 0.0004
SHOT_CHANCE_INCREMENT = 0.00002
SHOT_CHANCE_MULTIPLIERS = {
    ENEMY_NORMAL: 1.0,
    ENEMY_FAST: 1.5,
    ENEMY_TANK: 0.5,
    ENEMY_ELITE: 2.9,
    ENEMY_TREASURE: 6.0
}


# =============================================================================
# ENEMY MOVEMENT
# =============================================================================
BASE_ENEMY_SPEED_X = 0.2
BASE_DESCENT_DISTANCE = 4
ENEMY_ROWS = 4
ENEMY_COLUMNS = 10
SPEED_INCREMENT_PER_LEVEL = 0.2
DESCENT_INCREMENT_EVERY_5 = 2
SPEED_MULT_HARD = 1.9
SHOT_MULT_HARD = 2.9


# =============================================================================
# POWER-UPS
# =============================================================================
HEART_PROBABILITY = 0.0008
POWERUP_SKY_PROBABILITY = 0.0002
POWERUP_BASE_PROBABILITY = 0.12
POWERUP_ENDGAME_PROBABILITY = 0.30
POWERUP_RAY_PROBABILITY = 0.03

POWERUP_COLORS = {
    "cadencia": CYAN_MAGIC,
    "arco": MAGENTA_ARC,
    "disparo_doble": GREEN_BARRIER,
    "disparo_triple": (255, 200, 0),
    "explosivo": (255, 165, 0),
    "escudo": RED_LIFE,
    "doble_danio": GOLD_POWER,
    "rayo": BLUE_RAY,
    "orbital": ORBITAL_RED,
    "homing": HOMING_BLUE
}

POWERUP_STATS = {
    "cadencia": {"duration": 8000},
    "arco": {"charges": 6},
    "disparo_doble": {"charges": 8},
    "disparo_triple": {"charges": 5},
    "explosivo": {"charges": 3},
    "escudo": {"duration": 9000},
    "doble_danio": {"duration": 9000},
    "rayo": {"charges": 3},
    "orbital": {"duration": 15000},
    "homing": {"charges": 12}
}

UNLOCK_ORBITAL_LEVEL = 1
UNLOCK_HOMING_LEVEL = 3

# Power-up bonus system
POWERUP_BONUS_THRESHOLD_MS = 10000
POWERUP_BONUS_PER_SECOND = 0.005
MAX_POWERUP_BONUS = 0.25
BOSS_POWERUP_BONUS_MULTIPLIER = 2.0
MIN_POWERUP_INTERVAL = 500


# =============================================================================
# BARRIERS
# =============================================================================
BARRIER_GROUPS = 3
BARRIER_MAX_HP = 10
BARRIER_WIDTH = 40
BARRIER_HEIGHT = 9


# =============================================================================
# STATUS EFFECTS
# =============================================================================
FROZEN_DURATION_NORMAL = 2000
FROZEN_DURATION_BOSS = 600
SLOW_FACTOR = 0.5
SLOW_DURATION = 3000
Puddle_DURATION = 5000
POISON_TICK = 1000


# =============================================================================
# SHIELD SETTINGS
# =============================================================================
SHIELD_PENDING_COLOR = (0, 200, 255)
SHIELD_ACTIVE_COLOR = (255, 120, 0, 95)
SHIELD_REGEN_COOLDOWN = 45000  # 45 seconds


# =============================================================================
# META-PROGRESSION
# =============================================================================
SHOP_COST_FACTOR = 1.6
SHOP_ITEMS = {
    "base_lives": {"base": 150, "max": 10, "name": "VIDA INICIAL"},
    "base_damage": {"base": 200, "max": 20, "name": "PODER ARCANO"},
    "crit_chance": {"base": 300, "max": 10, "name": "SUERTE CRÍTICA"},
}


# =============================================================================
# IN-GAME PROGRESSION
# =============================================================================
ATTACK_SPEED_IMPROVEMENT = 0.99
DAMAGE_IMPROVEMENT = 0.5
LIVES_IMPROVEMENT = 1


# =============================================================================
# PLAYER SIZE
# =============================================================================
PLAYER_WIDTH = 24
PLAYER_HEIGHT = 24


# =============================================================================
# BASE PLAYER STATS
# =============================================================================
BASE_PLAYER_SPEED = 6
BASE_PLAYER_DAMAGE = 10
INITIAL_LIVES = 3
MAX_LIVES_BASE = 3


# =============================================================================
# BUTTON VISUALS
# =============================================================================
BUTTON_ALPHA = 110


# =============================================================================
# DEBUG SETTINGS (disabled by default)
# =============================================================================
DEBUG_MODE = False
DEBUG_START_LEVEL = 1
DEBUG_GOD_MODE = False
DEBUG_MAX_STATS = False
DEBUG_ALL_UNLOCKED = False
DEBUG_ALL_POWERUPS = False
DEBUG_INFINITE_CHARGES = False


# =============================================================================
# FILE PATHS
# =============================================================================
PATH_MUSIC = "assets/musica_fondo.wav"
PATH_SND_SHOOT = "assets/disparo.wav"
PATH_SND_DEATH = "assets/muerte.wav"
PATH_SND_POWERUP = "assets/powerup.wav"
PATH_SND_LEVEL = "assets/nivel_up.wav"
PATH_BOSS_SPRITE = "assets/boss.png"
