
import pygame
import math
import random

from src.constants import *
from src.utils import draw_glow_circle, draw_glow_line, draw_glow_rect, angle_to, dist


# ─── BALLE ENNEMIE ───────────────────────────────────────────────────────────

class EnemyBullet:
    def __init__(self, x, y, vx, vy, color=C_RED, radius=5, damage=1, homing=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.active = True
        self.damage = damage
        self.homing = homing
        self.homing_strength = 0.08

    def update(self, player_x=None, player_y=None):
        if self.homing and player_x is not None:
            desired_vx = (player_x - self.x)
            desired_vy = (player_y - self.y)
            d = max(1, math.hypot(desired_vx, desired_vy))
            spd = math.hypot(self.vx, self.vy)
            self.vx += (desired_vx/d * spd - self.vx) * self.homing_strength
            self.vy += (desired_vy/d * spd - self.vy) * self.homing_strength

        self.x += self.vx
        self.y += self.vy
        if (self.x < -30 or self.x > SCREEN_W + 30
                or self.y < -30 or self.y > SCREEN_H + 30):
            self.active = False

    def draw(self, surf):
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=90, layers=2)


# ─── CLASSE DE BASE ENNEMI ───────────────────────────────────────────────────

class Enemy:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 16
        self.color = C_MAGENTA
        self.hp = 1
        self.max_hp = 1
        self.score_value = SCORE_BASIC
        self.active = True
        self.angle = float(random.randint(0, 359))
        self.shoot_timer = random.randint(40, 120)
        self.speed = 2.5
        self.chain_explodes = False   # Overridden by explosive enemy types
        self.chain_radius   = 0       # Blast radius for chain reaction

    def hit(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def _base_update(self):
        self.angle += 3

    def update(self):
        self._base_update()
        self.x -= self.speed
        if self.x < -60:
            self.active = False

    def get_bullets(self, px, py):
        return []

    def _shoot_towards(self, px, py, speed=None, homing=False, color=C_RED):
        spd = speed or ENEMY_BULLET_SPEED
        a = angle_to(self.x, self.y, px, py)
        return EnemyBullet(self.x, self.y,
                           math.cos(a)*spd, math.sin(a)*spd,
                           color=color, homing=homing)

    def _draw_core(self, surf):
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=80)
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            px = self.x + math.cos(a) * (self.radius * 0.55)
            py = self.y + math.sin(a) * (self.radius * 0.55)
            pygame.draw.circle(surf, C_WHITE, (int(px), int(py)), 2)

    def _draw_hp_bar(self, surf):
        if self.max_hp <= 1:
            return
        bw = self.radius * 2
        bx = self.x - self.radius
        by = self.y - self.radius - 10
        pygame.draw.rect(surf, (60, 0, 0), (bx, by, bw, 5), border_radius=2)
        fill = int(bw * max(0, self.hp) / self.max_hp)
        if fill > 0:
            pygame.draw.rect(surf, C_GREEN, (bx, by, fill, 5), border_radius=2)

    def draw(self, surf):
        self._draw_core(surf)
        self._draw_hp_bar(surf)


# ─── ZIGZAG ──────────────────────────────────────────────────────────────────

class ZigzagEnemy(Enemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y)
        self.speed = speed
        self.color = C_GREEN
        self.score_value = SCORE_ZIGZAG
        self.amp = random.uniform(60, 100)
        self.freq = random.uniform(0.04, 0.07)
        self.origin_y = float(y)
        self.t = random.uniform(0, math.pi * 2)
        self.radius = 13

    def update(self):
        self._base_update()
        self.t += self.freq
        self.x -= self.speed
        self.y = self.origin_y + math.sin(self.t) * self.amp
        self.y = max(self.radius, min(SCREEN_H - self.radius, self.y))
        if self.x < -60:
            self.active = False


# ─── TANK ────────────────────────────────────────────────────────────────────

class TankEnemy(Enemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y)
        self.speed = speed * 0.65
        self.color = C_ORANGE
        self.score_value = SCORE_TANK
        self.hp = 4
        self.max_hp = 4
        self.radius = 22
        self.shoot_cd = 90
        self.chain_explodes = True
        self.chain_radius   = 100

    def update(self):
        self._base_update()
        self.x -= self.speed
        if self.x < -70:
            self.active = False

    def get_bullets(self, px, py):
        self.shoot_cd -= 1
        if self.shoot_cd <= 0:
            self.shoot_cd = 90
            return [self._shoot_towards(px, py, color=C_ORANGE)]
        return []


