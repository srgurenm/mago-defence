"""
Mago Defence - Main Game Module
Refactored game loop and logic.
"""
import asyncio
import pygame
import sys
import random
import math
import os
import json

from src.constants import *
from src.player import Mage
from src.sprites import (
    Particle, XPOrb, AmbientParticle, Orbital, Projectile,
    Enemy, Barrier, PowerUp, Heart, Ray, RayoPlayer,
    LaserSNAKE, SpecialShield, CriticalHit, RayImpact,
    Puddle, Boss, BossSNAKE
)


class DataManager:
    """Manages save data and persistence."""
    def __init__(self):
        self.file_path = resolve_path("save_data_rogue.json")
        self.is_web = sys.platform == 'emscripten'
        self.data = {
            "crystals": 0,
            "high_score": 0,
            "boss_kills": 0,
            "upgrades": {
                "base_lives": 0,
                "base_damage": 0,
                "crit_chance": 0,
            },
            "special_abilities": {
                "MAGO": False, "piromante": False, "cazador": False,
                "el_loco": False, "snake": False
            }
        }
        self.load()

    def load(self):
        if self.is_web:
            try:
                import js
                data_str = js.localStorage.getItem("mago_defence_save")
                if data_str:
                    self._merge_data(json.loads(data_str))
            except:
                pass
        else:
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, 'r') as f:
                        self._merge_data(json.load(f))
                except:
                    pass

    def _merge_data(self, data):
        for k, v in data.items():
            if k == "upgrades":
                for uk, uv in v.items():
                    if uk in self.data["upgrades"]:
                        self.data["upgrades"][uk] = uv
                    else:
                        self.data["upgrades"][uk] = uv
                for def_k, def_v in self.data["upgrades"].items():
                    if def_k not in v:
                        v[def_k] = def_v
            elif k == "special_abilities":
                for hk, hv in v.items():
                    if hk in self.data["special_abilities"]:
                        self.data["special_abilities"][hk] = hv
            else:
                self.data[k] = v
        if "unlocked_snake" not in self.data:
            self.data["unlocked_snake"] = False

    def save(self):
        if self.is_web:
            try:
                import js
                js.localStorage.setItem("mago_defence_save", json.dumps(self.data))
            except:
                pass
        else:
            try:
                with open(self.file_path, 'w') as f:
                    json.dump(self.data, f)
            except:
                pass

    def reset(self):
        self.data = {
            "crystals": 0, "high_score": 0, "boss_kills": 0,
            "upgrades": {"base_lives": 0, "base_damage": 0, "crit_chance": 0},
            "special_abilities": {
                "MAGO": False, "piromante": False, "cazador": False,
                "el_loco": False, "snake": False
            }
        }
        self.save()

    def add_crystals(self, amount):
        self.data["crystals"] += amount
        self.save()

    def register_boss_kill(self):
        self.data["boss_kills"] += 1
        self.save()

    def buy_upgrade(self, key):
        if key not in self.data["upgrades"]:
            return False
        current_level = self.data["upgrades"][key]
        info = SHOP_ITEMS.get(key, {"base": 100, "max": 10})
        if current_level >= info["max"]:
            return False
        if "custom_prices" in info:
            cost = info["custom_prices"][current_level]
        else:
            cost = int(info["base"] * (SHOP_COST_FACTOR ** current_level))
        if self.data["crystals"] >= cost:
            self.data["crystals"] -= cost
            self.data["upgrades"][key] += 1
            self.save()
            return True
        return False

    def update_highscore(self, score):
        if score > self.data["high_score"]:
            self.data["high_score"] = score
            self.save()


