"""
Mago Defence - Sprites Module
All sprite classes for the game.
"""
import pygame
import math
import random
import os
import sys

# Import constants with alias for compatibility
from src.constants import *


class Particle(pygame.sprite.Sprite):
    """Visual particle effect."""
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(2, 6)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-6, 6)
        self.alpha = 255
        self.decay = random.randint(8, 15)

    def update(self, *args, **kwargs):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.vy += 0.2
        self.alpha -= self.decay
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)


class XPOrb(pygame.sprite.Sprite):
    """Experience orb dropped by enemies."""
    def __init__(self, x, y):
        super().__init__()
        self.value = XP_PER_ENEMY
        size = 8
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, XP_GREEN, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, WHITE, (size // 2, size // 2), size // 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = random.uniform(1.5, 3.0)
        self.vx = random.uniform(-1, 1)

    def update(self, *args, **kwargs):
        mage = kwargs.get('mage', None)
        if not mage and args and not isinstance(args[0], pygame.sprite.Group):
            mage = args[0]
        if mage:
            dx = mage.rect.centerx - self.rect.centerx
            dy = mage.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 160:
                self.vx += (dx / dist) * 0.9
                self.vy += (dy / dist) * 0.9
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class AmbientParticle(pygame.sprite.Sprite):
    """Background particle effect (fireflies, magic motes)."""
    def __init__(self, x, y, ptype="firefly"):
        super().__init__()
        size = random.randint(2, 4)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = FIREFLY_COLOR if ptype == "firefly" else MAGIC_MOTA
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, -1.5) if ptype == "firefly" else random.uniform(-1, 1)
        self.alpha = 0
        self.alpha_state = 1

    def update(self, *args, **kwargs):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.alpha_state == 1:
            self.alpha += 3
            if self.alpha >= 200:
                self.alpha_state = -1
        else:
            self.alpha -= 2
            if self.alpha <= 0:
                self.kill()
        self.image.set_alpha(self.alpha)
        if random.random() < 0.05:
            self.vx += random.uniform(-0.1, 0.1)


class Orbital(pygame.sprite.Sprite):
    """Orbital projectile that orbits around the player."""
    def __init__(self, center_x, center_y, orbit_radius, angular_velocity):
        super().__init__()
        self.radius = 8
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORBITAL_RED, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius // 2)
        self.rect = self.image.get_rect()
        self.center_x = center_x
        self.center_y = center_y
        self.orbit_radius = orbit_radius
        self.angle = 0
        self.angular_velocity = angular_velocity
        self.damage = 5

    def update(self, *args, **kwargs):
        center_new_x = kwargs.get('center_new_x', None)
        center_new_y = kwargs.get('center_new_y', None)
        if not center_new_x and len(args) >= 2:
            center_new_x, center_new_y = args[0], args[1]
        if center_new_x is not None:
            self.center_x, self.center_y = center_new_x, center_new_y
        self.angle += self.angular_velocity
        if self.angle >= 360:
            self.angle -= 360
        rad = math.radians(self.angle)
        self.rect.centerx = self.center_x + math.cos(rad) * self.orbit_radius
        self.rect.centery = self.center_y + math.sin(rad) * self.orbit_radius