# ─── GHOST ───────────────────────────────────────────────────────────────────

class GhostEnemy(Enemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y)
        self.speed = speed * 0.85
        self.color = C_PURPLE
        self.score_value = SCORE_GHOST
        self.radius = 15
        self.phase = random.uniform(0, math.pi * 2)
        self.shoot_cd = random.randint(60, 100)

    def update(self):
        self._base_update()
        self.x -= self.speed
        self.phase += 0.04
        if self.x < -60:
            self.active = False

    def get_bullets(self, px, py):
        self.shoot_cd -= 1
        if self.shoot_cd <= 0:
            self.shoot_cd = random.randint(60, 100)
            return [self._shoot_towards(px, py, homing=True, color=C_PURPLE)]
        return []

    def draw(self, surf):
        alpha = int(100 + 80 * math.sin(self.phase))
        s = pygame.Surface((self.radius*6, self.radius*6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.radius*3, self.radius*3), self.radius*2)
        pygame.draw.circle(s, (*C_WHITE, alpha), (self.radius*3, self.radius*3), self.radius)
        surf.blit(s, (int(self.x) - self.radius*3, int(self.y) - self.radius*3))
        self._draw_hp_bar(surf)


# ─── SPLITTER ────────────────────────────────────────────────────────────────

class SplitterEnemy(Enemy):
    """Se divise en 2 petits ennemis à la mort."""
    def __init__(self, x, y, speed, small=False):
        super().__init__(x, y)
        self.speed = speed
        self.small = small
        self.color = C_PINK
        self.score_value = SCORE_SPLITTER // (2 if small else 1)
        self.radius = 10 if small else 19
        self.hp = 1 if small else 2
        self.max_hp = self.hp

    def update(self):
        self._base_update()
        self.x -= self.speed
        if self.x < -60:
            self.active = False

    def spawn_children(self):
        if self.small:
            return []
        return [
            SplitterEnemy(self.x, self.y - 15, self.speed * 1.2, small=True),
            SplitterEnemy(self.x, self.y + 15, self.speed * 1.2, small=True),
        ]


# ─── SNIPER ──────────────────────────────────────────────────────────────────