class Game:
    """Main game class."""
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except:
            pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mago Defence Roguelite")
        self.clock = pygame.time.Clock()

        self.font_lg = pygame.font.SysFont("Arial", 48, True)
        self.font_md = pygame.font.SysFont("Arial", 26, True)
        self.font_sm = pygame.font.SysFont("Arial", 18, True)
        self.font_xs = pygame.font.SysFont("Arial", 16, True)

        self.data_manager = DataManager()
        self.state = STATE_MENU
        self.state_start_time = 0
        self.screen_shake = 0
        self.flash_alpha = 0
        self.powerup_notification = None
        self.powerup_notification_time = 0

        self.muted = False
        self.score = 0
        self.level = 1
        self.running = True
        self.difficulty = MODE_NORMAL

        self.selected_character = "MAGO"
        self.active_touches = {}
        self.touch_controls_enabled = self._detect_touch_device()

        self.is_touch_device = self.touch_controls_enabled
        self.treasure_spawned = False
        self.time_without_powerup = 0
        self.last_sky_powerup_spawn = 0

        self.delete_confirmation = False
        self.delete_confirmation_timer = 0

        # Touch zones (invisible large hit areas)
        self.zone_left = pygame.Rect(0, SCREEN_HEIGHT - 150, SCREEN_WIDTH // 3, 150)
        self.zone_right = pygame.Rect(SCREEN_WIDTH // 3 * 2, SCREEN_HEIGHT - 150, SCREEN_WIDTH // 3, 150)
        self.zone_shoot = pygame.Rect(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 150, 180, 150)

        # Visual indicators
        self.left_zone_active = False
        self.right_zone_active = False
        self.shoot_zone_active = False

        # UI Buttons
        mute_size = 50
        self.btn_mute = pygame.Rect(10, SCREEN_HEIGHT - mute_size - 10, mute_size, mute_size)

        btn_toggle_size = 45
        self.btn_toggle_touch = pygame.Rect(SCREEN_WIDTH - 230, 20, 210, btn_toggle_size)

        btn_play_w, btn_play_h = 240, 60
        self.btn_play = pygame.Rect(SCREEN_WIDTH // 2 - btn_play_w // 2, 340, btn_play_w, btn_play_h)

        btn_diff_w, btn_diff_h = 115, 40
        self.btn_diff_normal = pygame.Rect(SCREEN_WIDTH // 2 - 120, 410, btn_diff_w, btn_diff_h)
        self.btn_diff_hard = pygame.Rect(SCREEN_WIDTH // 2 + 5, 410, btn_diff_w, btn_diff_h)

        btn_shop_w, btn_shop_h = 160, 40
        self.btn_shop = pygame.Rect(SCREEN_WIDTH // 2 - btn_shop_w // 2, 460, btn_shop_w, btn_shop_h)

        self.btn_delete = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 40, 130, 30)

        # Character selection
        char_w, char_h = 170, 240
        char_start = SCREEN_WIDTH // 2 - 370
        self.char_rects = [
            pygame.Rect(char_start + i * 180, SCREEN_HEIGHT // 2 - 50, char_w, char_h)
            for i in range(5)
        ]

        # Debug buttons
        self._init_debug_buttons()

        # Sound effects
        self.snd_shoot = self.snd_death = self.snd_powerup = self.snd_level = None
        self._load_resources()
        self.background_image = None
        self._load_background()
        self.boss_instance = None
        self._init_sprite_groups()

        # Environmental effects
        self.fog_layers = []
        for _ in range(3):
            self.fog_layers.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(50, SCREEN_HEIGHT - 100),
                'speed': random.uniform(0.1, 0.4),
                'width': random.randint(300, 600)
            })
        self.ambient_particles = pygame.sprite.Group()
        self.current_upgrade_options = []

    def _init_debug_buttons(self):
        btn_w, btn_h = 250, 40
        start_y = 150
        gap = 50
        self.btn_debug_toggle = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y, btn_w, btn_h)
        self.btn_debug_god = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + gap, btn_w, btn_h)
        self.btn_debug_stats = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + gap * 2, btn_w, btn_h)
        self.btn_debug_unlock = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + gap * 3, btn_w, btn_h)
        self.btn_debug_powerups = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + gap * 4, btn_w, btn_h)
        self.btn_debug_charges = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + gap * 5, btn_w, btn_h)
        self.btn_debug_prev = pygame.Rect(SCREEN_WIDTH // 2 - 160, start_y + gap * 6, 60, btn_h)
        self.btn_debug_next = pygame.Rect(SCREEN_WIDTH // 2 + 100, start_y + gap * 6, 60, btn_h)
        self.btn_debug_close = pygame.Rect(SCREEN_WIDTH // 2 - 100, start_y + gap * 7.5, 200, btn_h)

    def _detect_touch_device(self):
        if sys.platform == 'emscripten':
            try:
                import js
                max_touch = js.navigator.maxTouchPoints
                has_touch = max_touch > 0
                has_touch_start = 'ontouchstart' in js.window
                user_agent = js.navigator.userAgent.lower()
                is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
                return has_touch or has_touch_start or is_mobile
            except:
                return False
        return False

    def _load_resources(self):
        try:
            paths = {
                'shoot': PATH_SND_SHOOT,
                'death': PATH_SND_DEATH,
                'powerup': PATH_SND_POWERUP,
                'level': PATH_SND_LEVEL
            }
            sounds = {}
            for key, path in paths.items():
                full_path = resolve_path(path)
                if os.path.exists(full_path):
                    sounds[key] = pygame.mixer.Sound(full_path)
                    sounds[key].set_volume(0.25)
            self.snd_shoot = sounds.get('shoot')
            self.snd_death = sounds.get('death')
            self.snd_powerup = sounds.get('powerup')
            self.snd_level = sounds.get('level')

            music_path = resolve_path(PATH_MUSIC)
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.18)
        except:
            pass

    def _load_background(self):
        try:
            path = resolve_path("assets/fondo.png")
            if os.path.exists(path):
                self.background_image = pygame.image.load(path).convert()
                self.background_image = pygame.transform.scale(
                    self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            pass

    def _init_sprite_groups(self):
        self.all_sprites = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.player_projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.hearts = pygame.sprite.Group()
        self.barriers = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.xp_orbs = pygame.sprite.Group()
        self.puddles = pygame.sprite.Group()
        self.mage = Mage(self.all_sprites, self.player_projectiles,
                        self.snd_shoot, "MAGO")
        self.all_sprites.add(self.mage)

    def toggle_mute(self):
        self.muted = not self.muted
        volume = 0 if self.muted else 1
        try:
            pygame.mixer.music.set_volume(0.18 * volume)
        except:
            pass

    def go_to_character_select(self, diff):
        self.difficulty = diff
        self.state = STATE_CHARACTER_SELECT

    def start_game(self, char_type):
        self.selected_character = char_type
        self.score = 0
        self.level = DEBUG_START_LEVEL if DEBUG_MODE else 1
        self.time_without_powerup = 0
        self.last_sky_powerup_spawn = 0
        self._init_sprite_groups()
        self.mage.kill()
        upgrades = self.data_manager.data["upgrades"]
        self.mage = Mage(self.all_sprites, self.player_projectiles,
                        self.snd_shoot, char_type, upgrades)
        self.all_sprites.add(self.mage)

        self._create_barriers()
        self._create_wave()
        self.state = STATE_PLAYING
        self.background_cache = None

        try:
            if not self.muted:
                pygame.mixer.music.play(-1)
        except:
            pass

    def _create_barriers(self):
        for b in self.barriers:
            b.kill()
        interval = SCREEN_WIDTH // (BARRIER_GROUPS + 1)
        for i in range(1, BARRIER_GROUPS + 1):
            cx = i * interval
            b1 = Barrier(cx - 35, SCREEN_HEIGHT - 120)
            b2 = Barrier(cx + 35, SCREEN_HEIGHT - 120)
            self.barriers.add(b1, b2)
            self.all_sprites.add(b1, b2)

    def _create_wave(self):
        self._create_barriers()
        self.treasure_spawned = False
        self.mage.current_wave = self.level

        for s in self.player_projectiles:
            s.kill()
        for s in self.enemy_projectiles:
            s.kill()
        for s in self.xp_orbs:
            s.kill()
        for s in self.powerups:
            s.kill()
        for s in self.hearts:
            s.kill()
        for s in self.puddles:
            s.kill()

        if self.boss_instance:
            self.boss_instance.kill()
            self.boss_instance = None

        if self.level % BOSS_FREQUENCY == 0:
            if self.level == 10:
                for sprite in self.all_sprites:
                    if isinstance(sprite, (Boss, BossSNAKE)):
                        sprite.kill()
                self.boss_instance = BossSNAKE(self.difficulty, self.level)
                self.all_sprites.add(self.boss_instance)
            else:
                variant = BOSS_TYPE_NORMAL if self.difficulty == MODE_NORMAL else random.choice([
                    BOSS_TYPE_ICE, BOSS_TYPE_TOXIC, BOSS_TYPE_FIRE, BOSS_TYPE_NORMAL])
                self.boss_instance = Boss(self.level, self.difficulty, variant)
                self.all_sprites.add(self.boss_instance)
        else:
            self.boss_instance = None
            vx = (BASE_ENEMY_SPEED_X + (self.level * SPEED_INCREMENT_PER_LEVEL)) * (
                SPEED_MULT_HARD if self.difficulty == MODE_HARD else 1)
            descent = BASE_DESCENT_DISTANCE + ((self.level // 5) * DESCENT_INCREMENT_EVERY_5)
            shot_mult = SHOT_MULT_HARD if self.difficulty == MODE_HARD else 1.0

            spacing_x = 52
            spacing_y = 48
            mx = (SCREEN_WIDTH - (ENEMY_COLUMNS * spacing_x)) // 2

            for r in range(ENEMY_ROWS):
                for c in range(ENEMY_COLUMNS):
                    etype = ENEMY_NORMAL
                    roll = random.random()
                    if self.level >= 3 and roll < 0.2:
                        etype = ENEMY_FAST
                    elif self.level >= 5 and roll < 0.05:
                        etype = ENEMY_ELITE
                    elif self.level >= 6 and roll < 0.1:
                        etype = ENEMY_TANK
                    e = Enemy(mx + c * spacing_x, 90 + r * spacing_y,
                             (ENEMY_ROWS - 1 - r), vx, descent, shot_mult,
                             self.level, etype)
                    self.all_sprites.add(e)
                    self.monsters.add(e)

    def change_state(self, new_state):
        self.state = new_state
        self.state_start_time = pygame.time.get_ticks()
        if new_state == STATE_MENU:
            self.flash_alpha = 0
            self.screen_shake = 0
        if hasattr(self, 'mage') and self.mage and self.mage.type == "snake" and self.mage.charging:
            self.mage.release_charge(self.player_projectiles)
        if new_state == STATE_UPGRADE_SELECT:
            self._generate_upgrade_options()
        elif new_state == STATE_BOSS_REWARD:
            self._generate_boss_options()

    def _generate_upgrade_options(self):
        options = [
            {"id": "lives", "title": "MAX LIVES +1", "desc": "Increases max lives and heals.",
             "color": RED_LIFE},
            {"id": "damage", "title": "DAMAGE +20%", "desc": "Increases base damage.",
             "color": ORANGE_FIRE},
            {"id": "attack_speed", "title": "ATK SPEED +15%", "desc": "Faster shooting.",
             "color": CYAN_MAGIC},
            {"id": "multishot", "title": "+1 PROJECTILE", "desc": "Extra permanent bullet.",
             "color": GREEN_BARRIER},
            {"id": "bounce", "title": "BOUNCE +1", "desc": "Projectiles bounce off walls.",
             "color": BLUE_RAY},
            {"id": "pierce", "title": "PIERCE +1", "desc": "Penetrates 1 enemy.",
             "color": PURPLE_DARK},
            {"id": "fragmentation_perma", "title": "FRAGMENTATION", "desc": "Bullets split on impact.",
             "color": ORANGE_FIRE},
            {"id": "arco_perma", "title": "ARC SHOT", "desc": "Side shots (slower, less speed).",
             "color": MAGENTA_ARC},
            {"id": "ice_perma", "title": "FROZEN TOUCH", "desc": "Chance to freeze enemies.",
             "color": FROZEN_BLUE},
            {"id": "big_projectile", "title": "HUGE PROJECTILE", "desc": "Larger, faster bullets (+30%).",
             "color": GOLD_BRIGHT},
            {"id": "homing_perma", "title": "AUTO AIM", "desc": "High auto-target probability.",
             "color": FLUOR_GREEN},
        ]

        if self.mage.modifiers["fragmentacion"]:
            options = [o for o in options if o["id"] != "fragmentation_perma"]
        if self.mage.modifiers["arco"]:
            options = [o for o in options if o["id"] != "arco_perma"]
        if self.mage.modifiers["homing"]:
            options = [o for o in options if o["id"] != "homing_perma"]
        if self.mage.modifiers["big_projectile"]:
            options = [o for o in options if o["id"] != "big_projectile"]

        weighted = []
        for opt in options:
            times = self.mage.upgrade_counter.get(opt["id"], 0)
            if times > 0:
                for _ in range(times + 1):
                    weighted.append(opt.copy())
            else:
                weighted.append(opt)

        self.current_upgrade_options = random.sample(weighted, min(3, len(weighted)))

    def apply_upgrade(self, index):
        if index < 1 or index > len(self.current_upgrade_options):
            return
        upgrade_id = self.current_upgrade_options[index - 1]["id"]
        self.mage.upgrade_counter[upgrade_id] = self.mage.upgrade_counter.get(upgrade_id, 0) + 1

        if upgrade_id == "lives":
            self.mage.max_lives += LIVES_IMPROVEMENT
            self.mage.lives = self.mage.max_lives
        elif upgrade_id == "damage":
            val = 0.1 if self.mage.type == "el_loco" else 0.2
            bonus = self.mage.upgrade_counter["damage"] * 0.05
            self.mage.stats["damage_multiplier"] += val + bonus
        elif upgrade_id == "attack_speed":
            bonus = self.mage.upgrade_counter["attack_speed"] * 0.02
            self.mage.stats["attack_speed_multi"] += 0.15 + bonus
        elif upgrade_id == "multishot":
            self.mage.stats["extra_projectiles"] += 1
            if self.mage.upgrade_counter["multishot"] >= 3:
                self.mage.stats["extra_projectiles"] += 1
                self.mage.upgrade_counter["multishot"] = 0
        elif upgrade_id == "bounce":
            self.mage.stats["bounces"] += 1
        elif upgrade_id == "pierce":
            self.mage.stats["penetration"] += 1
        elif upgrade_id == "fragmentation_perma":
            self.mage.modifiers["fragmentacion"] = True
        elif upgrade_id == "arco_perma":
            self.mage.modifiers["arco"] = True
        elif upgrade_id == "ice_perma":
            self.mage.modifiers["hielo_perma"] = True
            self.mage.ice_level += 2
        elif upgrade_id == "big_projectile":
            self.mage.modifiers["big_projectile"] = True
        elif upgrade_id == "homing_perma":
            self.mage.modifiers["homing"] = True

    def _generate_boss_options(self):
        self.boss_options = []

        if self.level == 5:
            if self.mage.type == "MAGO" and not self.mage.special_shield_unlocked:
                self.boss_options = [{
                    "id": "unlock_special_shield",
                    "title": "ARCANE MIRROR",
                    "desc": "Front shield that bounces enemy projectiles (10s CD).",
                    "color": MAGE_BLUE
                }]
            elif self.mage.type == "piromante":
                self.boss_options = [{
                    "id": "unlock_fury",
                    "title": "IGNEO FURY",
                    "desc": "Enemies explode in chain when killed.",
                    "color": ORANGE_FIRE
                }]
            elif self.mage.type == "cazador":
                self.boss_options = [{
                    "id": "unlock_shadow",
                    "title": "SHADOW SNIPER",
                    "desc": "Critical shots pierce through enemies.",
                    "color": GREEN_BARRIER
                }]
            elif self.mage.type == "el_loco":
                self.boss_options = [{
                    "id": "unlock_chaos",
                    "title": "CHAOS STORM",
                    "desc": "20% chance for bullets to split.",
                    "color": (200, 255, 0)
                }]
            elif self.mage.type == "snake":
                self.boss_options = [{
                    "id": "unlock_serpent",
                    "title": "SNAKE BLOOD",
                    "desc": "+1 Life, Full Heal, +20% Projectile Speed.",
                    "color": (0, 200, 0)
                }]

        if not self.boss_options:
            char_type = self.mage.type
            if char_type == "MAGO":
                if not self.mage.skill_shield:
                    self.boss_options = [{
                        "id": "unlock_shield",
                        "title": "UNLOCK SHIELD",
                        "desc": "Protects from 1 hit (45s CD).",
                        "color": MAGE_BLUE
                    }]
                else:
                    self.boss_options = [
                        {"id": "shield_cd", "title": "FAST CHARGE", "desc": "Shield CD -10s.",
                         "color": CYAN_MAGIC},
                        {"id": "shield_hp", "title": "REINFORCED SHIELD", "desc": "Shield takes +1 hit.",
                         "color": MAGE_BLUE}
                    ]
            elif char_type == "piromante":
                if not self.mage.burn_skill:
                    self.boss_options = [{
                        "id": "unlock_burn",
                        "title": "IGNEO CLEAVAGE",
                        "desc": "Burned enemies explode on death.",
                        "color": ORANGE_FIRE
                    }]
                else:
                    self.boss_options = [
                        {"id": "burn_dmg", "title": "INCINERATION", "desc": "Explosions do +25% damage.",
                         "color": RED_LIFE},
                        {"id": "burn_rad", "title": "HEAT WAVE", "desc": "Explosions reach 30% farther.",
                         "color": ORANGE_FIRE}
                    ]
            elif char_type == "cazador":
                if not self.mage.pierce_skill:
                    self.boss_options = [{
                        "id": "unlock_pierce",
                        "title": "PRECISION SHOT",
                        "desc": "Every 4th shot pierces +3.",
                        "color": GREEN_BARRIER
                    }]
                else:
                    self.boss_options = [
                        {"id": "pierce_freq", "title": "CRITICAL CADENCE", "desc": "Piercing shot more often.",
                         "color": CYAN_MAGIC},
                        {"id": "pierce_count", "title": "MASTER ARROW", "desc": "Pierces +2 extra enemies.",
                         "color": GREEN_BARRIER}
                    ]
            elif char_type == "el_loco":
                if self.mage.cancel_skill_prob <= 0:
                    self.boss_options = [{
                        "id": "unlock_cancel",
                        "title": "MAGIC STOP",
                        "desc": "15% chance to destroy enemy bullets on collision.",
                        "color": (200, 255, 0)
                    }]
                else:
                    self.boss_options = [
                        {"id": "cancel_prob", "title": "CRAZY REFLEXES", "desc": "+10% cancel probability.",
                         "color": CYAN_MAGIC},
                        {"id": "loco_dmg", "title": "BRUTE FORCE", "desc": "Damage +0.1 (0.5x multiplier).",
                         "color": RED_LIFE}
                    ]

    def apply_boss_reward(self, index):
        if index >= len(self.boss_options):
            return
        opt = self.boss_options[index]
        opt_id = opt["id"]

        if opt_id == "unlock_special_shield":
            self.mage.special_shield_unlocked = True
            self.mage.special_shield = SpecialShield(self.mage)
            self.mage.special_shield.activate()
            self.all_sprites.add(self.mage.special_shield)
            self.powerup_notification = "ARCANE MIRROR UNLOCKED!"
            self.powerup_notification_time = pygame.time.get_ticks()
        elif opt_id == "unlock_fury":
            self.mage.fury_ignea = True
            self.mage.burn_skill = True
            self.mage.burn_explosion_damage = 0.80
            self.mage.burn_explosion_radius = 100
            self.powerup_notification = "IGNEO FURY UNLOCKED!"
            self.powerup_notification_time = pygame.time.get_ticks()
        elif opt_id == "unlock_shadow":
            self.mage.shadow_shooter = True
            self.mage.pierce_skill = True
            self.mage.pierce_freq = 3
            self.mage.pierce_count = 5
            self.powerup_notification = "SHADOW SNIPER UNLOCKED!"
            self.powerup_notification_time = pygame.time.get_ticks()
        elif opt_id == "unlock_chaos":
            self.mage.stats["damage_multiplier"] += 1.0
            self.powerup_notification = "CHAOS STORM UNLOCKED!"
            self.powerup_notification_time = pygame.time.get_ticks()
        elif opt_id == "unlock_serpent":
            self.mage.lives = self.mage.max_lives
            self.mage.lives += 1
            self.mage.max_lives += 1
            self.mage.stats["projectile_speed"] *= 1.2
            self.powerup_notification = "SNAKE BLOOD UNLOCKED!"
            self.powerup_notification_time = pygame.time.get_ticks()
        elif opt_id == "unlock_shield":
            self.mage.skill_shield = True
            self.mage.shield_hp = 1
        elif opt_id == "shield_cd":
            self.mage.shield_regen_cooldown = max(5000, self.mage.shield_regen_cooldown - 10000)
        elif opt_id == "shield_hp":
            self.mage.shield_max_hp += 1
            self.mage.shield_hp = self.mage.shield_max_hp
        elif opt_id == "unlock_burn":
            self.mage.burn_skill = True
        elif opt_id == "burn_dmg":
            self.mage.burn_explosion_damage += 0.25
        elif opt_id == "burn_rad":
            self.mage.burn_explosion_radius += 25
        elif opt_id == "unlock_pierce":
            self.mage.pierce_skill = True
        elif opt_id == "pierce_freq":
            self.mage.pierce_freq = max(1, self.mage.pierce_freq - 1)
        elif opt_id == "pierce_count":
            self.mage.pierce_count += 2
        elif opt_id == "unlock_cancel":
            self.mage.cancel_skill_prob = 0.15
        elif opt_id == "cancel_prob":
            self.mage.cancel_skill_prob = min(0.60, self.mage.cancel_skill_prob + 0.10)
        elif opt_id == "loco_dmg":
            self.mage.stats["damage_multiplier"] += 0.05

        if hasattr(self, 'pending_xp_boss') and self.pending_xp_boss > 0:
            if self.mage.gain_xp(self.pending_xp_boss):
                self.change_state(STATE_UPGRADE_SELECT)
                if self.snd_level and not self.muted:
                    self.snd_level.play()
            self.pending_xp_boss = 0
        else:
            if self.boss_instance and self.boss_instance.destruyendo:
                self.boss_instance.kill()
                self.boss_instance = None
            self.state = STATE_PLAYING

    def handle_collisions(self):
        if self.state != STATE_PLAYING:
            return

        now = pygame.time.get_ticks()
        damage_mult = 2 if self.mage.double_damage_active else 1

        for orb in pygame.sprite.spritecollide(self.mage, self.xp_orbs, True):
            if self.mage.gain_xp(orb.value):
                self.change_state(STATE_UPGRADE_SELECT)
                if self.snd_level and not self.muted:
                    self.snd_level.play()

        impacts = pygame.sprite.groupcollide(
            self.player_projectiles, self.monsters, False, False)
        for bullet, enemies in impacts.items():
            is_ray = getattr(bullet, 'is_ray', False)
            is_ice = getattr(bullet, 'ice', False)
            is_frag = getattr(bullet, 'fragmentation', False)
            penetration = getattr(bullet, 'penetration', 0)

            if not is_ray:
                if penetration <= 0:
                    reboted = False
                    if getattr(bullet, 'bounces', 0) > 0:
                        reboted = bullet.bounce(self.monsters, ignorar=enemies[0])
                    if not reboted:
                        bullet.kill()
                        if getattr(bullet, 'explosive', False):
                            bullet.fragment(self.all_sprites, self.player_projectiles, damage_mult)
                        if is_frag:
                            bullet.fragment(self.all_sprites, self.player_projectiles, damage_mult)
                else:
                    bullet.penetration -= 1

            for e in enemies:
                if getattr(bullet, 'burn', False):
                    e.burned = True
                    e.burn_timer = now
                    e.last_burn_damage = now
                    if getattr(bullet, 'fury_ignea', False):
                        e.fury_ignea_active = True

                e.hp -= bullet.damage
                if is_ice:
                    e.freeze()

                if getattr(bullet, 'critical', False):
                    crit = CriticalHit(e.rect.centerx, e.rect.centery)
                    self.all_sprites.add(crit)

                if e.hp <= 0:
                    if getattr(e, 'died_from_burn', False):
                        e.propagate_burn(self.monsters)
                        self._explosion_effect(e.rect.centerx, e.rect.centery, ORANGE_FIRE)

                    if getattr(e, 'burned', False) and not e.died_from_burn:
                        for m in self.monsters:
                            if m != e:
                                d = math.hypot(m.rect.centerx - e.rect.centerx,
                                              m.rect.centery - e.rect.centery)
                                if d < self.mage.burn_explosion_radius:
                                    m.hp -= bullet.damage * self.mage.burn_explosion_damage
                                    self._explosion_effect(m.rect.centerx, m.rect.centery, ORANGE_FIRE)

                    if e.frozen:
                        for i in range(8):
                            rad = math.radians(i * 45)
                            vx_f = math.cos(rad) * 7.5
                            vy_f = math.sin(rad) * 7.5
                            frag = Projectile(e.rect.centerx, e.rect.centery,
                                            vx_f, vy_f, 5, color=FROZEN_BLUE, ice=False)
                            self.all_sprites.add(frag)
                            self.player_projectiles.add(frag)
                        self._explosion_effect(e.rect.centerx, e.rect.centery, FROZEN_BLUE)

                    pts = POINTS_PER_ROW.get(e.row_original, 100)
                    if e.type == ENEMY_ELITE:
                        pts *= 3
                    self.score += pts
                    self._explosion_effect(e.rect.centerx, e.rect.centery, e.color)

                    xp = XPOrb(e.rect.centerx, e.rect.centery)
                    self.all_sprites.add(xp)
                    self.xp_orbs.add(xp)

                    drop_crystal = False
                    crystal_count = 0
                    if e.type == ENEMY_TREASURE:
                        drop_crystal = True
                        crystal_count = 5
                    elif e.type == ENEMY_ELITE:
                        drop_crystal = True
                        crystal_count = 2
                    elif random.random() < 0.02:
                        drop_crystal = True
                        crystal_count = 1
                    if drop_crystal:
                        self.data_manager.add_crystals(crystal_count)
                        color = GOLD_POWER if crystal_count > 1 else CYAN_MAGIC
                        self._draw_text(f"+{crystal_count}", self.font_sm, color,
                                       e.rect.centerx, e.rect.centery - 20)

                    if self.snd_death and not self.muted:
                        self.snd_death.play()
                    self._drop_powerup(e.rect.centerx, e.rect.centery, now)
                    e.kill()

        if self.mage.orbital_active:
            orb_impacts = pygame.sprite.groupcollide(
                self.mage.orbitales_grupo, self.monsters, False, False)
            for orb, enemies in orb_impacts.items():
                for e in enemies:
                    if random.random() < 0.1:
                        self._explosion_effect(e.rect.centerx, e.rect.centery, ORBITAL_RED)
                    e.hp -= orb.damage * 0.2
                    if e.hp <= 0:
                        self.score += 10
                        self._explosion_effect(e.rect.centerx, e.rect.centery, e.color)
                        e.kill()

            orb_proj_impacts = pygame.sprite.groupcollide(
                self.mage.orbitales_grupo, self.enemy_projectiles, False, True)
            for orb, projs in orb_proj_impacts.items():
                for p in projs:
                    self._explosion_effect(p.rect.centerx, p.rect.centery, ORBITAL_RED)

        pygame.sprite.groupcollide(self.player_projectiles, self.barriers, False, False)

        if self.boss_instance and not self.boss_instance.destruyendo:
            h = pygame.sprite.spritecollide(self.boss_instance, self.player_projectiles, False)
            for b in h:
                if not self.boss_instance:
                    break
                is_ray = getattr(b, 'is_ray', False)
                is_ice = getattr(b, 'ice', False)
                if not is_ray:
                    b.kill()
                self.boss_instance.hp -= (40 if is_ray else b.damage)
                if is_ice:
                    self.boss_instance.freeze()
                self._explosion_effect(b.rect.centerx, b.rect.centery, PURPLE_DARK)
                if self.boss_instance.hp <= 0:
                    self.score += 2000 * (self.level // BOSS_FREQUENCY)
                    self.data_manager.add_crystals(10)
                    self.data_manager.register_boss_kill()

                    if self.level == 10 and isinstance(self.boss_instance, BossSNAKE):
                        if self.boss_instance:
                            self.boss_instance.kill()
                        self.boss_instance = None
                        self.data_manager.add_crystals(100)
                        if self.difficulty == MODE_HARD:
                            self.data_manager.data["special_abilities"]["snake"] = True
                            self.data_manager.save()
                        self.victory_clicks = 0
                        self.change_state(STATE_VICTORY)
                        break
                    elif self.level == 5:
                        if self.boss_instance:
                            self.boss_instance.kill()
                        self.boss_instance = None
                        self.level += 1
                        self._boss_reward()
                        break
                    else:
                        if self.boss_instance:
                            self.boss_instance.kill()
                        self.boss_instance = None
                        self.pending_xp_boss = (ENEMY_ROWS * ENEMY_COLUMNS * XP_PER_ENEMIGO) // 2
                        self.change_state(STATE_BOSS_REWARD)

        if self.boss_instance and not self.boss_instance.alive():
            for c in self.puddles:
                c.kill()
            if self.level == 10 and isinstance(self.boss_instance, BossSNAKE):
                self.boss_instance = None
                self.data_manager.add_crystals(100)
                if self.difficulty == MODE_HARD:
                    self.data_manager.data["special_abilities"]["snake"] = True
                    self.data_manager.save()
                self.victory_clicks = 0
                self.change_state(STATE_VICTORY)
            else:
                self.boss_instance = None
                self.level += 1
                self.change_state(STATE_TRANSITION)

        pygame.sprite.groupcollide(self.enemy_projectiles, self.barriers, False, False)

        if self.mage.special_shield and self.mage.special_shield.active:
            shield_impacts = pygame.sprite.spritecollide(
                self.mage.special_shield, self.enemy_projectiles, False)
            for p in shield_impacts:
                damage_rebound = (BASE_PLAYER_DAMAGE * self.mage.stats["damage_multiplier"] * 2)
                p.is_enemy = False
                p.damage = damage_rebound
                p.vx *= -1
                p.color = CYAN_MAGIC
                p.explosive = True
                p.image = pygame.Surface((10 * 2 + 6, 10 * 2 + 6), pygame.SRCALPHA)
                pygame.draw.circle(p.image, CYAN_MAGIA, (10 + 3, 10 + 3), 10)
                pygame.draw.circle(p.image, BLANCO, (10 + 3, 10 + 3), 10 // 3)
                p.rect = p.image.get_rect(center=p.rect.center)
                self.mage.special_shield.deactivate()

        enemy_proj_hits = pygame.sprite.spritecollide(self.mage, self.enemy_projectiles, True)
        for p in enemy_proj_hits:
            if getattr(p, 'bomb', False) and self.boss_instance:
                ptype = "fire" if self.boss_instance.variant == BOSS_TYPE_FIRE else (
                    "poison" if self.boss_instance.variant == BOSS_TYPE_TOXIC else "ice")
                puddle = Puddle(p.rect.centerx, SCREEN_HEIGHT - 50, ptype)
                self.puddles.add(puddle)
                self.all_sprites.add(puddle)

            if self.mage.take_damage():
                self.screen_shake = 10
                self.flash_alpha = 150
                self._explosion_effect(self.mage.rect.centerx, self.mage.rect.top, MAGE_BLUE)
                if self.boss_instance and self.boss_instance.variant == BOSS_TYPE_ICE:
                    self.mage.apply_slow()
                if self.mage.lives <= 0:
                    self.change_state(STATE_GAMEOVER)

        if self.mage.cancel_skill_prob > 0:
            bullet_collisions = pygame.sprite.groupcollide(
                self.player_projectiles, self.enemy_projectiles, False, False)
            for player_b, enemy_bullets in bullet_collisions.items():
                for enemy_b in enemy_bullets:
                    if random.random() < self.mage.cancel_skill_prob:
                        self._explosion_effect(enemy_b.rect.centerx, enemy_b.rect.centery, BLANCO)
                        player_b.kill()
                        enemy_b.kill()
                        break

        for s in self.all_sprites:
            if isinstance(s, LaserSNAKE):
                rad = math.radians(s.angle)
                for d in range(0, 1000, 20):
                    px = s.x + math.cos(rad) * d
                    py = s.y + math.sin(rad) * d
                    if self.mage.rect.collidepoint(px, py):
                        self.mage.take_damage()
                        break
                    for b in self.barriers:
                        if b.rect.collidepoint(px, py):
                            break

        if self.boss_instance and hasattr(self.boss_instance, 'embestiendo') and self.boss_instance.embestiendo:
            if pygame.sprite.collide_rect(self.mage, self.boss_instance):
                if self.mage.take_damage():
                    self.screen_shake = 15
                    self.flash_alpha = 200
                    self._explosion_effect(self.mage.rect.centerx, self.mage.rect.top, RED_LIFE)

        for p in self.enemy_projectiles:
            if p.rect.bottom >= SCREEN_HEIGHT - 50 and (
                getattr(p, 'bomb', False) or getattr(p, 'radio_custom', 0) > 30):
                if self.boss_instance:
                    ptype = "fire" if self.boss_instance.variant == BOSS_TYPE_FIRE else (
                        "poison" if self.boss_instance.variant == BOSS_TYPE_TOXIC else "ice")
                    c = Puddle(p.rect.centerx, SCREEN_HEIGHT - 50, ptype)
                    self.puddles.add(c)
                    self.all_sprites.add(c)
                p.kill()
                self._explosion_effect(p.rect.centerx, p.rect.bottom, PURPLE_CHARGED)

        puddle_hits = pygame.sprite.spritecollide(self.mage, self.puddles, False)
        for p in puddle_hits:
            if p.type == "ice":
                self.mage.sliding = True
                if random.random() < 0.1:
                    self.mage.momentum_x += random.choice([-2, 2])
            elif p.type == "poison":
                now = pygame.time.get_ticks()
                if not hasattr(self.mage, "last_poison"):
                    self.mage.last_poison = 0
                if now - self.mage.last_poison > POISON_TICK:
                    self.mage.take_damage()
                    self.mage.last_poison = now
            elif p.type == "fire":
                self.mage.take_damage()

        for p in pygame.sprite.spritecollide(self.mage, self.powerups, True):
            self.time_without_powerup = 0
            if p.type == "reparar_barriers":
                self._create_barriers()
                if self.snd_powerup and not self.muted:
                    self.snd_powerup.play()
            else:
                self.mage.apply_powerup(p.type)
                if self.snd_powerup and not self.muted:
                    self.snd_powerup.play()

        for c in pygame.sprite.spritecollide(self.mage, self.hearts, True):
            if self.mage.lives < self.mage.max_lives:
                self.mage.lives += 1
            if self.snd_powerup and not self.muted:
                self.snd_powerup.play()

        if self.mage.shield_pending:
            targets = list(self.monsters) + (
                [self.boss_instance] if self.boss_instance and not self.boss_instance.destruyendo else [])
            for m in targets:
                if m and math.hypot(self.mage.rect.centerx - m.rect.centerx,
                                   self.mage.rect.centery - m.rect.centery) < self.mage.shield_radius:
                    self.mage.activate_shield()
                    break
        if self.mage.shield_active:
            for m in list(self.monsters):
                if math.hypot(self.mage.rect.centerx - m.rect.centerx,
                             self.mage.rect.centery - m.rect.centery) < self.mage.shield_radius:
                    self._explosion_effect(m.rect.centerx, m.rect.centery, ORANGE_FUEGO)
                    m.kill()

    def _boss_reward(self):
        self.pending_xp_boss = (ENEMY_ROWS * ENEMY_COLUMNS * XP_PER_ENEMIGO) // 2
        self.is_level_5_boss = (self.level == 5)
        self._generate_boss_options()
        self.change_state(STATE_BOSS_REWARD)
        if self.mage.lives < self.mage.max_lives:
            self.mage.lives += 1

    def _explosion_effect(self, x, y, color):
        for _ in range(16):
            p = Particle(x, y, color)
            self.particles.add(p)
            self.all_sprites.add(p)

    def _drop_powerup(self, x, y, now):
        bonus = 0.0
        if self.time_without_powerup > POWERUP_BONUS_THRESHOLD_MS:
            extra_time = self.time_without_powerup - POWERUP_BONUS_THRESHOLD_MS
            bonus = min(MAX_POWERUP_BONUS, (extra_time / 1000.0) * POWERUP_BONUS_PER_SECOND)
            if self.boss_instance and not self.boss_instance.destruyendo:
                bonus *= BOSS_POWERUP_BONUS_MULTIPLIER

        total_barrier_hp = sum(b.hp for b in self.barriers)

        if total_barrier_hp == 0 and random.random() < 0.15:
            pu = PowerUp(x, y, "reparar_barriers")
            self.powerups.add(pu)
            self.all_sprites.add(pu)
            return

        roll = random.random()
        base_prob = POWERUP_BASE_PROBABILITY + bonus
        if self.level >= 10:
            base_prob = POWERUP_ENDGAME_PROBABILITY + bonus

        if roll < HEART_PROBABILITY:
            c = Heart(x, y, now)
            self.hearts.add(c)
            self.all_sprites.add(c)
        elif roll < POWERUP_RAY_PROBABILITY + bonus:
            p = PowerUp(x, y, "rayo")
            self.powerups.add(p)
            self.all_sprites.add(p)
        elif roll < base_prob:
            types = ["cadencia", "arco", "disparo_doble", "disparo_triple",
                    "explosivo", "escudo", "doble_danio"]
            if self.mage.run_level >= UNLOCK_ORBITAL_LEVEL:
                types.append("orbital")
            if self.mage.run_level >= UNLOCK_HOMING_LEVEL:
                types.append("homing")
            t = random.choice(types)
            p = PowerUp(x, y, t)
            self.powerups.add(p)
            self.all_sprites.add(p)

    def _generate_powerup(self, x, y):
        if random.random() < POWERUP_RAY_PROBABILITY:
            pu = PowerUp(x, y, "rayo")
            self.all_sprites.add(pu)
            self.powerups.add(pu)
            return
        opts = list(POWERUP_COLORS.keys())
        if "rayo" in opts:
            opts.remove("rayo")
        if self.mage.shield_active or self.mage.shield_pending:
            if "escudo" in opts:
                opts.remove("escudo")
        if self.mage.stats["extra_projectiles"] > 1 and "disparo_doble" in opts:
            opts.remove("disparo_doble")
        kills = self.data_manager.data.get("boss_kills", 0)
        if kills < UNLOCK_ORBITAL_LEVEL and "orbital" in opts:
            opts.remove("orbital")
        if kills < UNLOCK_HOMING_LEVEL and "homing" in opts:
            opts.remove("homing")
        if opts:
            pu = PowerUp(x, y, random.choice(opts))
            self.all_sprites.add(pu)
            self.powerups.add(pu)

    def _draw_text(self, text, font, color, x, y):
        s = font.render(str(text), True, color)
        r = s.get_rect(center=(x, y))
        self.screen.blit(s, r)

    def process_touch_controls(self):
        if not self.touch_controls_enabled or self.state != STATE_PLAYING:
            return

        for touch_id, (tx, ty) in self.active_touches.items():
            if self.zone_left.collidepoint(tx, ty):
                self.mage.move_left = True
                self.mage.move_right = False
                self.left_zone_active = True

            if self.zone_right.collidepoint(tx, ty):
                self.mage.move_right = True
                self.mage.move_left = False
                self.right_zone_active = True

            if self.zone_shoot.collidepoint(tx, ty):
                self.mage.shooting_touch = True
                self.shoot_zone_active = True

    def reset_touch_movement(self):
        if not self.touch_controls_enabled:
            return

        left_touch = False
        right_touch = False
        shoot_touch = False

        for touch_id, (tx, ty) in self.active_touches.items():
            if self.zone_left.collidepoint(tx, ty):
                left_touch = True
            if self.zone_right.collidepoint(tx, ty):
                right_touch = True
            if self.zone_shoot.collidepoint(tx, ty):
                shoot_touch = True

        self.left_zone_active = left_touch
        self.right_zone_active = right_touch
        self.shoot_zone_active = shoot_touch

        if not left_touch:
            self.mage.move_left = False
        if not right_touch:
            self.mage.move_right = False
        if not shoot_touch:
            self.mage.shooting_touch = False
            if self.mage.type == "snake" and self.mage.charging:
                self.mage.release_charge(self.player_projectiles)

    def draw_touch_controls(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        if self.left_zone_active:
            pygame.draw.polygon(s, (100, 200, 255, 180), [
                (25, SCREEN_HEIGHT - 75),
                (10, SCREEN_HEIGHT - 60),
                (25, SCREEN_HEIGHT - 45)
            ], 3)
            pygame.draw.line(s, (100, 200, 255, 100), (25, SCREEN_HEIGHT - 60), (5, SCREEN_HEIGHT - 60), 2)

        if self.right_zone_active:
            pygame.draw.polygon(s, (100, 200, 255, 180), [
                (SCREEN_WIDTH - 25, SCREEN_HEIGHT - 75),
                (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 60),
                (SCREEN_WIDTH - 25, SCREEN_HEIGHT - 45)
            ], 3)
            pygame.draw.line(s, (100, 200, 255, 100), (SCREEN_WIDTH - 25, SCREEN_HEIGHT - 60),
                           (SCREEN_WIDTH - 5, SCREEN_HEIGHT - 60), 2)

        if self.shoot_zone_active:
            pygame.draw.circle(s, (255, 100, 100, 150), (SCREEN_WIDTH - 45, SCREEN_HEIGHT - 60), 20, 3)
            pygame.draw.circle(s, (255, 100, 100, 80), (SCREEN_WIDTH - 45, SCREEN_HEIGHT - 60), 12)

        self.screen.blit(s, (0, 0))

    def draw_background(self):
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            bioma_idx = (self.level - 1) // 5 % 3
            palette = BIOMES.get(bioma_idx, BIOMES[0])

            if not hasattr(self, 'background_cache') or self.background_cache is None:
                self.background_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background_cache.fill(palette["grass"])

                for _ in range(200):
                    bx = random.randint(0, SCREEN_WIDTH)
                    by = random.randint(0, SCREEN_HEIGHT)
                    bcolor = palette["var1"] if random.random() < 0.5 else palette["var2"]
                    pygame.draw.rect(self.background_cache, bcolor, (bx, by, 4, 4))

                for _ in range(15):
                    bx = random.randint(0, SCREEN_WIDTH)
                    by = random.randint(0, 100)
                    pygame.draw.circle(self.background_cache, palette["tree_bg"],
                                      (bx, by), random.randint(20, 40))

            self.screen.blit(self.background_cache, (0, 0))

        s_fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for layer in self.fog_layers:
            pygame.draw.ellipse(s_fog, (*FOG_COLOR, 40),
                               (layer['x'], layer['y'], layer['width'], 80))
            if layer['x'] + layer['width'] > SCREEN_WIDTH:
                pygame.draw.ellipse(s_fog, (*FOG_COLOR, 40),
                                   (layer['x'] - SCREEN_WIDTH - 300, layer['y'],
                                    layer['width'], 80))
        self.screen.blit(s_fog, (0, 0))

    def draw_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 255))
        self.screen.blit(overlay, (0, 0))
        self._draw_text("ARCANE SHOP", self.font_lg, GOLD_POWER, SCREEN_WIDTH // 2, 50)
        self._draw_text(f"Your Crystals: {self.data_manager.data['crystals']}",
                       self.font_md, CYAN_MAGIA, SCREEN_WIDTH // 2, 90)

        items = ["base_lives", "base_damage", "crit_chance"]
        rects = [
            pygame.Rect(SCREEN_WIDTH // 2 - 250, 120, 160, 180),
            pygame.Rect(SCREEN_WIDTH // 2 - 80, 120, 160, 180),
            pygame.Rect(SCREEN_WIDTH // 2 + 90, 120, 160, 180)
        ]

        for i, key in enumerate(items):
            info = SHOP_ITEMS.get(key, {"base": 100, "max": 10})
            lvl = self.data_manager.data["upgrades"].get(key, 0)
            r = rects[i]
            pygame.draw.rect(self.screen, CARD_GRAY, r, border_radius=15)
            pygame.draw.rect(self.screen, BORDER_GRAY, r, 3, border_radius=15)
            self._draw_text(info["name"], self.font_md, WHITE, r.centerx, r.top + 30)
            self._draw_text(f"Level: {lvl}/{info['max']}", self.font_sm, GOLD_POWER,
                           r.centerx, r.top + 60)
            cost = int(info["base"] * (SHOP_COST_FACTOR ** lvl))
            if lvl >= info["max"]:
                cost_text = "MAX"
                c_cost = RED_LIFE
            else:
                cost_text = f"{cost} Gems"
                c_cost = CYAN_MAGIA if self.data_manager.data['crystals'] >= cost else RED_LIFE
            self._draw_text(cost_text, self.font_md, c_cost, r.centerx, r.bottom - 40)

        pygame.draw.rect(self.screen, RED_LIFE, self.btn_shop, border_radius=10)
        self._draw_text("BACK TO MENU", self.font_md, WHITE,
                       self.btn_shop.centerx, self.btn_shop.centery)

    def draw_hud(self):
        s = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        s.fill(HUD_BG)
        self.screen.blit(s, (0, 0))

        if DEBUG_MODE:
            debug_text = "DEBUG MODE"
            if DEBUG_GOD_MODE:
                debug_text += " [GOD]"
            if DEBUG_INFINITE_CHARGES:
                debug_text += " [INF]"
            self._draw_text(debug_text, self.font_sm, (255, 0, 255), SCREEN_WIDTH // 2, 5)

        pygame.draw.rect(self.screen, BUTTON_GRAY, [20, 48, 150, 8])
        px = (self.mage.xp / self.mage.xp_required) * 150
        pygame.draw.rect(self.screen, XP_GREEN, [20, 48, px, 8])

        self.screen.blit(self.font_md.render(f"LEVEL {self.level}", True, WHITE), (20, 15))
        self.screen.blit(self.font_sm.render(f"Run Lvl: {self.mage.run_level}", True, WHITE_ICE),
                        (100, 22))
        self.screen.blit(self.font_sm.render(f"GEMS: {self.data_manager.data['crystals']}", True, CYAN_MAGIA),
                        (180, 22))

        self._draw_text(f"{self.score}", self.font_lg, GOLD_POWER, SCREEN_WIDTH // 2, 35)

        start_x_hearts = SCREEN_WIDTH - 40
        for i in range(min(10, self.mage.lives)):
            pygame.draw.circle(self.screen, RED_LIFE,
                              (start_x_hearts - (i * 25), 25), 10)
        if self.mage.lives > 10:
            self._draw_text(f"+{self.mage.lives - 10}", self.font_sm, RED_LIFE,
                           start_x_hearts - 260, 25)

        now = pygame.time.get_ticks()
        info_parts = []

        if self.mage.special_shield and self.mage.special_shield_unlocked:
            if self.mage.special_shield.active:
                info_parts.append("ARCANE MIRROR ACTIVE")
            elif not self.mage.special_shield.active and self.mage.special_shield.rebounced:
                cd = max(0, (self.mage.special_shield.respawn_timer - now) // 1000)
                info_parts.append(f"ARCANE MIRROR: {cd}s")

        if self.mage.shield_pending:
            info_parts.append("SHIELD READY")

        pu = self.mage.current_powerup
        if pu != "normal":
            pu_text = pu.upper()
            if pu == "cadencia":
                pu_text += f" ({max(0, (self.mage.powerup_end - now) // 1000)}s)"
            elif self.mage.charges > 0:
                pu_text += f" x{self.mage.charges}"
            info_parts.append(pu_text)

        if self.mage.double_damage_active:
            info_parts.append(f"2x DMG ({max(0, (self.mage.double_damage_end - now) // 1000)}s)")

        if info_parts:
            full_text = " | ".join(info_parts)
            self._draw_text(full_text, self.font_sm, CYAN_MAGIA, SCREEN_WIDTH // 2, 85)

        if self.boss_instance and not self.boss_instance.destruyendo:
            bw = 180
            w = (self.boss_instance.hp / self.boss_instance.hp_max) * bw
            bx = SCREEN_WIDTH - bw - 40
            by = 52

            pygame.draw.rect(self.screen, (40, 0, 80), [bx - 2, by - 2, bw + 4, 14], border_radius=3)
            pygame.draw.rect(self.screen, BLACK, [bx, by, bw, 10], border_radius=2)
            pygame.draw.rect(self.screen, PURPLE_DARK, [bx, by, w, 10], border_radius=2)

            if w > 0:
                pygame.draw.rect(self.screen, (180, 100, 255), [bx, by, w, 3], border_radius=2)

            boss_name = "BOSS"
            if self.boss_instance.variant == BOSS_TYPE_ICE:
                boss_name = "ICE BOSS"
            elif self.boss_instance.variant == BOSS_TYPE_FIRE:
                boss_name = "FIRE BOSS"
            elif self.boss_instance.variant == BOSS_TYPE_TOXIC:
                boss_name = "TOXIC BOSS"

            self._draw_text(boss_name, self.font_sm, WHITE, bx + bw // 2, by - 14)

        if self.powerup_notification:
            alpha = 255
            elapsed = pygame.time.get_ticks() - self.powerup_notification_time
            if elapsed > 2500:
                alpha = max(0, 255 - (elapsed - 2500) * 5)
            s = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, (0, SCREEN_HEIGHT // 2 - 25))
            self._draw_text(self.powerup_notification, self.font_md, GOLD_POWER,
                           SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def draw(self):
        ox, oy = (random.randint(-4, 4), random.randint(-4, 4)) if self.screen_shake > 0 else (0, 0)
        self.draw_background()
        for p in self.ambient_particles:
            self.screen.blit(p.image, p.rect)

        if self.state == STATE_MENU:
            self._draw_text("MAGO DEFENCE", self.font_lg, MAGE_BLUE, SCREEN_WIDTH // 2, 100)
            self._draw_text("By Jose C Sierra", self.font_sm, GOLD_POWER, SCREEN_WIDTH // 2, 140)
            if self.data_manager.data["high_score"] > 0:
                self._draw_text(f"RECORD: {self.data_manager.data['high_score']}",
                               self.font_md, WHITE, SCREEN_WIDTH // 2, 180)
            self._draw_text(f"CRYSTALS: {self.data_manager.data['crystals']}",
                           self.font_md, CYAN_MAGIA, SCREEN_WIDTH // 2, 220)
            kills = self.data_manager.data.get("boss_kills", 0)
            if kills > 0:
                self._draw_text(f"Bosses Defeated: {kills}", self.font_sm, PURPLE_DARK,
                               SCREEN_WIDTH // 2, 250)

            pygame.draw.rect(self.screen, BUTTON_GRAY, self.btn_toggle_touch, border_radius=12)
            self._draw_text("TOUCH: " + ("ON" if self.touch_controls_enabled else "OFF"),
                           self.font_sm, WHITE, self.btn_toggle_touch.centerx,
                           self.btn_toggle_touch.centery)

            pygame.draw.rect(self.screen, GREEN_PLAY, self.btn_play, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, self.btn_play, 3, border_radius=15)
            self._draw_text("PLAY", self.font_md, WHITE, self.btn_play.centerx,
                           self.btn_play.centery)

            c_norm = SELECTION_YELLOW if self.difficulty == MODE_NORMAL else BUTTON_GRAY
            c_hard = RED_DELETE if self.difficulty == MODE_HARD else BUTTON_GRAY
            pygame.draw.rect(self.screen, c_norm, self.btn_diff_normal, border_radius=8)
            self._draw_text("NORMAL", self.font_sm, BLACK if self.difficulty == MODE_NORMAL else WHITE,
                           self.btn_diff_normal.centerx, self.btn_diff_normal.centery)
            pygame.draw.rect(self.screen, c_hard, self.btn_diff_hard, border_radius=8)
            self._draw_text("HARD", self.font_sm, WHITE, self.btn_diff_hard.centerx,
                           self.btn_diff_hard.centery)

            pygame.draw.rect(self.screen, PURPLE_CHARGED, self.btn_shop, border_radius=10)
            self._draw_text("SHOP", self.font_md, WHITE, self.btn_shop.centerx,
                           self.btn_shop.centery)

            c_del = RED_DELETE if not self.delete_confirmation else (255, 0, 0)
            pygame.draw.rect(self.screen, c_del, self.btn_delete, border_radius=8)
            txt = "DELETE DATA" if not self.delete_confirmation else "SURE?"
            self._draw_text(txt, self.font_sm, WHITE, self.btn_delete.centerx,
                           self.btn_delete.centery)

        elif self.state == STATE_SHOP:
            self.draw_shop()

        elif self.state == STATE_CHARACTER_SELECT:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            self.screen.blit(overlay, (0, 0))
            self._draw_text("CHOOSE YOUR MAGE", self.font_lg, WHITE, SCREEN_WIDTH // 2, 60)
            diff_text = "MODE: NORMAL" if self.difficulty == MODE_NORMAL else "MODE: HARD"
            c_diff = GREEN_BARRIER if self.difficulty == MODE_NORMAL else RED_LIFE
            self._draw_text(diff_text, self.font_md, c_diff, SCREEN_WIDTH // 2, 100)

            chars = list(CHARACTER_CONFIGS.keys())
            for i, char_key in enumerate(chars):
                self._draw_char_card(self.char_rects[i], char_key)

            self._draw_text("Click to select and start", self.font_sm, WHITE,
                           SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)

        elif self.state in (STATE_PLAYING, STATE_PAUSE, STATE_GAMEOVER,
                          STATE_TRANSITION, STATE_UPGRADE_SELECT, STATE_BOSS_REWARD,
                          STATE_VICTORY):
            balcony_y = SCREEN_HEIGHT - 50
            pygame.draw.rect(self.screen, (40, 40, 50), [0, balcony_y, SCREEN_WIDTH, SCREEN_HEIGHT - balcony_y])
            pygame.draw.line(self.screen, (100, 100, 120), (0, balcony_y), (SCREEN_WIDTH, balcony_y), 5)
            pygame.draw.rect(self.screen, (20, 20, 30), [0, balcony_y + 5, SCREEN_WIDTH, 10])

            for s in self.all_sprites:
                self.screen.blit(s.image, (s.rect.x + ox, s.rect.y + oy))
            if self.mage.orbital_active:
                for o in self.mage.orbitales_grupo:
                    self.screen.blit(o.image, (o.rect.x + ox, o.rect.y + oy))

            if self.mage.shield_radius and getattr(self.mage, 'shield_pending', False):
                r = self.mage.shield_radius
                pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5
                alpha = int(30 + (pulse * 40))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*SHIELD_PENDING_COLOR, alpha), (r, r), r, width=2)
                self.screen.blit(s, (self.mage.rect.centerx - r + ox, self.mage.rect.centery - r + oy))

            if self.mage.type == "snake" and self.mage.charging:
                bar_w, bar_h = 60, 8
                bar_x = self.mage.rect.centerx - bar_w // 2 + ox
                bar_y = self.mage.rect.bottom + 10 + oy
                pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
                progress = self.mage.charge / self.mage.max_charge
                bar_c = (0, 255, 0) if progress >= 1.0 else (255, 200, 0)
                pygame.draw.rect(self.screen, bar_c, (bar_x, bar_y, int(bar_w * progress), bar_h))
                pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
                txt = "READY!" if progress >= 1.0 else "CHARGING"
                self._draw_text(txt, self.font_xs, bar_c, bar_x + bar_w // 2, bar_y - 10)

            self.draw_hud()

            if self.mage.shield_active:
                r = self.mage.shield_radius
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, SHIELD_ACTIVE_COLOR, (r, r), r)
                self.screen.blit(s, (self.mage.rect.centerx - r + ox, self.mage.rect.centery - r + oy))

            if self.touch_controls_enabled and self.state == STATE_PLAYING:
                self.draw_touch_controls()

            if self.state == STATE_PAUSE:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 190))
                self.screen.blit(overlay, (0, 0))
                self._draw_text("PAUSED", self.font_lg, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
                self._draw_text("M: Menu | Esc/P: Return", self.font_sm, WHITE,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)

            if self.state == STATE_TRANSITION:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0, 0))
                self._draw_text(f"LEVEL {self.level - 1} CLEARED!", self.font_lg, GOLD_POWER,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
                self._draw_text("Preparing next wave...", self.font_sm, WHITE,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)

            elif self.state in (STATE_UPGRADE_SELECT, STATE_BOSS_REWARD):
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 180))
                self.screen.blit(s, (0, 0))
                title = "LEVEL UP" if self.state == STATE_UPGRADE_SELECT else "BOSS REWARD"
                self._draw_text(title, self.font_lg, GOLD_POWER, SCREEN_WIDTH // 2, 80)
                sub = "Choose an upgrade:" if self.state == STATE_UPGRADE_SELECT else "Choose a reward:"
                self._draw_text(sub, self.font_md, WHITE, SCREEN_WIDTH // 2, 130)

                opts = (self.current_upgrade_options if self.state == STATE_UPGRADE_SELECT
                       else self.boss_options)
                for i, opt in enumerate(opts):
                    rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150 + i * 130, 300, 110)
                    self._draw_upgrade_card(rect, opt["title"], opt["desc"], opt["color"])
                self._draw_text("(Use Click or Keys 1, 2, 3)", self.font_sm, WHITE,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)

            if self.state == STATE_GAMEOVER:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((60, 0, 0, 210))
                self.screen.blit(overlay, (0, 0))
                self._draw_text("GAME OVER", self.font_lg, RED_LIFE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
                self._draw_text(f"SCORE: {self.score}", self.font_md, WHITE,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)
                remaining = max(0, 2000 - (pygame.time.get_ticks() - self.state_start_time))
                if remaining > 0:
                    self._draw_text(f"Wait {int(remaining / 100) + 1}...", self.font_sm, WHITE,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
                else:
                    self._draw_text("Touch to return to Menu", self.font_sm, WHITE,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)

            elif self.state == STATE_VICTORY:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 60, 0, 210))
                self.screen.blit(overlay, (0, 0))
                self._draw_text("VICTORY!", self.font_lg, GREEN_BARRIER,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)
                self._draw_text("Safe Home", self.font_md, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
                self._draw_text(f"+100 GEMS", self.font_md, GOLD_POWER,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
                self._draw_text(f"Clicks left: {3 - getattr(self, 'victory_clicks', 0)}",
                               self.font_sm, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
                self._draw_text("Press 3 times to return to menu", self.font_sm, (200, 200, 200),
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120)

        if self.flash_alpha > 0:
            f = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            f.fill(BLANCO)
            f.set_alpha(self.flash_alpha)
            self.screen.blit(f, (0, 0))

        c_mute = RED_LIFE if self.muted else GREEN_BARRIER
        pygame.draw.rect(self.screen, c_mute, self.btn_mute, border_radius=6)
        self._draw_text("M", self.font_sm, BLACK, self.btn_mute.centerx, self.btn_mute.centery)
        pygame.display.flip()

    def _draw_char_card(self, rect, char_key):
        char_data = CHARACTER_CONFIGS.get(char_key, CHARACTER_CONFIGS["MAGO"])
        unlocked = True
        if char_key == "el_loco":
            unlocked = (self.data_manager.data.get("unlocked_loco", False) or
                       (DEBUG_MODE and DEBUG_ALL_UNLOCKED))
        elif char_key == "snake":
            unlocked = (self.data_manager.data.get("unlocked_snake", False) or
                       (DEBUG_MODE and DEBUG_ALL_UNLOCKED))

        if DEBUG_MODE and DEBUG_ALL_UNLOCKED:
            unlocked = True

        if not unlocked:
            pygame.draw.rect(self.screen, (20, 20, 20), rect, border_radius=15)
            pygame.draw.rect(self.screen, DISABLED_GRAY, rect, 2, border_radius=15)
            if char_key == "snake":
                self._draw_text("???", self.font_md, DISABLED_GRAY, rect.centerx, rect.top + 60)
                self._draw_text("Defeat final boss", self.font_xs, DISABLED_GRAY,
                               rect.centerx, rect.top + 100)
                self._draw_text("on Hard", self.font_xs, DISABLED_GRAY,
                               rect.centerx, rect.top + 120)
            else:
                self._draw_text("???", self.font_md, DISABLED_GRAY, rect.centerx, rect.top + 60)
                self._draw_text("Reach level 10", self.font_xs, DISABLED_GRAY,
                               rect.centerx, rect.top + 100)
                self._draw_text("to unlock", self.font_xs, DISABLED_GRAY,
                               rect.centerx, rect.top + 120)
            return

        pygame.draw.rect(self.screen, CARD_GRAY, rect, border_radius=15)
        c_border = GOLD_POWER if self.selected_character == char_key else BORDER_GRAY
        pygame.draw.rect(self.screen, c_border, rect,
                        3 if self.selected_character == char_key else 5, border_radius=15)

        sprite_path = resolve_path(char_data.get("sprite_front", char_data["sprite"]))
        if os.path.exists(sprite_path):
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                img = pygame.transform.scale(img, (70, 70))
                self.screen.blit(img, (rect.centerx - 35, rect.top + 25))
            except:
                pass

        self._draw_text(char_data["name"], self.font_md, char_data["color"],
                       rect.centerx, rect.top + 105)
        self._draw_text(char_data["description"], self.font_sm, WHITE,
                       rect.centerx, rect.top + 130)
        self._draw_text(char_data["detail"], self.font_xs, DISABLED_GRAY,
                       rect.centerx, rect.top + 150)

        pygame.draw.line(self.screen, (80, 80, 90), (rect.left + 15, rect.top + 170),
                        (rect.right - 15, rect.top + 170), 1)

        s = char_data.get("stats_base", {})
        y_stats = rect.top + 185
        self._draw_text(f"Damage: {s.get('damage_multiplier', 1.0):.1f}x", self.font_xs,
                       ORANGE_FIRE, rect.centerx, y_stats)
        self._draw_text(f"Speed: {s.get('attack_speed_multi', 1.0):.1f}x", self.font_xs,
                       CYAN_MAGIA, rect.centerx, y_stats + 20)

        mods = []
        if s.get("modifiers"):
            mods.extend([m.upper() for m in s["modifiers"]])
        if s.get("extra_projectiles", 0) > 0:
            mods.append(f"MULTI +{s['extra_projectiles']}")
        if mods:
            y_mods = y_stats + 40
            for i, mod in enumerate(mods):
                self._draw_text(f"[{mod}]", self.font_xs, GOLD_POWER,
                               rect.centerx, y_mods + (i * 18))

    def _draw_upgrade_card(self, rect, title, desc, color):
        pygame.draw.rect(self.screen, CARD_GRAY, rect, border_radius=15)
        pygame.draw.rect(self.screen, color, rect, 3, border_radius=15)
        self._draw_text(title, self.font_md, color, rect.centerx, rect.top + 35)
        words = desc.split(' ')
        lines = []
        line = ""
        for w in words:
            if len(line + w) > 18:
                lines.append(line)
                line = w + " "
            else:
                line += w + " "
        lines.append(line)
        y_off = 75
        for l in lines:
            self._draw_text(l, self.font_sm, WHITE, rect.centerx, rect.top + y_off)
            y_off += 25

    def update(self):
        self._handle_environment()
        if self.screen_shake > 0:
            self.screen_shake -= 1
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 5)
        if self.powerup_notification and pygame.time.get_ticks() - self.powerup_notification_time > 3000:
            self.powerup_notification = None

        self.process_touch_controls()

        if self.state == STATE_PLAYING:
            now = pygame.time.get_ticks()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] or self.mage.shooting_touch:
                self.mage.shoot(self.monsters)

            if self.mage.lives < self.mage.max_lives and random.random() < HEART_PROBABILITY:
                c = Heart(random.randint(40, SCREEN_WIDTH - 40), -30)
                self.all_sprites.add(c)
                self.hearts.add(c)

            bonus = 0.0
            if self.time_without_powerup > POWERUP_BONUS_THRESHOLD_MS:
                extra = self.time_without_powerup - POWERUP_BONUS_THRESHOLD_MS
                bonus = min(MAX_POWERUP_BONUS, (extra / 1000.0) * POWERUP_BONUS_PER_SECOND)
                if self.boss_instance and not self.boss_instance.destruyendo:
                    bonus *= BOSS_POWERUP_BONUS_MULTIPLIER * 0.5

            since_last = now - self.last_sky_powerup_spawn
            if since_last > MIN_POWERUP_INTERVAL:
                prob = POWERUP_SKY_PROBABILITY + bonus
                if random.random() < prob:
                    self._generate_powerup(random.randint(60, SCREEN_WIDTH - 60), -40)
                    self.last_sky_powerup_spawn = now

            if not self.boss_instance:
                if len(self.monsters) < 4 and not self.treasure_spawned and self.level % BOSS_FREQUENCY != 0:
                    self.treasure_spawned = True
                    if random.random() < 0.5:
                        side = random.choice([0, SCREEN_WIDTH - 30])
                        vel = BASE_ENEMY_SPEED_X * 2.5
                        if side > SCREEN_WIDTH // 2:
                            vel *= -1
                        m = Enemy(side, 130, 0, abs(vel), 0, 1.0, self.level, ENEMY_TESORO)
                        m.vel_x = vel
                        m.direction = 1
                        self.all_sprites.add(m)
                        self.monsters.add(m)

            if self.boss_instance:
                self.boss_instance.update(ahora=now, grupo_s=self.all_sprites,
                                         grupo_b=self.enemy_projectiles, mago=self.mage)
            else:
                edge = False
                for m in self.monsters:
                    m.try_shoot(self.level, self.all_sprites, self.enemy_projectiles)
                    if m.type != ENEMY_TREASURE:
                        if (m.rect.right >= SCREEN_WIDTH and m.direction == 1) or \
                           (m.rect.left <= 0 and m.direction == -1):
                            edge = True
                if edge:
                    for m in self.monsters:
                        m.rect.y += m.descent

            self.all_sprites.update(mago=self.mage, monstruos=self.monsters,
                                   grupo_s=self.all_sprites, grupo_b=self.enemy_projectiles)
            self.handle_collisions()

            if not self.monsters and not self.boss_instance and self.state == STATE_PLAYING:
                for orb in self.xp_orbs:
                    if self.mage.gain_xp(orb.valor):
                        self.change_state(STATE_UPGRADE_SELECT)
                        if self.snd_level and not self.muted:
                            self.snd_level.play()
                        break
                else:
                    self.level += 1
                    self.change_state(STATE_TRANSITION)
                    if self.snd_level and not self.muted:
                        self.snd_level.play()

            for m in self.monsters:
                if m.rect.bottom >= self.mage.rect.top:
                    self.change_state(STATE_GAMEOVER)

        elif self.state == STATE_TRANSITION:
            if pygame.time.get_ticks() - self.state_start_time > 2000:
                self._create_wave()
                self.change_state(STATE_PLAYING)

        if self.delete_confirmation and pygame.time.get_ticks() - self.delete_confirmation_timer > 3000:
            self.delete_confirmation = False

    def _handle_environment(self):
        now = pygame.time.get_ticks()
        if random.random() < 0.02:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            p = AmbientParticle(x, y, "firefly")
            self.ambient_particles.add(p)
            self.all_sprites.add(p)
        if random.random() < 0.01:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(50, SCREEN_HEIGHT - 100)
            p = AmbientParticle(x, y, "mota")
            self.ambient_particles.add(p)
            self.all_sprites.add(p)

        for layer in self.fog_layers:
            layer['x'] += layer['speed']
            if layer['x'] > SCREEN_WIDTH + 300:
                layer['x'] = -layer['width']

        for p in list(self.ambient_particles):
            if not p.alive():
                self.ambient_particles.remove(p)

    async def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.mage.touch_direction = 0
            await asyncio.sleep(0)

            now = pygame.time.get_ticks()
            if self.state == STATE_PLAYING:
                self.time_without_powerup += self.clock.get_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.FINGERDOWN:
                    tx, ty = event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT
                    self.active_touches[event.finger_id] = (tx, ty)
                    if self.btn_mute.collidepoint(tx, ty):
                        self.toggle_mute()

                    if self.state == STATE_MENU:
                        if self.btn_toggle_touch.collidepoint(tx, ty):
                            self.touch_controls_enabled = not self.touch_controls_enabled
                        if self.btn_shop.collidepoint(tx, ty):
                            self.change_state(STATE_SHOP)
                        if self.btn_play.collidepoint(tx, ty):
                            self.go_to_character_select(self.difficulty)
                        if self.btn_diff_normal.collidepoint(tx, ty):
                            self.difficulty = MODE_NORMAL
                        if self.btn_diff_hard.collidepoint(tx, ty):
                            self.difficulty = MODE_HARD
                        if self.btn_delete.collidepoint(tx, ty):
                            if self.delete_confirmation:
                                self.data_manager.reset()
                                self.delete_confirmation = False
                            else:
                                self.delete_confirmation = True
                                self.delete_confirmation_timer = now

                    elif self.state == STATE_CHARACTER_SELECT:
                        chars = list(CHARACTER_CONFIGS.keys())
                        for i, char_key in enumerate(chars):
                            if self.char_rects[i].collidepoint(tx, ty):
                                unlocked = (self.data_manager.data.get("unlocked_loco", False) or
                                           (DEBUG_MODE and DEBUG_ALL_UNLOCKED)) if char_key == "el_loco" else (
                                           self.data_manager.data.get("unlocked_snake", False) or
                                           (DEBUG_MODE and DEBUG_ALL_UNLOCKED)) if char_key == "snake" else True
                                if unlocked:
                                    self.start_game(char_key)

                    elif self.state == STATE_UPGRADE_SELECT:
                        for i in range(len(self.current_upgrade_options)):
                            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(tx, ty):
                                self.apply_upgrade(i + 1)
                                break

                    elif self.state == STATE_BOSS_REWARD:
                        selected = False
                        for i in range(len(self.boss_options)):
                            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(tx, ty):
                                self.apply_boss_reward(i)
                                self.data_manager.save()
                                selected = True
                                break
                        if selected:
                            self.change_state(STATE_TRANSITION)

                    elif self.state == STATE_SHOP:
                        if self.btn_shop.collidepoint(tx, ty):
                            self.change_state(STATE_MENU)
                        elif pygame.Rect(SCREEN_WIDTH // 2 - 250, 120, 160, 180).collidepoint(tx, ty):
                            self.data_manager.buy_upgrade("base_lives")
                        elif pygame.Rect(SCREEN_WIDTH // 2 - 80, 120, 160, 180).collidepoint(tx, ty):
                            self.data_manager.buy_upgrade("base_damage")
                        elif pygame.Rect(SCREEN_WIDTH // 2 + 90, 120, 160, 180).collidepoint(tx, ty):
                            self.data_manager.buy_upgrade("crit_chance")

                    elif self.state == STATE_VICTORY:
                        if not hasattr(self, 'victory_clicks'):
                            self.victory_clicks = 0
                        self.victory_clicks += 1
                        if self.victory_clicks >= 3:
                            self.victory_clicks = 0
                            self.change_state(STATE_MENU)

                    elif self.state == STATE_TRANSITION:
                        self._create_wave()
                        self.change_state(STATE_PLAYING)

                if event.type == pygame.FINGERUP and event.finger_id in self.active_touches:
                    if self.state == STATE_PLAYING and self.mage.type == "snake" and self.mage.charging:
                        self.mage.release_charge(self.player_projectiles)
                    del self.active_touches[event.finger_id]

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_pos = event.pos
                    self.active_touches['mouse'] = m_pos
                    if self.btn_mute.collidepoint(m_pos):
                        self.toggle_mute()

                    if self.state == STATE_MENU:
                        if self.btn_toggle_touch.collidepoint(m_pos):
                            self.touch_controls_enabled = not self.touch_controls_enabled
                        elif self.btn_shop.collidepoint(m_pos):
                            self.change_state(STATE_SHOP)
                        elif self.btn_play.collidepoint(m_pos):
                            self.go_to_character_select(self.difficulty)
                        elif self.btn_diff_normal.collidepoint(m_pos):
                            self.difficulty = MODE_NORMAL
                        elif self.btn_diff_hard.collidepoint(m_pos):
                            self.difficulty = MODE_HARD
                        elif self.btn_delete.collidepoint(m_pos):
                            if self.delete_confirmation:
                                self.data_manager.reset()
                                self.delete_confirmation = False
                            else:
                                self.delete_confirmation = True
                                self.delete_confirmation_timer = now

                    elif self.state == STATE_CHARACTER_SELECT:
                        chars = list(CHARACTER_CONFIGS.keys())
                        for i, char_key in enumerate(chars):
                            if self.char_rects[i].collidepoint(m_pos):
                                unlocked = (self.data_manager.data.get("unlocked_loco", False) or
                                           (DEBUG_MODE and DEBUG_ALL_UNLOCKED)) if char_key == "el_loco" else (
                                           self.data_manager.data.get("unlocked_snake", False) or
                                           (DEBUG_MODE and DEBUG_ALL_UNLOCKED)) if char_key == "snake" else True
                                if unlocked:
                                    self.start_game(char_key)

                    elif self.state == STATE_GAMEOVER and now - self.state_start_time > 2000:
                        self.change_state(STATE_MENU)

                    elif self.state == STATE_VICTORY:
                        if not hasattr(self, 'victory_clicks'):
                            self.victory_clicks = 0
                        self.victory_clicks += 1
                        if self.victory_clicks >= 3:
                            self.victory_clicks = 0
                            self.change_state(STATE_MENU)

                    elif self.state == STATE_TRANSITION:
                        self._create_wave()
                        self.change_state(STATE_PLAYING)

                    elif self.state == STATE_BOSS_REWARD:
                        selected = False
                        for i in range(len(self.boss_options)):
                            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(m_pos):
                                self.apply_boss_reward(i)
                                self.data_manager.save()
                                selected = True
                                break
                        if selected:
                            self.change_state(STATE_TRANSITION)

                    elif self.state == STATE_UPGRADE_SELECT:
                        for i in range(len(self.current_upgrade_options)):
                            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(m_pos):
                                self.apply_upgrade(i + 1)
                                break

                    elif self.state == STATE_SHOP:
                        if self.btn_shop.collidepoint(m_pos):
                            self.change_state(STATE_MENU)
                        elif pygame.Rect(SCREEN_WIDTH // 2 - 250, 120, 160, 180).collidepoint(m_pos):
                            self.data_manager.buy_upgrade("base_lives")
                        elif pygame.Rect(SCREEN_WIDTH // 2 - 80, 120, 160, 180).collidepoint(m_pos):
                            self.data_manager.buy_upgrade("base_damage")
                        elif pygame.Rect(SCREEN_WIDTH // 2 + 90, 120, 160, 180).collidepoint(m_pos):
                            self.data_manager.buy_upgrade("crit_chance")

                    elif self.state == STATE_PAUSE:
                        pass

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.state == STATE_PLAYING and self.mage.type == "snake" and self.mage.charging:
                        self.mage.release_charge(self.player_projectiles)
                    if 'mouse' in self.active_touches:
                        del self.active_touches['mouse']

                if event.type == pygame.KEYUP:
                    if self.state == STATE_PLAYING and self.mage.type == "snake" and event.key == pygame.K_SPACE:
                        self.mage.release_charge(self.player_projectiles)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        if self.state in (STATE_PAUSE, STATE_GAMEOVER):
                            self.change_state(STATE_MENU)
                        else:
                            self.toggle_mute()
                    if event.key == pygame.K_LSHIFT:
                        self.mage.dash()

                    if self.state == STATE_MENU:
                        if event.key == pygame.K_1:
                            self.difficulty = MODE_NORMAL
                            self.go_to_character_select(MODE_NORMAL)
                        if event.key == pygame.K_2:
                            self.difficulty = MODE_HARD
                            self.go_to_character_select(MODE_HARD)

                    elif self.state == STATE_CHARACTER_SELECT:
                        if event.key == pygame.K_1:
                            self.start_game("MAGO")
                        if event.key == pygame.K_2:
                            self.start_game("piromante")
                        if event.key == pygame.K_3:
                            self.start_game("cazador")
                        if event.key == pygame.K_4:
                            if self.data_manager.data.get("unlocked_loco", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED):
                                self.start_game("el_loco")

                    elif self.state == STATE_PLAYING:
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            self.change_state(STATE_PAUSE)
                        if event.key == pygame.K_F12:
                            self.change_state(STATE_DEBUG_MENU)

                        if DEBUG_MODE:
                            if event.key == pygame.K_F1:
                                self.level = max(1, self.level - 1)
                                self._create_wave()
                            if event.key == pygame.K_F2:
                                self.level = min(10, self.level + 1)
                                self._create_wave()
                            if event.key == pygame.K_F3:
                                self.mage.invulnerable = not self.mage.invulnerable
                            if event.key == pygame.K_F4:
                                for m in list(self.monsters):
                                    m.hp = 0
                                    m.kill()
                                if self.boss_instance:
                                    self.boss_instance.hp = 0

            self.reset_touch_movement()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    asyncio.run(Game().run())
