"""
Mago Defence - Player Module
Player character class and related functionality.
"""
import pygame
import math
import random
import settings

from src.constants import *


class Mage(pygame.sprite.Sprite):
    """Player character."""
    def __init__(self, all_sprites, player_projectiles, snd_shoot=None,
                 character_type="MAGO", meta_upgrades=None):

        super().__init__()
        self.group_s = all_sprites
        self.group_b = player_projectiles
        self.snd_shoot = snd_shoot
        self.type = character_type

        config = CHARACTER_CONFIGS.get(character_type, CHARACTER_CONFIGS["MAGO"])

        if meta_upgrades is None:
            meta_upgrades = {"base_lives": 0, "base_damage": 0, "crit_chance": 0, "ice_mastery": 0}
        self.ice_level = meta_upgrades.get("ice_mastery", 0)

        self.stats = {
            "damage_multiplier": config["damage_multiplier"] +
                                (meta_upgrades.get("base_damage", 0) * config["damage_scaling"]),
            "attack_speed_multi": BASE_ATTACK_COOLDOWN / config["cooldown_ms"],
            "projectile_speed": config["projectile_speed"],
            "extra_projectiles": config["extra_projectiles"],
            "bounces": 0,
            "penetration": 0,
            "crit_chance": config["crit_chance"] + meta_upgrades.get("crit_chance", 0) * 0.05,
            "crit_damage": config["crit_damage"],
            "move_speed": config["move_speed"]
        }

        self.modifiers = {
            "explosivo": "explosivo" in config["initial_modifiers"],
            "arco": "arco" in config["initial_modifiers"],
            "fragmentacion": False,
            "homing": False,
            "big_projectile": False
        }

        self.upgrade_counter = {
            "lives": 0, "damage": 0, "attack_speed": 0, "multishot": 0,
            "bounce": 0, "pierce": 0, "ice_perma": 0, "big_projectile": 0,
            "homing_perma": 0
        }

        self._load_assets(config["color"])
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))

        self.max_lives = config["max_lives"] + meta_upgrades.get("base_lives", 0)
        self.lives = self.max_lives

        self.xp = 0
        self.xp_required = XP_BASE_REQUIRED
        self.run_level = 1
        self.current_wave = 1
        self.last_shot = self.powerup_end = self.charges = self.double_damage_end = 0
        self.current_powerup = "normal"
        self.double_damage_active = self.is_shooting = self.shield_active = False
        self.invulnerable = False
        self.shot_animation_end = self.invulnerable_end = 0
        self.shield_radius = 140
        self.orbital_group = pygame.sprite.Group()
        self.orbital_active = False
        self.orbital_end = 0

        self.special_shield = None
        self.special_shield_unlocked = False

        self.dashing = False
        self.dash_end = 0
        self.dash_cooldown = 0
        self.dash_direction = 0
        self.dash_speed = config["dash_speed"]
        self.dash_duration = config["dash_duration_ms"]
        self.dash_cooldown_time = config["dash_cooldown_ms"]

        self.shield_pending = False
        self.slow_end = 0
        self.sliding = False
        self.momentum_x = 0

        self.skill_shield = False
        self.shield_hp = 0
        self.shield_regen_timer = 0
        self.shield_regen_cooldown = SHIELD_REGEN_COOLDOWN
        self.shield_max_hp = 1

        self.burn_skill = config["special_ability"] == "explosion_burn"
        self.burn_explosion_damage = config.get("explosion_damage", 0.70) if self.burn_skill else 0
        self.burn_explosion_radius = config.get("explosion_radius", 70) if self.burn_skill else 0

        self.pierce_skill = False
        self.shots_fired = 0
        self.pierce_freq = 4
        self.pierce_count = 3

        self.cancel_skill_prob = 0.0

        self.fury_ignea = False
        self.shadow_shooter = False

        self.charge = 0
        self.max_charge = config.get("charge_time_ms", 1000)
        self.charging = False
        self.max_charge_damage = config.get("max_charge_damage", 0.15)
        self.charge_speed_multi = config.get("charge_speed_multi", 1.0)
        self.charge_velocity = config.get("charge_velocity", config.get("move_speed", 6.5))

        self.move_left = False
        self.move_right = False
        self.shooting_touch = False
        self.touch_direction = 0

        if DEBUG_MODE:
            self._apply_debug_boosts()

    def _apply_debug_boosts(self):
        if DEBUG_MAX_STATS:
            self.stats["damage_multiplier"] = 10.0
            self.stats["attack_speed_multi"] = 5.0
            self.stats["projectile_speed"] = 15.0
            self.stats["extra_projectiles"] = 5
            self.stats["bounces"] = 5
            self.stats["penetration"] = 5
            self.stats["crit_chance"] = 1.0
            self.stats["crit_damage"] = 5.0
            self.stats["move_speed"] = 12.0
            self.ice_level = 20
        if DEBUG_GOD_MODE:
            self.max_lives = 999
            self.lives = 999
            self.invulnerable = True
        if DEBUG_ALL_POWERUPS:
            self.modifiers["explosivo"] = True
            self.modifiers["arco"] = True
            self.modifiers["fragmentacion"] = True
            self.skill_shield = True
            self.shield_hp = 999
            self.shield_max_hp = 999
            self.burn_skill = True
            self.pierce_skill = True
            self.cancel_skill_prob = 1.0

    def _load_assets(self, color):
        char_data = CHARACTER_CONFIGS.get(self.type, CHARACTER_CONFIGS["MAGO"])
        try:
            normal_img = pygame.transform.scale(
                pygame.image.load(resolve_path(char_data["sprite"])).convert_alpha(),
                (PLAYER_WIDTH, PLAYER_HEIGHT)
            )
            shoot_img = pygame.transform.scale(
                pygame.image.load(resolve_path(char_data["sprite_shoot"])).convert_alpha(),
                (PLAYER_WIDTH, PLAYER_HEIGHT)
            )
        except:
            normal_img = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(normal_img, color, [(12, 0), (0, 24), (24, 24)])
            pygame.draw.circle(normal_img, WHITE, (8, 12), 3)
            pygame.draw.circle(normal_img, WHITE, (16, 12), 3)
            shoot_img = normal_img.copy()
            pygame.draw.rect(shoot_img, CYAN_MAGIC, [0, 0, 24, 24], 2)
        self.normal_image = normal_img
        self.shoot_image = shoot_img
        self.image = normal_img

    def dash(self):
        now = pygame.time.get_ticks()
        if now > self.dash_cooldown and self.dash_direction != 0:
            self.dashing = self.dash_end = self.dash_cooldown = True, now + self.dash_duration, now + self.dash_cooldown_time
            self.invulnerable = True
            self.invulnerable_end = now + self.dash_duration + 100

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_required:
            self.xp -= self.xp_required
            self.run_level += 1
            self.xp_required = int(self.xp_required * XP_SCALING_FACTOR)
            return True
        return False

    def apply_powerup(self, ptype):
        now = pygame.time.get_ticks()
        stats = POWERUP_STATS.get(ptype, {})
        if ptype == "escudo":
            self.shield_pending = True
            return
        if ptype == "orbital":
            self.orbital_active = True
            self.orbital_end = now + stats.get("duration", 15000)
            self.orbital_group.empty()
            for i in range(3):
                self.orbital_group.add(Orbital(self.rect.centerx, self.rect.centery, 80, 4 + i))
            return
        if ptype == "doble_danio":
            self.double_damage_active = True
            self.double_damage_end = now + stats.get("duration", 9000)
            return
        self.current_powerup = ptype
        if "duration" in stats:
            self.powerup_end = now + stats["duration"]
            self.charges = 0
        elif "charges" in stats:
            self.charges = stats["charges"]
            self.powerup_end = 0

    def activate_shield(self):
        self.shield_pending = False
        self.shield_active = True
        self.shield_end = pygame.time.get_ticks() + 8000

    def can_shoot(self):
        now = pygame.time.get_ticks()
        cooldown = (BASE_ATTACK_COOLDOWN * (ATTACK_SPEED_SCALING ** self.current_wave) *
                   self.stats["attack_speed_multi"])
        if self.current_powerup == "cadencia":
            cooldown *= 0.4
        elif self.current_powerup == "disparo_doble":
            cooldown *= 1.25
        elif self.current_powerup == "disparo_triple":
            cooldown *= 1.67
        cooldown = min(cooldown, 2500)
        return now - self.last_shot > cooldown

    def shoot(self, monsters):
        if self.type == "snake":
            self.charge_shot()
            return

        now = pygame.time.get_ticks()
        if not self.can_shoot():
            return

        self.last_shot = now
        self.is_shooting = True
        self.shot_animation_end = now + 150
        if self.snd_shoot:
            self.snd_shoot.play()

        critical = random.random() < self.stats["crit_chance"]
        crit_multi = self.stats["crit_damage"] if critical else 1
        damage = BASE_PLAYER_DAMAGE * self.stats["damage_multiplier"] * (
            2 if self.double_damage_active else 1) * crit_multi

        if self.current_powerup == "rayo" and self.charges > 0:
            ray = Ray(self.rect.centerx, self.rect.top)
            self.group_s.add(ray)
            self.group_b.add(ray)
            self.charges -= 1
            return

        explosive = self.modifiers["explosivo"] or (
            self.current_powerup == "explosivo" and self.charges > 0)
        fragmentation = self.modifiers["fragmentacion"]

        if self.current_powerup == "explosivo" and not DEBUG_INFINITE_CHARGES:
            self.charges -= 1

        target = None
        if self.current_powerup == "homing" and self.charges > 0:
            if not DEBUG_INFINITE_CHARGES:
                self.charges -= 1
            min_dist = 9999
            for m in monsters:
                d = math.hypot(m.rect.centerx - self.rect.centerx,
                              m.rect.centery - self.rect.centery)
                if d < min_dist and m.rect.y < self.rect.y:
                    min_dist = d
                    target = m

        ice = random.random() < (self.ice_level * 0.05)
        homing = self.current_powerup == "homing" and (
            self.charges > 0 or (DEBUG_MODE and DEBUG_INFINITE_CHARGES))

        num = 1 + self.stats["extra_projectiles"]
        if self.current_powerup == "disparo_doble" and (self.charges > 0 or DEBUG_INFINITE_CHARGES):
            num += 1
        if self.current_powerup == "disparo_triple" and (self.charges > 0 or DEBUG_INFINITE_CHARGES):
            num += 1

        if self.current_powerup == "disparo_doble":
            if not DEBUG_INFINITE_CHARGES:
                self.charges -= 1
        elif self.current_powerup == "disparo_triple":
            if not DEBUG_INFINITE_CHARGES:
                self.charges -= 1

        burn = self.burn_skill
        if self.fury_ignea and random.random() < 0.30:
            burn = True

        penetration = 0
        if self.shadow_shooter and random.random() < 0.20:
            penetration = 999
        elif self.pierce_skill:
            self.shots_fired += 1
            if self.shots_fired % self.pierce_freq == 0:
                penetration = self.pierce_count

        start_angle = -90 - (5 * (num - 1))
        vel_p = self.stats["projectile_speed"]
        for i in range(num):
            rad = math.radians(start_angle + (10 * i))
            self._create_bullet(math.cos(rad) * vel_p, math.sin(rad) * vel_p,
                               damage, explosive, target, ice, fragmentation,
                               burn=burn, penetration=penetration,
                               homing=homing, critical=critical)

        if self.modifiers["arco"] or (self.current_powerup == "arco" and
                                       (self.charges > 0 or DEBUG_INFINITE_CHARGES)):
            arc_vx = vel_p * 0.38
            arc_vy = -vel_p * 0.88
            self._create_bullet(-arc_vx, arc_vy, damage, explosive, target,
                               ice, fragmentation, burn=burn,
                               penetration=penetration, homing=homing,
                               critical=critical)
            self._create_bullet(arc_vx, arc_vy, damage, explosive, target,
                               ice, fragmentation, burn=burn,
                               penetration=penetration, homing=homing,
                               critical=critical)
            if self.current_powerup == "arco" and not DEBUG_INFINITE_CHARGES:
                self.charges -= 1

        if self.charges <= 0 and not DEBUG_INFINITE_CHARGES:
            if self.current_powerup in ["arco", "disparo_doble", "disparo_triple",
                                        "explosivo", "rayo", "homing"]:
                self.current_powerup = "normal"

    def _create_bullet(self, vx, vy, damage, explosive, target, ice, fragmentation,
                      burn=False, penetration=0, homing=False, critical=False):
        color = ORANGE_FIRE if explosive else (
            (100, 255, 100) if self.stats["bounces"] > 0 else CYAN_MAGIC)
        total_penetration = self.stats["penetration"] + penetration
        fury = self.fury_ignea
        shadow = self.shadow_shooter

        homing_perma = False
        if self.modifiers.get("homing", False):
            prob = 0.4 + (self.upgrade_counter.get("homing_perma", 0) * 0.05)
            if random.random() < prob:
                homing_perma = True

        bullet = Projectile(
            self.rect.centerx, self.rect.top, vx, vy, damage,
            color=color, explosive=explosive,
            empowered=self.double_damage_active,
            bounces=self.stats["bounces"],
            penetration=total_penetration,
            target=target,
            ice=ice,
            fragmentation=fragmentation,
            burn=burn,
            homing=homing or homing_perma,
            fury_ignea=fury,
            shadow_shooter=shadow,
            critical=critical,
            big_projectile=self.modifiers.get("big_projectile", False)
        )
        self.group_s.add(bullet)
        self.group_b.add(bullet)

    def charge_shot(self):
        now = pygame.time.get_ticks()
        cooldown = (BASE_ATTACK_COOLDOWN * (ATTACK_SPEED_SCALING ** self.current_wave) *
                   self.stats["attack_speed_multi"])
        cooldown = min(cooldown, 2500)

        if now - self.last_shot > cooldown:
            self.last_shot = now
            self.charging = True
            self.charge = 0
            self.max_charge = CHARACTER_CONFIGS["snake"]["charge_time_ms"]
        else:
            if self.charging:
                self.charging = False
                self.charge = 0

        if self.charging:
            self.charge += self.charge_velocity
            if self.charge >= self.max_charge:
                self.charge = self.max_charge

    def release_charge(self, player_projectiles):
        if self.charging and self.charge >= self.max_charge:
            damage = (self.max_charge_damage * self.charge_speed_multi *
                     self.stats["damage_multiplier"] *
                     (2 if self.double_damage_active else 1))
            num_bullets = 1 + self.stats["extra_projectiles"]
            for i in range(num_bullets):
                spread = (num_bullets - 1) * 3
                angle = -90 + (i * 6) - spread / 2
                rad = math.radians(angle)
                vel_p = self.stats["projectile_speed"] * 1.5
                bullet = Projectile(
                    self.rect.centerx, self.rect.top,
                    math.cos(rad) * vel_p, math.sin(rad) * vel_p,
                    damage, color=(255, 0, 150)
                )
                self.group_s.add(bullet)
                player_projectiles.add(bullet)
            self.charge = 0
            self.charging = False

    def take_damage(self):
        if self.invulnerable or self.shield_active or self.dashing:
            if self.skill_shield and self.shield_hp > 0:
                self.shield_hp -= 1
                self.shield_regen_timer = pygame.time.get_ticks() + self.shield_regen_cooldown
                self.invulnerable = True
                self.invulnerable_end = pygame.time.get_ticks() + 1000
                return False
            return False

        self.lives -= 1
        self.invulnerable = True
        self.invulnerable_end = pygame.time.get_ticks() + 2000
        return True

    def update(self, *args, **kwargs):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        dash_from_key = -1 if keys[pygame.K_LEFT] else (1 if keys[pygame.K_RIGHT] else 0)
        self.dash_direction = dash_from_key

        if self.move_left:
            self.dash_direction = -1
        elif self.move_right:
            self.dash_direction = 1

        speed_factor = 1.0
        if self.slow_end > 0:
            speed_factor = SLOW_FACTOR

        speed = self.stats["move_speed"] * speed_factor

        if self.charging and self.type == "snake":
            speed = self.charge_velocity

        target_vx = 0
        if self.sliding:
            if self.dash_direction != 0:
                self.momentum_x += self.dash_direction * 0.2
            self.momentum_x *= 0.98
        else:
            if self.dashing:
                speed = self.dash_speed
            if self.dash_direction != 0:
                target_vx = self.dash_direction * speed
            self.momentum_x = target_vx

        if self.sliding:
            max_slide = speed * 1.5
            if self.momentum_x > max_slide:
                self.momentum_x = max_slide
            if self.momentum_x < -max_slide:
                self.momentum_x = -max_slide

        if self.momentum_x != 0:
            new_x = self.rect.x + self.momentum_x
            if 0 <= new_x <= SCREEN_WIDTH - self.rect.width:
                self.rect.x = int(new_x)
            else:
                self.momentum_x = 0

        if self.dashing and now > self.dash_end:
            self.dashing = False
        self.sliding = False

        if self.slow_end > 0 and now > self.slow_end:
            self.slow_end = 0

        if self.special_shield:
            self.special_shield.update()

        if self.skill_shield and self.shield_hp < self.shield_max_hp:
            if now > self.shield_regen_timer:
                self.shield_hp += 1
                if self.shield_hp < self.shield_max_hp:
                    self.shield_regen_timer = now + self.shield_regen_cooldown

        self.image = (self.shoot_image if self.is_shooting and
                     now < self.shot_animation_end else self.normal_image)
        if self.invulnerable and now > self.invulnerable_end:
            self.invulnerable = False
            self.image.set_alpha(255)
        elif self.invulnerable:
            self.image.set_alpha(100 if (now // 100) % 2 == 0 else 255)

        if self.powerup_end > 0 and now > self.powerup_end:
            self.current_powerup = "normal"
            self.powerup_end = 0
        if self.double_damage_active and now > self.double_damage_end:
            self.double_damage_active = False
        if self.shield_active and now > self.shield_end:
            self.shield_active = False

        if self.orbital_active:
            if now > self.orbital_end:
                self.orbital_active = False
                for o in self.orbital_group:
                    o.kill()
            else:
                self.orbital_group.update(self.rect.centerx, self.rect.centery)

    def apply_slow(self):
        self.slow_end = pygame.time.get_ticks() + SLOW_DURATION


# Export
__all__ = ['Mage']