class SniperEnemy(Enemy):
    """Reste à droite, vise et tire une balle rapide toutes les 2s."""
    def __init__(self, x, y, speed):
        super().__init__(x, y)
        self.speed = speed * 0.4
        self.color = C_TEAL
        self.score_value = SCORE_SNIPER
        self.radius = 14
        self.target_x = SCREEN_W - 100
        self.arrived = False
        self.aim_timer = 0
        self.aim_duration = 70
        self.shoot_cd = random.randint(90, 150)
        self.aim_x = None
        self.aim_y = None

    def update(self):
        self._base_update()
        if not self.arrived:
            if self.x > self.target_x:
                self.x -= self.speed * 3
            else:
                self.arrived = True
        # Orbite verticale légère
        if self.arrived:
            self.y += math.sin(pygame.time.get_ticks() * 0.002) * 0.8
        if self.x < -60:
            self.active = False

    def get_bullets(self, px, py):
        if not self.arrived:
            return []
        self.shoot_cd -= 1
        if self.shoot_cd <= 0:
            self.shoot_cd = random.randint(90, 150)
            self.aim_x = px
            self.aim_y = py
            return [self._shoot_towards(px, py, speed=9, color=C_TEAL)]
        return []

    def draw(self, surf):
        self._draw_core(surf)
        # Ligne de visée
        if self.arrived and self.aim_x is not None:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            alpha = int(40 + 30 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.line(s, (*C_TEAL, alpha),
                             (int(self.x), int(self.y)),
                             (int(self.aim_x), int(self.aim_y)), 1)
            surf.blit(s, (0, 0))
        self._draw_hp_bar(surf)


# ─── ALLY GHOST ──────────────────────────────────────────────────────────────

class AllyGhost:
    """
    A converted Ghost that fights alongside the player for 30 seconds.
    Spawned when a Ghost's homing purple bullet hits the player without
    dealing damage (shield blocked it, or player was invincible).

    Behaviour:
      - Orbits just behind the player
      - Finds the nearest enemy and fires purple homing bullets at it
      - Fades out and disappears after ALLY_DURATION frames
      - Drawn in cyan-tinted purple to distinguish it from enemies
    """
    ALLY_DURATION = 1800   # 30 s at 60 FPS
    ORBIT_RADIUS  = 55
    ORBIT_SPEED   = 0.035
    SHOOT_CD_MIN  = 40
    SHOOT_CD_MAX  = 70

    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.radius = 13
        self.active = True
        self.angle  = random.uniform(0, math.pi * 2)   # orbit angle
        self.spin   = random.uniform(0, math.pi * 2)   # visual spin
        self.shoot_cd = random.randint(self.SHOOT_CD_MIN, self.SHOOT_CD_MAX)
        self.phase    = random.uniform(0, math.pi * 2)  # glow phase

    # ── Update ───────────────────────────────────────────────────────────

    def update(self, player_x, player_y):
        # Smoothly orbit player
        self.angle += self.ORBIT_SPEED
        target_x = player_x - self.ORBIT_RADIUS * math.cos(self.angle)
        target_y = player_y + self.ORBIT_RADIUS * math.sin(self.angle) * 0.5
        self.x += (target_x - self.x) * 0.12
        self.y += (target_y - self.y) * 0.12

        self.spin  += 4.0
        self.phase += 0.06

        self.shoot_cd -= 1

    def get_bullets(self, enemies):
        """Return a homing ally bullet aimed at the Boss (or nearest enemy), if ready."""
        if self.shoot_cd > 0 or not enemies:
            return []
        self.shoot_cd = random.randint(self.SHOOT_CD_MIN, self.SHOOT_CD_MAX)

        # Prefer the Boss as target; fall back to nearest active enemy
        nearest    = None
        best_d     = float("inf")
        boss_target = None
        for e in enemies:
            if not e.active:
                continue
            if isinstance(e, Boss):
                boss_target = e
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < best_d:
                best_d  = d
                nearest = e

        nearest = boss_target if boss_target is not None else nearest

        if nearest is None:
            return []

        a   = math.atan2(nearest.y - self.y, nearest.x - self.x)
        spd = ENEMY_BULLET_SPEED * 1.1
        return [AllyBullet(self.x, self.y,
                           math.cos(a) * spd,
                           math.sin(a) * spd)]

    # ── Draw ─────────────────────────────────────────────────────────────

    def draw(self, surf):
        alpha_scale = 1.0

        glow_alpha = int((80 + 40 * math.sin(self.phase)) * alpha_scale)
        pulse_r    = self.radius + int(3 * math.sin(self.phase * 2))

        # Outer glow — teal-purple mix
        draw_glow_circle(surf, C_TEAL, (self.x, self.y), pulse_r + 6,
                         alpha=glow_alpha // 2, layers=2)
        # Body
        draw_glow_circle(surf, C_PURPLE, (self.x, self.y), pulse_r,
                         alpha=glow_alpha, layers=3)

        # Inner white dot
        s = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C_WHITE, int(180 * alpha_scale)),
                           (pulse_r * 2, pulse_r * 2), pulse_r - 4)
        surf.blit(s, (int(self.x) - pulse_r * 2, int(self.y) - pulse_r * 2))

        # Spinning orbit dots (cyan to distinguish from enemy ghosts)
        for i in range(3):
            a = math.radians(self.spin + i * 120)
            dx = math.cos(a) * (pulse_r + 5)
            dy = math.sin(a) * (pulse_r + 5)
            dot_s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot_s, (*C_CYAN, int(200 * alpha_scale)), (4, 4), 3)
            surf.blit(dot_s, (int(self.x + dx) - 4, int(self.y + dy) - 4))


# ─── ALLY BULLET ─────────────────────────────────────────────────────────────

