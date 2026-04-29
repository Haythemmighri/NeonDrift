

import pygame
import math
import random

from src.constants import *
from src.utils import draw_glow_circle, draw_glow_line


class StarField:
    def __init__(self, count=160):
        self.stars = [self._new_star(random.randint(0, SCREEN_W)) for _ in range(count)]

    def _new_star(self, x=None):
        return [
            x if x is not None else SCREEN_W,
            random.randint(0, SCREEN_H),
            random.uniform(0.3, 3.0),
            random.randint(1, 3),
        ]

    def update(self, speed=1.0):
        for s in self.stars:
            s[0] -= s[2] * speed
            if s[0] < 0:
                self.stars[self.stars.index(s)] = self._new_star()

    def draw(self, surf):
        for x, y, spd, size in self.stars:
            b = int(80 + spd * 55)
            c = (b, b, min(255, b + 90))
            pygame.draw.circle(surf, c, (int(x), int(y)), size)


# ─── NEBULA (fond atmosphérique animé) ───────────────────────────────────────

class Nebula:
    def __init__(self, count=6):
        self.blobs = [
            {
                "x": random.randint(0, SCREEN_W),
                "y": random.randint(0, SCREEN_H),
                "r": random.randint(100, 220),
                "color": random.choice([C_CYAN, C_PURPLE, C_MAGENTA, C_TEAL]),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.2, 0.6),
            }
            for _ in range(count)
        ]
        self.t = 0

    def update(self):
        self.t += 0.008
        for b in self.blobs:
            b["x"] -= b["speed"]
            if b["x"] < -b["r"]:
                b["x"] = SCREEN_W + b["r"]
                b["y"] = random.randint(0, SCREEN_H)

    def draw(self, surf):
        for b in self.blobs:
            pulse = 0.6 + 0.4 * math.sin(self.t + b["phase"])
            alpha = int(10 * pulse)
            r = int(b["r"] * pulse)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*b["color"], alpha), (r, r), r)
            surf.blit(s, (int(b["x"]) - r, int(b["y"]) - r))


# ─── PARTICLE ────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None,
                 life=30, size=3, gravity=0.05, glow=True):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-3, 3)
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.glow = glow

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.life -= 1

    def draw(self, surf):
        ratio = self.life / self.max_life
        alpha = int(255 * ratio)
        r = max(1, int(self.size * ratio))
        if self.glow:
            s = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha // 3), (r*2, r*2), r*2)
            pygame.draw.circle(s, (*self.color, alpha),     (r*2, r*2), r)
            surf.blit(s, (int(self.x) - r*2, int(self.y) - r*2))
        else:
            s = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
            surf.blit(s, (int(self.x)-r, int(self.y)-r))

    @property
    def dead(self):
        return self.life <= 0


# ─── TRAIL PARTICLE (trainée du joueur) ─────────────────────────────────────

class TrailParticle(Particle):
    def __init__(self, x, y, color):
        super().__init__(x, y, color,
                         vx=random.uniform(-0.3, 0.3),
                         vy=random.uniform(-0.3, 0.3),
                         life=18, size=4, gravity=0, glow=True)


# ─── SHOCKWAVE ───────────────────────────────────────────────────────────────

class Shockwave:
    def __init__(self, x, y, color, max_r=80):
        self.x = x
        self.y = y
        self.color = color
        self.r = 5
        self.max_r = max_r
        self.life = 25
        self.max_life = 25

    def update(self):
        self.r += (self.max_r - self.r) * 0.25
        self.life -= 1

    def draw(self, surf):
        alpha = int(200 * self.life / self.max_life)
        width = max(1, int(3 * self.life / self.max_life))
        s = pygame.Surface((int(self.r*2+4), int(self.r*2+4)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha),
                           (int(self.r+2), int(self.r+2)), int(self.r), width)
        surf.blit(s, (int(self.x - self.r - 2), int(self.y - self.r - 2)))

    @property
    def dead(self):
        return self.life <= 0


# ─── LASER BEAM ──────────────────────────────────────────────────────────────

class LaserBeam:
    """Laser visuel temporaire (utilisé par le boss)."""
    def __init__(self, x1, y1, x2, y2, color=C_RED, life=15):
        self.p1 = (x1, y1)
        self.p2 = (x2, y2)
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        width = max(1, int(5 * self.life / self.max_life))
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.line(s, (*self.color, alpha // 2), self.p1, self.p2, width + 6)
        pygame.draw.line(s, (*self.color, alpha),      self.p1, self.p2, width)
        surf.blit(s, (0, 0))

    @property
    def dead(self):
        return self.life <= 0


# ─── EFFECT MANAGER ──────────────────────────────────────────────────────────

class EffectManager:
    def __init__(self):
        self.particles  = []
        self.shockwaves = []
        self.lasers     = []
        self.flashes    = []   # [(color, alpha, decay)]

    def explosion(self, x, y, color, count=24, big=False):
        sz = 6 if big else 4
        lf = 50 if big else 35
        for _ in range(count):
            spd = random.uniform(1, 7 if big else 5)
            angle = random.uniform(0, math.pi * 2)
            self.particles.append(Particle(
                x, y, color,
                vx=math.cos(angle)*spd,
                vy=math.sin(angle)*spd,
                life=random.randint(20, lf),
                size=random.randint(2, sz),
            ))
        self.shockwaves.append(Shockwave(x, y, color, max_r=90 if big else 55))
        if big:
            self.flashes.append([color, 120, 15])

    def sparks(self, x, y, color, count=8):
        for _ in range(count):
            spd = random.uniform(0.5, 3)
            angle = random.uniform(0, math.pi * 2)
            self.particles.append(Particle(
                x, y, color,
                vx=math.cos(angle)*spd,
                vy=math.sin(angle)*spd,
                life=random.randint(10, 22),
                size=2, gravity=0.1,
            ))

    def trail(self, x, y, color):
        self.particles.append(TrailParticle(x, y, color))

    def laser(self, x1, y1, x2, y2, color=C_RED):
        self.lasers.append(LaserBeam(x1, y1, x2, y2, color))

    def screen_flash(self, color, alpha=80, decay=8):
        self.flashes.append([color, alpha, decay])

    def update(self):
        for p in self.particles:  p.update()
        for s in self.shockwaves: s.update()
        for l in self.lasers:     l.update()
        for f in self.flashes:
            f[1] -= f[2]

        self.particles  = [p for p in self.particles  if not p.dead]
        self.shockwaves = [s for s in self.shockwaves if not s.dead]
        self.lasers     = [l for l in self.lasers     if not l.dead]
        self.flashes    = [f for f in self.flashes    if f[1] > 0]

    def draw(self, surf):
        for s in self.shockwaves: s.draw(surf)
        for l in self.lasers:     l.draw(surf)
        for p in self.particles:  p.draw(surf)
        for color, alpha, _ in self.flashes:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            s.fill((*color, int(alpha)))
            surf.blit(s, (0, 0))
