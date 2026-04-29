
import pygame
import math
import random

from src.constants import *
from src.utils import draw_glow_circle, draw_glow_rect, draw_neon_text, draw_text_centered
from src.enemies import (Enemy, ZigzagEnemy, TankEnemy, GhostEnemy,
                          SplitterEnemy, SniperEnemy, Boss)


# ─── POWER-UP ────────────────────────────────────────────────────────────────

POWERUP_DEFS = {
    "rapid":     {"label": "R", "color": C_YELLOW,  "desc": "Tir Rapide"},
    "shield":    {"label": "S", "color": C_CYAN,    "desc": "Bouclier"},
    "multishot": {"label": "M", "color": C_MAGENTA, "desc": "Tir Triple"},
    "laser":     {"label": "L", "color": C_GREEN,   "desc": "Laser"},
    "life":      {"label": "♥", "color": C_RED,     "desc": "+1 Vie"},
}

class PowerUp:
    TYPES = list(POWERUP_DEFS.keys())
    WEIGHTS = [30, 25, 25, 15, 5]   # pondération du tirage

    def __init__(self, x, y, ptype=None):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype or random.choices(self.TYPES, weights=self.WEIGHTS, k=1)[0]
        self.radius = 14
        self.active = True
        self.t = random.uniform(0, math.pi * 2)
        self.base_y = float(y)

    @property
    def color(self):
        return POWERUP_DEFS[self.ptype]["color"]

    @property
    def label(self):
        return POWERUP_DEFS[self.ptype]["label"]

    def update(self):
        self.x -= 1.8
        self.t += 0.06
        self.y = self.base_y + math.sin(self.t) * 14
        if self.x < -30:
            self.active = False

    def draw(self, surf, font):
        draw_glow_circle(surf, self.color, (self.x, self.y), self.radius, alpha=80)
        # Anneau pulsant
        pulse = int(3 + 2 * math.sin(self.t * 3))
        s = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 60),
                           (self.radius*2, self.radius*2), self.radius*2 - pulse, 2)
        surf.blit(s, (int(self.x)-self.radius*2, int(self.y)-self.radius*2))
        t = font.render(self.label, True, C_WHITE)
        surf.blit(t, t.get_rect(center=(int(self.x), int(self.y))))


# ─── FLOATING SCORE TEXT ─────────────────────────────────────────────────────

class FloatText:
    def __init__(self, x, y, text, color=C_YELLOW, size="small"):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.life = 55
        self.max_life = 55
        self.size = size

    def update(self):
        self.y -= 1.2
        self.life -= 1

    def draw(self, surf, fonts):
        alpha = int(255 * self.life / self.max_life)
        f = fonts.get(self.size, fonts["small"])
        t = f.render(self.text, True, self.color)
        t.set_alpha(alpha)
        surf.blit(t, t.get_rect(center=(int(self.x), int(self.y))))

    @property
    def dead(self):
        return self.life <= 0


# ─── WAVE MANAGER ────────────────────────────────────────────────────────────

