
import pygame
import math
import random

from src.constants import *
from src.utils import draw_glow_circle, clamp


class PlayerBullet:
    def __init__(self, x, y, angle=0.0, color=C_YELLOW, speed=BULLET_SPEED, damage=1):
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = 6
        self.color = color
        self.active = True
        self.damage = damage

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x > SCREEN_W + 20 or self.x < -20 or self.y < -20 or self.y > SCREEN_H + 20:
            self.active = False

    def draw(self, surf):
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=70, layers=3)
        # Noyau blanc
        pygame.draw.circle(surf, C_WHITE, (int(self.x), int(self.y)), max(2, self.radius - 3))


class Player:
    BASE_SPEED     = PLAYER_SPEED
    MAX_LIVES      = 3
    INVINCIBLE_DUR = 130   # frames
    DASH_SPEED     = 18
    DASH_DURATION  = 12
    DASH_COOLDOWN  = 60

    def __init__(self):
        self.x = 130.0
        self.y = float(SCREEN_H) / 2
        self.radius = 15
        self.color = C_CYAN
        self.lives = self.MAX_LIVES
        self.max_lives = self.MAX_LIVES

        # Tir
        self.shoot_timer = 0

        # Invincibilité
        self.invincible = 0

        # Dash
        self.dashing = False
        self.dash_timer = 0
        self.dash_cd = 0
        self.dash_vx = 0.0
        self.dash_vy = 0.0

        # Rotation déco
        self.angle = 0.0
        self.inner_angle = 0.0

        # Power-ups actifs : {type: frames_restants}
        self.powerups: dict[str, int] = {}

        # Stats accumulées
        self.shots_fired  = 0
        self.kills        = 0
        self.combo        = 0
        self.combo_timer  = 0
        self.max_combo    = 0

        # Dernier mouvement (pour la traînée)
        self.last_x = self.x
        self.last_y = self.y

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def has_shield(self):
        return "shield" in self.powerups

    @property
    def has_rapid(self):
        return "rapid" in self.powerups

    @property
    def has_multishot(self):
        return "multishot" in self.powerups

    @property
    def has_laser_shot(self):
        return "laser" in self.powerups

    @property
    def current_shoot_cooldown(self):
        return RAPID_FIRE_COOLDOWN if self.has_rapid else PLAYER_SHOOT_COOLDOWN

    def can_shoot(self):
        return self.shoot_timer <= 0

    def can_dash(self):
        return self.dash_cd <= 0 and not self.dashing

    # ── Input ────────────────────────────────────────────────────────────────

    def handle_input(self, events):
        keys = pygame.key.get_pressed()

        if not self.dashing:
            dx, dy = 0.0, 0.0
            if keys[pygame.K_UP]    or keys[pygame.K_z]: dy -= 1
            if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
            if keys[pygame.K_LEFT]  or keys[pygame.K_q]: dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
            # Normaliser diagonale
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            self.x += dx * self.BASE_SPEED
            self.y += dy * self.BASE_SPEED

        else:
            # Dash actif
            self.x += self.dash_vx
            self.y += self.dash_vy
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
                self.dash_cd = self.DASH_COOLDOWN

        self.x = clamp(self.x, self.radius, SCREEN_W - self.radius)
        self.y = clamp(self.y, self.radius, SCREEN_H - self.radius)

        # Dash avec Shift
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    if self.can_dash():
                        self._start_dash(keys)

    def _start_dash(self, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_UP]    or keys[pygame.K_z]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if keys[pygame.K_LEFT]  or keys[pygame.K_q]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if dx == 0 and dy == 0:
            dx = 1.0   # dash avant par défaut
        length = math.hypot(dx, dy)
        self.dash_vx = (dx / length) * self.DASH_SPEED
        self.dash_vy = (dy / length) * self.DASH_SPEED
        self.dashing   = True
        self.dash_timer = self.DASH_DURATION
        self.invincible = max(self.invincible, self.DASH_DURATION)

    # ── Tir ─────────────────────────────────────────────────────────────────

    def get_bullets(self):
        """Retourne la liste des balles produites par un tir."""
        if not self.can_shoot():
            return []
        self.shoot_timer = self.current_shoot_cooldown
        self.shots_fired += 1
        bullets = []

        if self.has_laser_shot:
            # Balle laser large + rapide
            b = PlayerBullet(self.x + self.radius, self.y, 0,
                             color=C_CYAN, speed=18, damage=2)
            b.radius = 9
            bullets.append(b)
        elif self.has_multishot:
            for angle in [-0.28, 0, 0.28]:
                bullets.append(PlayerBullet(
                    self.x + self.radius, self.y, angle,
                    color=C_MAGENTA, damage=1))
        else:
            bullets.append(PlayerBullet(self.x + self.radius, self.y, 0, C_YELLOW))

        return bullets

    # ── Vie & état ──────────────────────────────────────────────────────────

    def hit(self):
        """Appelé quand le joueur prend un coup. Retourne True si vraiment blessé."""
        if self.invincible > 0 or self.dashing:
            return False
        if self.has_shield:
            del self.powerups["shield"]
            self.invincible = 60
            return False
        self.lives -= 1
        self.invincible = self.INVINCIBLE_DUR
        self.combo = 0
        return True

    def add_kill(self):
        self.kills += 1
        self.combo += 1
        self.combo_timer = 120
        if self.combo > self.max_combo:
            self.max_combo = self.combo

    def add_powerup(self, ptype):
        self.powerups[ptype] = POWERUP_DURATION

    # ── Update ──────────────────────────────────────────────────────────────

    def update(self):
        self.angle       += 2.2
        self.inner_angle -= 3.5
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.dash_cd > 0:
            self.dash_cd -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
        # Décrémenter power-ups
        for k in list(self.powerups.keys()):
            self.powerups[k] -= 1
            if self.powerups[k] <= 0:
                del self.powerups[k]

    # ── Draw ────────────────────────────────────────────────────────────────

    def draw(self, surf, fx_manager=None):
        # Traînée
        if fx_manager and (abs(self.x - self.last_x) > 1 or abs(self.y - self.last_y) > 1):
            fx_manager.trail(self.x, self.y, C_CYAN)
        self.last_x, self.last_y = self.x, self.y

        # Clignotement invincibilité
        if self.invincible > 0 and (self.invincible // 6) % 2 == 1 and not self.dashing:
            return

        # Bouclier
        if self.has_shield:
            alpha = int(60 + 40 * math.sin(pygame.time.get_ticks() * 0.005))
            s = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_CYAN, alpha), (40, 40), 36, 3)
            surf.blit(s, (int(self.x) - 40, int(self.y) - 40))

        # Halo principal
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=70)

        # Anneau extérieur rotatif
        for i in range(8):
            a = math.radians(self.angle + i * 45)
            rx = self.x + math.cos(a) * (self.radius + 8)
            ry = self.y + math.sin(a) * (self.radius + 8)
            draw_glow_circle(surf, C_YELLOW, (rx, ry), 2, alpha=50, layers=1)

        # Anneau intérieur contra-rotatif
        for i in range(4):
            a = math.radians(self.inner_angle + i * 90)
            rx = self.x + math.cos(a) * (self.radius - 4)
            ry = self.y + math.sin(a) * (self.radius - 4)
            pygame.draw.circle(surf, C_WHITE, (int(rx), int(ry)), 2)

        # Indicateur dash
        if self.dash_cd > 0:
            pct = 1.0 - self.dash_cd / self.DASH_COOLDOWN
            arc_r = self.radius + 14
            s = pygame.Surface((arc_r*2+2, arc_r*2+2), pygame.SRCALPHA)
            pygame.draw.arc(s, (*C_TEAL, 200),
                            (1, 1, arc_r*2, arc_r*2),
                            -math.pi/2,
                            -math.pi/2 + math.pi*2*pct, 2)
            surf.blit(s, (int(self.x)-arc_r-1, int(self.y)-arc_r-1))
        else:
            # Dash prêt : petit flash
            pygame.draw.circle(surf, C_TEAL, (int(self.x), int(self.y)), self.radius+14, 1)

    def draw_hud(self, surf, fonts):
        """Vies, power-ups actifs, combo."""
        # Vies
        for i in range(self.max_lives):
            color = C_CYAN if i < self.lives else C_DARK_GREY
            draw_glow_circle(surf, color, (22 + i * 32, SCREEN_H - 22), 10,
                             alpha=50 if i < self.lives else 20, layers=2)

        # Power-ups actifs
        icons = {"rapid": ("R", C_YELLOW), "shield": ("S", C_CYAN),
                 "multishot": ("M", C_MAGENTA), "laser": ("L", C_GREEN)}
        x0 = SCREEN_W - 200
        row = 0
        for ptype, frames in self.powerups.items():
            if ptype not in icons:
                continue
            lbl, col = icons[ptype]
            bar_w = int(90 * frames / POWERUP_DURATION)
            pygame.draw.rect(surf, C_DARK_GREY, (x0, SCREEN_H-42+row*22, 90, 12), border_radius=4)
            pygame.draw.rect(surf, col, (x0, SCREEN_H-42+row*22, bar_w, 12), border_radius=4)
            t = fonts["tiny"].render(lbl, True, col)
            surf.blit(t, (x0 - 16, SCREEN_H-44+row*22))
            row += 1

        # Dash cooldown label
        if self.dash_cd == 0:
            t = fonts["tiny"].render("DASH ✓", True, C_TEAL)
        else:
            pct = int(100 * (1 - self.dash_cd / self.DASH_COOLDOWN))
            t = fonts["tiny"].render(f"DASH {pct}%", True, C_GREY)
        surf.blit(t, (22, SCREEN_H - 45))

        # Combo
        if self.combo >= 3:
            cx = 80
            col = C_ORANGE if self.combo < 10 else C_MAGENTA
            t = fonts["medium"].render(f"x{self.combo} COMBO", True, col)
            surf.blit(t, (cx, SCREEN_H - 70))