class AllyBullet:
    """Homing bullet fired by an AllyGhost towards the nearest enemy."""
    def __init__(self, x, y, vx, vy):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = vx
        self.vy     = vy
        self.radius = 5
        self.active = True
        self.damage = 1
        self.homing_strength = 0.07

    def update(self, target_x=None, target_y=None):
        if target_x is not None:
            desired_vx = target_x - self.x
            desired_vy = target_y - self.y
            d   = max(1, math.hypot(desired_vx, desired_vy))
            spd = math.hypot(self.vx, self.vy)
            self.vx += (desired_vx / d * spd - self.vx) * self.homing_strength
            self.vy += (desired_vy / d * spd - self.vy) * self.homing_strength
        self.x += self.vx
        self.y += self.vy
        if (self.x < -30 or self.x > SCREEN_W + 30
                or self.y < -30 or self.y > SCREEN_H + 30):
            self.active = False

    def draw(self, surf):
        # Purple-cyan mix to look like a tamed ghost bullet
        draw_glow_circle(surf, C_PURPLE, (self.x, self.y), self.radius,
                         alpha=80, layers=2)
        s = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C_CYAN, 200),
                           (self.radius + 1, self.radius + 1), max(2, self.radius - 2))
        surf.blit(s, (int(self.x) - self.radius - 1, int(self.y) - self.radius - 1))


# ─── BOSS ─────────────────────────────────────────────────────────────────────

class BossPhase:
    IDLE    = "idle"
    CHARGE  = "charge"
    LASER   = "laser"
    SPREAD  = "spread"
    SUMMON  = "summon"