class Projectile(pygame.sprite.Sprite):
    """Player and enemy projectile."""
    def __init__(self, x, y, vx, vy, damage, color=CYAN_MAGIC,
                 explosive=False, is_enemy=False, empowered=False,
                 bounces=0, penetration=0, custom_radius=None,
                 homing=False, target=None, ice=False,
                 fragmentation=False, burn=False, bomb=False,
                 fury_ignea=False, shadow_shooter=False,
                 critical=False, big_projectile=False):

        super().__init__()
        self.damage = damage
        self.explosive = explosive
        self.is_enemy = is_enemy
        self.bounces = bounces
        self.penetration = penetration
        self.homing = homing
        self.ice = ice
        self.fragmentation = fragmentation
        self.burn = burn
        self.target = target
        self.bomb = bomb
        self.fury_ignea = fury_ignea
        self.shadow_shooter = shadow_shooter
        self.original_color = color
        self.empowered = empowered
        self.critical = critical

        default_radius = 4 if is_enemy else (10 if explosive else 5)
        if big_projectile:
            default_radius = int(default_radius * 1.8)
        radius = custom_radius if custom_radius else default_radius

        if is_enemy:
            c = color if color != PURPLE_DARK else ENEMY_PROJECTILE_COLOR
            if radius > 20:
                c = PURPLE_CHARGED
            if color == BOSS_FIRE_COLOR:
                c = BOSS_FIRE_COLOR
            glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*ENEMY_GLOW, 100), (radius * 2, radius * 2), radius * 2)
            self.image = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            self.image.blit(glow_surf, (0, 0))
            pygame.draw.circle(self.image, c, (radius * 2, radius * 2), radius)
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.image = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
            c = GOLD_POWER if empowered else color
            if self.homing:
                c = HOMING_BLUE
            if self.ice:
                c = FROZEN_BLUE
            if self.fragmentation:
                c = ORANGE_FIRE
            if self.burn:
                c = RED_LIFE
            if self.penetration > 0:
                c = (255, 255, 200)
            pygame.draw.circle(self.image, c, (radius + 3, radius + 3), radius)
            if explosive or self.ice:
                pygame.draw.circle(self.image, WHITE, (radius + 3, radius + 3), radius // 3)
            if self.ice:
                pygame.draw.circle(self.image, (200, 240, 255), (radius + 3, radius + 3), radius, width=2)
            self.rect = self.image.get_rect(center=(x, y))

        self.vx = vy
        self.vy = vy
        self.total_speed = math.hypot(vx, vy)

    def update(self, *args, **kwargs):
        monsters = kwargs.get('monsters', None)
        if not monsters and args and isinstance(args[0], pygame.sprite.Group):
            monsters = args[0]

        if self.homing:
            if (not self.target or not self.target.alive()):
                if monsters:
                    self.target = self._find_target(monsters)
            if self.target and self.target.alive():
                dx = self.target.rect.centerx - self.rect.centerx
                dy = self.target.rect.centery - self.rect.centery
                target_angle = math.atan2(dy, dx)
                current_angle = math.atan2(self.vy, self.vx)
                diff = target_angle - current_angle
                while diff <= -math.pi:
                    diff += 2 * math.pi
                while diff > math.pi:
                    diff -= 2 * math.pi
                new_direction = current_angle + diff * 0.15
                self.vx = math.cos(new_direction) * self.total_speed
                self.vy = math.sin(new_direction) * self.total_speed

        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.bounces > 0 and (self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH):
            self.vx *= -1
            self.bounces -= 1

        if (self.rect.bottom < 0 or self.rect.top > SCREEN_WIDTH or
            (self.bounces <= 0 and (self.rect.left > SCREEN_WIDTH or self.rect.right < 0))):
            self.kill()

    def _find_target(self, monsters):
        target = None
        min_dist = 9999
        for m in monsters:
            if m.alive() and m.rect.centery < self.rect.centery:
                d = math.hypot(m.rect.centerx - self.rect.centerx,
                              m.rect.centery - self.rect.centery)
                if d < min_dist:
                    min_dist = d
                    target = m
        return target

    def bounce(self, monsters, ignore=None):
        new_target = None
        min_dist = 9999
        for m in monsters:
            if m.alive() and m != ignore:
                d = math.hypot(m.rect.centerx - self.rect.centerx,
                              m.rect.centery - self.rect.centery)
                if d < min_dist:
                    min_dist = d
                    new_target = m
        if new_target:
            dx = new_target.rect.centerx - self.rect.centerx
            dy = new_target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            self.vx = (dx / dist) * self.total_speed
            self.vy = (dy / dist) * self.total_speed
            return True
        return False

    def fragment(self, all_sprites, player_projectiles, damage_multi):
        for _ in range(6):
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            speed = 5
            frag = Projectile(
                self.rect.centerx, self.rect.centery,
                math.cos(rad) * speed, math.sin(rad) * speed,
                self.damage * 0.3,
                color=ORANGE_FIRE,
                es_fragmentacion=True
            )
            all_sprites.add(frag)
            player_projectiles.add(frag)


class Enemy(pygame.sprite.Sprite):
    """Enemy spaceship."""
    def __init__(self, x, y, row, vel_x, descent, mult_f, level=1, etype=ENEMY_NORMAL):
        super().__init__()
        self.row_original = row
        self.type = etype
        idx = min(row, 3)

        base_hp = HP_PER_ROW[idx]
        if etype == ENEMY_TANK:
            base_hp *= 3.0
        elif etype == ENEMY_ELITE:
            base_hp *= 4.5
        elif etype == ENEMY_FAST:
            base_hp *= 0.8
        self.hp = int(base_hp * (1 + (level * LIFE_MULTIPLIER)))

        self.color = ENEMY_COLORS.get(idx, WHITE)

        v_base = vel_x
        if etype == ENEMY_FAST:
            v_base *= 1.8

        self.vel_x = v_base
        self.descent = descent
        self.direction = 1
        self.frozen = False
        self.burned = False
        self.burn_timer = 0
        self.last_burn_damage = 0
        self.died_from_burn = False
        self.fury_ignea_active = False
        self.frames = []
        self.image_index = 0
        self.anim_timer = 0
        self.anim_delay = 500 if etype != ENEMY_FAST else 300

        self._load_assets(idx, etype)
        self.image = self.original_image.copy()

        border_color = None
        if self.type == ENEMY_TANK:
            border_color = ENEMY_BORDER_COLORS["tank"]
        elif self.type == ENEMY_ELITE:
            border_color = ENEMY_BORDER_COLORS["elite"]
        elif self.type == ENEMY_TREASURE:
            border_color = ENEMY_BORDER_COLORS["treasure"]
        if border_color:
            pygame.draw.rect(self.image, border_color, self.image.get_rect(), 2)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.unfreeze_timer = 0
        self.mult_f = mult_f
        self.remaining_bounces = 3 if self.type == ENEMY_TREASURE else 0

    def _load_assets(self, idx, etype):
        try:
            path_a = resolve_path(f"assets/monstruo_{idx}_A.png")
            path_b = resolve_path(f"assets/monstruo_{idx}_B.png")
            img_a = pygame.image.load(path_a).convert_alpha()
            img_b = pygame.image.load(path_b).convert_alpha()
            size = 28 if etype == ENEMY_ELITE else 22
            img_a = pygame.transform.scale(img_a, (size, size))
            img_b = pygame.transform.scale(img_b, (size, size))
            self.frames = [img_a, img_b]
            self.original_image = self.frames[0]
        except:
            size = 28 if etype == ENEMY_ELITE else 22
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(fallback, self.color, [0, 0, size, size], border_radius=4)
            offset = size // 4
            pygame.draw.circle(fallback, BLACK, (offset, offset), 4)
            pygame.draw.circle(fallback, BLACK, (offset, offset), 2)
            pygame.draw.circle(fallback, BLACK, (size - offset, offset), 4)
            pygame.draw.circle(fallback, BLACK, (size - offset, offset), 2)
            self.frames = [fallback, fallback]
            self.original_image = fallback

    def try_shoot(self, level, all_sprites, enemy_projectiles):
        if self.frozen:
            return
        chance_base = (BASE_SHOT_CHANCE + (level * SHOT_CHANCE_INCREMENT)) * self.mult_f
        multiplier = SHOT_CHANCE_MULTIPLIERS.get(self.type, 1.0)
        final_chance = chance_base * multiplier

        if random.random() < final_chance:
            vel_bala = 3.5
            if self.type == ENEMY_ELITE:
                vel_bala = 5.5
            elif self.type == ENEMY_TREASURE:
                vel_bala = 4.5
            p = Projectile(self.rect.centerx, self.rect.bottom, 0, vel_bala, 1, is_enemy=True)
            all_sprites.add(p)
            enemy_projectiles.add(p)

    def freeze(self):
        self.frozen = True
        self.unfreeze_timer = pygame.time.get_ticks() + FROZEN_DURATION_NORMAL
        t = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        t.fill((*FROZEN_BLUE, 150))
        self.image.blit(t, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def update(self, *args, **kwargs):
        now = pygame.time.get_ticks()
        if self.frozen:
            if now > self.unfreeze_timer:
                self.frozen = False
                self.image = self.original_image.copy()
            else:
                return

        self.pos_x += self.vel_x * self.direction
        self.rect.x = int(self.pos_x)

        if self.type == ENEMY_TREASURE:
            if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
                self.direction *= -1
                self.remaining_bounces -= 1
                if self.remaining_bounces <= 0:
                    self.kill()

        if now - self.anim_timer > self.anim_delay:
            self.anim_timer = now
            self.image_index = (self.image_index + 1) % len(self.frames)
            self.original_image = self.frames[self.image_index]
            self.image = self.original_image.copy()
            if self.burned:
                tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                tint.fill((255, 50, 0, 100))
                self.image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            border_color = None
            if self.type == ENEMY_TANK:
                border_color = ENEMY_BORDER_COLORS["tank"]
            elif self.type == ENEMY_ELITE:
                border_color = ENEMY_BORDER_COLORS["elite"]
            elif self.type == ENEMY_TREASURE:
                border_color = ENEMY_BORDER_COLORS["treasure"]
            if border_color:
                pygame.draw.rect(self.image, border_color, self.image.get_rect(), 2)

    def descend_all(direction_change):
        pass

    def propagate_burn(self, monsters):
        for m in monsters:
            if m != self and m.alive():
                d = math.hypot(m.rect.centerx - self.rect.centerx,
                              m.rect.centery - self.rect.centery)
                if d < 100:
                    m.burned = True
                    m.burn_timer = pygame.time.get_ticks()


class Barrier(pygame.sprite.Sprite):
    """Protective barrier that can be destroyed."""
    def __init__(self, x, y):
        super().__init__()
        self.max_hp = BARRIER_MAX_HP
        self.hp = self.max_hp
        self.width = BARRIER_WIDTH
        self.height = BARRIER_HEIGHT
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect(center=(x, y))
        self._update_image()

    def take_damage(self):
        self.hp -= 1
        self._update_image()
        if self.hp <= 0:
            self.kill()

    def _update_image(self):
        ratio = self.hp / self.max_hp
        if ratio > 0.6:
            color = BARRIER_FULL
        elif ratio > 0.3:
            color = BARRIER_MEDIUM
        else:
            color = BARRIER_LOW
        self.image.fill(color)
        pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 1)


class PowerUp(pygame.sprite.Sprite):
    """Collectible power-up item."""
    def __init__(self, x, y, ptype):
        super().__init__()
        self.type = ptype
        size = 20
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = POWERUP_COLORS.get(ptype, WHITE)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, WHITE, (size // 2, size // 2), size // 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = 1.5

    def update(self, *args, **kwargs):
        self.rect.y += self.vy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Heart(pygame.sprite.Sprite):
    """Health pickup."""
    def __init__(self, x, y, current_time):
        super().__init__()
        self.spawn_time = current_time
        size = 16
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, HEART_COLOR, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, WHITE, (size // 2 - 3, size // 2 - 3), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = 1.5

    def update(self, *args, **kwargs):
        self.rect.y += self.vy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Ray(pygame.sprite.Sprite):
    """Instant ray attack (Snake special)."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 0, 150), (4, 0, 6, SCREEN_HEIGHT))
        self.rect = self.image.get_rect(center=(x, y))
        self.creation = pygame.time.get_ticks()

    def update(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.creation > 150:
            self.kill()


class RayoPlayer(pygame.sprite.Sprite):
    """Charged ray attack (Snake)."""
    def __init__(self, x, y, angle=-90, duration=1000, color=(255, 0, 150),
                 mage=None, power=1.0, max_length=600, damage=None,
                 bounces=0, homing=False):
        super().__init__()
        self.origin_x = x
        self.origin_y = y
        self.angle = angle
        self.duration = duration
        self.creation = pygame.time.get_ticks()
        self.color = color
        self.power = power
        self.max_length = max_length
        self.mage = mage

        self.is_ray = True
        if damage is not None:
            self.damage = damage
        else:
            self.damage = (0.5 if mage else 150) * (0.3 + (0.7 * power))
        self.penetration = 999
        self.hit_enemies = []

        self.rebotes = bounces
        self.homing = homing

        self.ray_speed = 800
        self.full_expansion = False
        self.full_expansion_time = None

        self.image = pygame.Surface((100, max_length + 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.left = x - 50
        self.rect.top = y - max_length

    def update(self, *args, **kwargs):
        now = pygame.time.get_ticks()
        elapsed = now - self.creation

        if not self.full_expansion:
            self.current_length = min(elapsed * self.ray_speed / 1000, self.max_length)
            if self.current_length >= self.max_length:
                self.full_expansion = True
                self.full_expansion_time = now
        else:
            self.current_length = self.max_length

        if self.full_expansion:
            time_since_expansion = now - self.full_expansion_time
            if time_since_expansion > 200:
                fade_ratio = min((time_since_expansion - 200) / 300, 1.0)
                if fade_ratio >= 1.0:
                    self.kill()
                    return
            else:
                fade_ratio = 0.0
        else:
            fade_ratio = 0.0

        self.image.fill((0, 0, 0, 0))
        length = int(self.current_length)
        pygame.draw.rect(self.image, self.color, (48, 0, 4, length))

        glow_intensity = 255 - int(fade_ratio * 200)
        for i in range(3):
            glow_radius = 8 - i * 2
            alpha = glow_intensity // (i + 1)
            pygame.draw.circle(self.image, (*self.color[:3], alpha), (50, length - 10), glow_radius)


class LaserSNAKE(pygame.sprite.Sprite):
    """Boss Snake laser beam."""
    def __init__(self, x, y, angle, duration=500):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        self.duration = duration
        self.creation = pygame.time.get_ticks()
        self.length = 1000
        self.width = 15
        self.image = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self._update_position()

    def _update_position(self):
        rad = math.radians(self.angle)
        end_x = self.x + math.cos(rad) * self.length
        end_y = self.y + math.sin(rad) * self.length
        min_x = min(self.x, end_x)
        max_x = max(self.x, end_x)
        min_y = min(self.y, end_y)
        max_y = max(self.y, end_y)
        self.rect = pygame.Rect(min_x - self.width // 2, min_y - self.width // 2,
                                max_x - min_x + self.width, max_y - min_y + self.width)

    def update(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.creation > self.duration:
            self.kill()


class SpecialShield(pygame.sprite.Sprite):
    """Special shield for level 5 Mage ability."""
    def __init__(self, mage):
        super().__init__()
        self.mage = mage
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rebounced = False
        self.respawn_cooldown = 10000
        self.disappear_timer = 0
        self.respawn_timer = 0
        self.active = False
        self.shield_image = self._create_shield_image()
        self._update_position()

    def _create_shield_image(self):
        image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.arc(image, MAGE_BLUE, [5, 5, 30, 30], 0, math.pi, 3)
        pygame.draw.arc(image, CYAN_MAGIC, [10, 10, 20, 20], 0, math.pi, 2)
        return image

    def _update_position(self):
        self.rect.midbottom = (self.mage.rect.centerx, self.mage.rect.top - 10)

    def activate(self):
        self.active = True
        self.rebounced = False
        self.disappear_timer = 0
        self.image = self.shield_image

    def deactivate(self):
        self.active = False
        self.rebounced = True
        self.respawn_timer = pygame.time.get_ticks() + self.respawn_cooldown
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def update(self, *args, **kwargs):
        self._update_position()
        if not self.active:
            now = pygame.time.get_ticks()
            if now > self.respawn_timer:
                self.activate()


class CriticalHit(pygame.sprite.Sprite):
    """Visual feedback for critical hits."""
    def __init__(self, x, y):
        super().__init__()
        self.font = pygame.font.SysFont("Arial", 24, True)
        self.image = self.font.render("X", True, GOLD_POWER)
        self.rect = self.image.get_rect(center=(x, y))
        self.end = pygame.time.get_ticks() + 600

    def update(self, **kwargs):
        if pygame.time.get_ticks() > self.end:
            self.kill()


class RayImpact(pygame.sprite.Sprite):
    """Impact effect for ray attacks."""
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.creation = pygame.time.get_ticks()
        self.duration = 200
        self.radius = 5
        self.max_radius = 30
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, **kwargs):
        now = pygame.time.get_ticks()
        elapsed = now - self.creation
        if elapsed > self.duration:
            self.kill()
            return
        ratio = elapsed / self.duration
        self.radius = min(self.max_radius * ratio, self.max_radius)
        alpha = int(255 * (1 - ratio))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (255, 200, 255, alpha), (30, 30), int(self.radius))
        pygame.draw.circle(self.image, (255, 255, 255, alpha), (30, 30), int(self.radius * 0.5), 2)


class Puddle(pygame.sprite.Sprite):
    """Ground effect puddle (fire, ice, poison)."""
    def __init__(self, x, y, ptype):
        super().__init__()
        self.type = ptype
        width = 80 if ptype == "poison" else 60
        height = 15
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        color = BOSS_FIRE_COLOR if ptype == "fire" else (
            GREEN_VENOM if ptype == "poison" else WHITE_ICE)
        pygame.draw.ellipse(self.image, color, self.image.get_rect())
        self.rect = self.image.get_rect(center=(x, y))
        self.creation = pygame.time.get_ticks()

    def update(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.creation > Puddle_DURATION:
            self.kill()


class Boss(pygame.sprite.Sprite):
    """Boss enemy."""
    def __init__(self, level, difficulty, variant=BOSS_TYPE_NORMAL):
        super().__init__()
        self.level = level
        self.difficulty = difficulty
        self.variant = variant
        self.hp = int(BASE_BOSS_HP * (1 + (level // 5) * 0.5))
        if difficulty == MODE_HARD:
            self.hp = int(self.hp * 1.5)
        self.hp_max = self.hp
        self.creation = pygame.time.get_ticks()
        self.destruyendo = False
        self.frozen = False
        self.unfreeze_timer = 0

        size = 60
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        if variant == BOSS_TYPE_ICE:
            self.image.fill((*FROZEN_BLUE, 100))
        elif variant == BOSS_TYPE_FIRE:
            self.image.fill((*BOSS_FIRE_COLOR, 100))
        elif variant == BOSS_TYPE_TOXIC:
            self.image.fill((*GREEN_VENOM, 100))
        else:
            self.image.fill((100, 50, 100, 100))

        pygame.draw.circle(self.image, PURPLE_DARK, (size // 2, size // 2), size // 2 - 5)
        pygame.draw.circle(self.image, WHITE, (size // 2, size // 2), 8)

        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = 80
        self.vel_x = 2 if difficulty == MODE_NORMAL else 4
        self.vel_y = 1 if difficulty == MODE_NORMAL else 2
        self.direction_x = 1
        self.direction_y = 1
        self.attack_cooldown = 0
        self.last_vertical_move = 0

        self.cargas_arco = 0
        self.cargas_rafaga = 0

    def update(self, ahora=None, grupo_s=None, grupo_b=None, mago=None):
        if self.destruyendo:
            return
        if self.frozen:
            if ahora and ahora > self.unfreeze_timer:
                self.frozen = False
            return

        if self.vel_x != 0:
            self.rect.x += self.vel_x * self.direction_x
            if self.rect.right >= SCREEN_WIDTH - 20 or self.rect.left <= 20:
                self.direction_x *= -1

        if self.vel_y != 0:
            if ahora and ahora - self.last_vertical_move > 1500:
                self.last_vertical_move = ahora
                self.rect.y += self.vel_y * self.direction_y
                if self.rect.y <= LIMITE_INFERIOR_BOSS or self.rect.y >= 150:
                    self.direction_y *= -1

        if ahora and self.attack_cooldown < ahora:
            self._do_attack(grupo_s, grupo_b, mago)
            if self.variant == BOSS_TYPE_NORMAL:
                self.attack_cooldown = ahora + 2000
            else:
                self.attack_cooldown = ahora + random.randint(1500, 2500)

    def _do_attack(self, grupo_s, grupo_b, mago):
        attack_type = random.choice(["arco", "rafaga", "cargado"])
        if attack_type == "arco":
            for i in range(3):
                p = Projectile(self.rect.centerx, self.rect.bottom, 0, 4, 3, is_enemy=True)
                grupo_s.add(p)
                grupo_b.add(p)
        elif attack_type == "rafaga":
            for _ in range(5):
                ang = random.uniform(-80, -100)
                rad = math.radians(ang)
                vx = math.cos(rad) * random.uniform(3, 5)
                vy = math.sin(rad) * random.uniform(3, 5)
                p = Projectile(self.rect.centerx, self.rect.bottom, vx, vy, 2, is_enemy=True)
                grupo_s.add(p)
                grupo_b.add(p)
        elif attack_type == "cargado":
            p = Projectile(self.rect.centerx, self.rect.bottom, 0, 3, 8, is_enemy=True, radio_custom=25)
            grupo_s.add(p)
            grupo_b.add(p)

    def freeze(self):
        self.frozen = True
        self.unfreeze_timer = pygame.time.get_ticks() + FROZEN_DURATION_BOSS


class BossSNAKE(pygame.sprite.Sprite):
    """Final boss - Astral Snake."""
    def __init__(self, difficulty, level):
        super().__init__()
        self.level = level
        self.difficulty = difficulty
        self.hp = BOSS_SNAKE_HP
        if difficulty == MODE_HARD:
            self.hp = int(self.hp * 1.8)
        self.hp_max = self.hp
        self.creation = pygame.time.get_ticks()
        self.destruyendo = False
        self.frozen = False
        self.unfreeze_timer = 0

        self.rect = pygame.Rect(0, 0, 100, 100)
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = 100
        self.vel_x = 5 if difficulty == MODE_NORMAL else 8
        self.vel_y = 3 if difficulty == MODE_NORMAL else 5
        self.direction_x = 1
        self.direction_y = 1
        self.attack_cooldown = 0
        self.phase = "normal"
        self.embestiendo = False
        self.embestir_target_x = 0
        self.laser_cooldown = 0

        # Cola de disparos en cadena (efecto serpiente)
        self.burst_queue = []   # lista de (timestamp, vx, vy)
        self.burst_angle = 0    # ángulo fijo de la cadena actual

        self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (150, 0, 100), (50, 50), 45)
        pygame.draw.circle(self.image, (200, 50, 150), (50, 50), 30)
        pygame.draw.circle(self.image, WHITE, (50, 40), 10)
        pygame.draw.circle(self.image, (255, 0, 0), (50, 40), 5)

    def update(self, ahora=None, grupo_s=None, grupo_b=None, mago=None):
        if self.destruyendo:
            return
        if self.frozen:
            if ahora and ahora > self.unfreeze_timer:
                self.frozen = False
            return

        # --- Procesar cola de disparos en cadena ---
        if ahora and self.burst_queue and grupo_s and grupo_b:
            while self.burst_queue and ahora >= self.burst_queue[0][0]:
                _, vx, vy = self.burst_queue.pop(0)
                proj = Projectile(
                    self.rect.centerx, self.rect.centery,
                    vx, vy, 3,
                    is_enemy=True, custom_radius=5
                )
                grupo_s.add(proj)
                grupo_b.add(proj)

        if self.phase == "normal":
            self.rect.x += self.vel_x * self.direction_x
            if self.rect.right >= SCREEN_WIDTH - 50 or self.rect.left <= 50:
                self.direction_x *= -1
            if ahora and self.attack_cooldown < ahora:
                self._do_attack(grupo_s, grupo_b, mago, ahora)
                self.attack_cooldown = ahora + random.randint(2200, 3500)
        elif self.phase == "embestir":
            speed = 15
            dx = self.embestir_target_x - self.rect.centerx
            if abs(dx) < 20:
                self.phase = "normal"
                self.embestiendo = False
                self.attack_cooldown = ahora + 2000
            else:
                self.rect.x += (1 if dx > 0 else -1) * speed

    def _do_attack(self, grupo_s, grupo_b, mago, ahora):
        if random.random() < 0.4 and self.laser_cooldown < ahora:
            angle = random.uniform(-70, -110)
            laser = LaserSNAKE(self.rect.centerx, self.rect.centery, angle, 500)
            grupo_s.add(laser)
            self.laser_cooldown = ahora + 5000
        elif random.random() < 0.3 and mago:
            self.embestir_target_x = mago.rect.centerx
            self.phase = "embestir"
            self.embestiendo = True
        else:
            # Cadena de proyectiles pequeños en sucesión rápida (efecto serpiente)
            # Calcular dirección hacia el mago o aleatoria si no hay mago
            if mago:
                dx = mago.rect.centerx - self.rect.centerx
                dy = mago.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy) or 1
                base_ang = math.atan2(dy, dx)
            else:
                base_ang = math.radians(random.uniform(-60, -120))

            speed = 6 if self.difficulty == MODE_NORMAL else 7.5
            vx_base = math.cos(base_ang) * speed
            vy_base = math.sin(base_ang) * speed

            # Número de proyectiles: 4 normal / 5 difícil
            chain_len = 4 if self.difficulty == MODE_NORMAL else 5
            delay_ms = 120  # ms entre cada proyectil de la cadena

            for i in range(chain_len):
                fire_time = ahora + i * delay_ms
                self.burst_queue.append((fire_time, vx_base, vy_base))

    def freeze(self):
        self.frozen = True
        self.unfreeze_timer = pygame.time.get_ticks() + FROZEN_DURATION_BOSS


# Export all classes
__all__ = [
    'Particle', 'XPOrb', 'AmbientParticle', 'Orbital', 'Projectile',
    'Enemy', 'Barrier', 'PowerUp', 'Heart', 'Ray', 'RayoPlayer',
    'LaserSNAKE', 'SpecialShield', 'CriticalHit', 'RayImpact',
    'Puddle', 'Boss', 'BossSNAKE'
]