class WaveManager:
    def __init__(self):
        self.wave = 1
        self.spawn_queue = []
        self.spawn_timer = 0
        self.between_waves = False
        self.wave_cooldown = 0
        self.boss_active = False
        self._build_wave()

    def _speed(self, base=2.5):
        return base + (self.wave - 1) * 0.28

    def _build_wave(self):
        q = []
        is_boss_wave = (self.wave % BOSS_APPEAR_WAVE == 0)
        if is_boss_wave:
            # Vague boss : quelques ennemis + le boss en dernier
            n = 4 + self.wave // 2
            for _ in range(n):
                q.append(("basic", self._speed()))
            q.append(("boss", self.wave))
        else:
            n = 6 + self.wave * 3
            for _ in range(n):
                roll = random.random()
                if self.wave >= 7 and roll < 0.10:
                    q.append(("sniper", self._speed()))
                elif self.wave >= 5 and roll < 0.18:
                    q.append(("splitter", self._speed()))
                elif self.wave >= 4 and roll < 0.26:
                    q.append(("ghost", self._speed()))
                elif self.wave >= 3 and roll < 0.38:
                    q.append(("tank", self._speed()))
                elif self.wave >= 2 and roll < 0.55:
                    q.append(("zigzag", self._speed()))
                else:
                    q.append(("basic", self._speed()))
        self.spawn_queue = q
        self.spawn_timer = 0
        self.spawn_interval = max(20, 70 - self.wave * 4)

    def _make_enemy(self, etype, param):
        y = random.randint(50, SCREEN_H - 50)
        x = SCREEN_W + 60
        if etype == "basic":
            e = Enemy(x, y)
            e.speed = param
            return e
        elif etype == "zigzag":
            return ZigzagEnemy(x, y, param)
        elif etype == "tank":
            return TankEnemy(x, y, param)
        elif etype == "ghost":
            return GhostEnemy(x, y, param)
        elif etype == "splitter":
            return SplitterEnemy(x, y, param)
        elif etype == "sniper":
            return SniperEnemy(x, y, param)
        elif etype == "boss":
            self.boss_active = True
            return Boss(param)   # param = wave number
        return None

    def update(self, enemies):
        if self.between_waves:
            self.wave_cooldown -= 1
            if self.wave_cooldown <= 0:
                self.between_waves = False
                self.wave += 1
                self.boss_active = False
                self._build_wave()
            return False   # pas de nouvelle vague

        self.spawn_timer -= 1
        if self.spawn_timer <= 0 and self.spawn_queue:
            etype, param = self.spawn_queue.pop(0)
            e = self._make_enemy(etype, param)
            if e:
                enemies.append(e)
            self.spawn_timer = self.spawn_interval

        return False

    def check_wave_complete(self, enemies):
        """Retourne True si la vague vient de se terminer."""
        if not self.spawn_queue and not enemies and not self.between_waves:
            self.between_waves = True
            self.wave_cooldown = WAVE_PAUSE_FRAMES
            return True
        return False

    @property
    def is_boss_wave(self):
        return self.wave % BOSS_APPEAR_WAVE == 0


# ─── SCORE SYSTEM ────────────────────────────────────────────────────────────

class ScoreSystem:
    def __init__(self, highscore=0):
        self.score = 0
        self.highscore = highscore
        self.multiplier = 1
        self.float_texts: list[FloatText] = []

    def add(self, value, x, y, combo=1):
        mult = max(1, combo // 3)
        total = value * mult
        self.score += total
        if self.score > self.highscore:
            self.highscore = self.score
        color = C_ORANGE if mult > 1 else C_YELLOW
        text = f"+{total}" if mult <= 1 else f"+{total} x{mult}!"
        self.float_texts.append(FloatText(x, y, text, color))

    def update(self):
        for t in self.float_texts:
            t.update()
        self.float_texts = [t for t in self.float_texts if not t.dead]

    def draw(self, surf, fonts):
        for t in self.float_texts:
            t.draw(surf, fonts)


# ─── HUD ─────────────────────────────────────────────────────────────────────

class HUD:
    def __init__(self):
        self.boss_label_alpha = 0

    def draw(self, surf, fonts, score, highscore, wave, wave_mgr, player, boss=None):
        # Score
        draw_neon_text(surf, f"SCORE  {score:07d}", fonts["medium"], C_YELLOW,
                       SCREEN_W//2, 20)
        # Highscore
        t = fonts["tiny"].render(f"BEST {highscore:07d}", True, C_DARK_CYAN)
        surf.blit(t, t.get_rect(center=(SCREEN_W//2, 38)))

        # Vague
        draw_neon_text(surf, f"WAVE  {wave}", fonts["medium"], C_CYAN,
                       SCREEN_W - 80, 20)

        # Boss label
        if boss and boss.arrived:
            alpha = min(255, self.boss_label_alpha + 4)
            self.boss_label_alpha = alpha
            t = fonts["medium"].render(f"BOSS — VAGUE {wave}", True, C_RED)
            t.set_alpha(alpha)
            surf.blit(t, t.get_rect(center=(SCREEN_W//2, 70)))
        else:
            self.boss_label_alpha = max(0, self.boss_label_alpha - 4)

        # Player HUD
        player.draw_hud(surf, fonts)