class Boss(Enemy):
    """Boss multi-phase avec 5 patterns d'attaque."""
    # HP per difficulty: FACILE=30, NORMAL=75, DIFFICILE scales higher
    MAX_HP_BASE = 75

    def __init__(self, wave, diff=1.0):
        super().__init__(SCREEN_W + 100, SCREEN_H // 2)
        self.wave = wave
        self.diff = diff
        self.radius = 46
        self.color = C_RED

        # Scale HP: FACILE=30 flat, NORMAL=75+wave*30, DIFFICILE=75+wave*30 scaled up
        if diff <= 0.7:
            self.hp = 30
        elif diff >= 1.5:
            self.hp = self.MAX_HP_BASE + wave * 50
        else:
            self.hp = self.MAX_HP_BASE + wave * 30
        self.max_hp = self.hp

        self.score_value = SCORE_BOSS + wave * 50

        # Speed: slower in FACILE, faster in DIFFICILE
        self.speed = 1.8 * diff

        # Déplacement
        self.target_x = SCREEN_W - 160.0
        self.target_y = float(SCREEN_H // 2)
        self.arrived = False
        self.move_timer = 0
        self.move_period = 120

        # Phase d'attaque — longer cooldown in FACILE, shorter in DIFFICILE
        self.phase = BossPhase.IDLE
        self.phase_timer = 0
        if diff <= 0.7:
            self.attack_cd = 120
        elif diff >= 1.5:
            self.attack_cd = 55
        else:
            self.attack_cd = 80
        self.angle2 = 0.0

        # Laser
        self.laser_charging = False
        self.laser_timer = 0
        self.laser_target = (0, 300)

        # Spawn
        self.spawned_children = []

        # Rage (sous 30% HP)
        self.rage = False

    @property
    def phase_ratio(self):
        return self.hp / self.max_hp

    def _choose_attack(self):
        options = [BossPhase.SPREAD, BossPhase.LASER, BossPhase.SUMMON]
        if self.phase_ratio < 0.5:
            options.append(BossPhase.CHARGE)
        self.phase = random.choice(options)
        self.phase_timer = 0

    def update(self):
        self.angle  += 1.5
        self.angle2 -= 2.0

        # Arrivée
        if not self.arrived:
            self.x += (self.target_x - self.x) * 0.04
            if abs(self.x - self.target_x) < 2:
                self.arrived = True
            return

        # Mode rage — no rage in FACILE
        if self.phase_ratio < 0.3 and not self.rage and self.diff > 0.7:
            self.rage = True
            self.speed *= 1.4
            self.attack_cd = max(40, self.attack_cd - 20)

        # Déplacement sinusoïdal — slower oscillation in FACILE
        self.move_timer += 1
        osc_speed = 0.025 * self.diff
        self.target_y = SCREEN_H/2 + math.sin(self.move_timer * osc_speed) * (SCREEN_H/2 - 70)
        self.y += (self.target_y - self.y) * 0.03

        # Logique de phase
        self.phase_timer += 1
        self.attack_cd -= 1
        if self.attack_cd <= 0:
            if self.diff <= 0.7:
                self.attack_cd = 100
            elif self.diff >= 1.5:
                self.attack_cd = 45 if not self.rage else 28
            else:
                self.attack_cd = 70 if not self.rage else 45
            self._choose_attack()

        if self.x < -120:
            self.active = False

    def get_bullets(self, px, py):
        bullets = []
        if not self.arrived:
            return bullets

        if self.phase == BossPhase.SPREAD and self.phase_timer == 1:
            if self.diff <= 0.7:
                count = 6
                spd = 2.5
            elif self.diff >= 1.5:
                count = 18 if not self.rage else 24
                spd = 5.0 if not self.rage else 6.5
            else:
                count = 12 if not self.rage else 18
                spd = 4.0 if not self.rage else 5.5
            for i in range(count):
                a = math.radians(i * (360 / count) + self.angle)
                bullets.append(EnemyBullet(
                    self.x, self.y,
                    math.cos(a)*spd, math.sin(a)*spd,
                    color=C_RED, radius=6))

        elif self.phase == BossPhase.LASER and self.phase_timer == 1:
            self.laser_charging = True
            self.laser_timer = 40
            self.laser_target = (px, py)

        elif self.phase == BossPhase.CHARGE and self.phase_timer == 1:
            # Rafale directe
            for _ in range(5):
                a = angle_to(self.x, self.y, px, py)
                spread = random.uniform(-0.2, 0.2)
                spd = 7.0
                bullets.append(EnemyBullet(
                    self.x, self.y,
                    math.cos(a+spread)*spd, math.sin(a+spread)*spd,
                    color=C_ORANGE, radius=5))

        # Laser
        if self.laser_charging:
            self.laser_timer -= 1
            if self.laser_timer <= 0:
                self.laser_charging = False
                # Balle laser large
                a = angle_to(self.x, self.y, *self.laser_target)
                bullets.append(EnemyBullet(
                    self.x, self.y,
                    math.cos(a)*10, math.sin(a)*10,
                    color=C_CYAN, radius=10, damage=2))

        return bullets

    def get_spawns(self):
        """Retourne les ennemis invoqués lors du pattern SUMMON."""
        if self.phase == BossPhase.SUMMON and self.phase_timer == 1:
            count = 3 if not self.rage else 5
            return [Enemy(SCREEN_W + 40 + i*30,
                          random.randint(60, SCREEN_H-60))
                    for i in range(count)]
        return []

    def draw(self, surf):
        # Halo externe pulsant
        pulse = int(40 + 30 * math.sin(pygame.time.get_ticks() * 0.004))
        draw_glow_circle(surf, C_RED, (self.x, self.y), self.radius + 20,
                         alpha=pulse, layers=2)

        # Corps
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=90, layers=5)

        # Anneaux rotatifs doubles
        for i in range(10):
            a = math.radians(self.angle + i * 36)
            rx = self.x + math.cos(a) * (self.radius + 10)
            ry = self.y + math.sin(a) * (self.radius + 10)
            draw_glow_circle(surf, C_ORANGE, (rx, ry), 4, alpha=60, layers=2)

        for i in range(6):
            a = math.radians(self.angle2 + i * 60)
            rx = self.x + math.cos(a) * (self.radius - 12)
            ry = self.y + math.sin(a) * (self.radius - 12)
            pygame.draw.circle(surf, C_WHITE, (int(rx), int(ry)), 3)

        # Laser en charge
        if self.laser_charging:
            alpha = int(200 * (1 - self.laser_timer / 40))
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.line(s, (*C_CYAN, alpha),
                             (int(self.x), int(self.y)),
                             (int(self.laser_target[0]), int(self.laser_target[1])), 3)
            surf.blit(s, (0, 0))

        bw = 300
        bx = SCREEN_W//2 - bw//2
        by = 50
        pygame.draw.rect(surf, (60, 0, 0),   (bx-1, by-1, bw+2, 16), border_radius=6)
        fill = int(bw * max(0, self.hp) / self.max_hp)
        if fill > 0:
            col = C_RED if self.phase_ratio < 0.3 else C_ORANGE if self.phase_ratio < 0.6 else C_GREEN
            pygame.draw.rect(surf, col, (bx, by, fill, 14), border_radius=6)
       