import pygame
import math
import random
import os
import json

from src.constants import *


# ─── Rendu néon ─────────────────────────────────────────────────────────────

def draw_glow_circle(surf, color, pos, radius, alpha=80, layers=4):
    x, y = int(pos[0]), int(pos[1])
    for i in range(layers, 0, -1):
        r = radius + i * 5
        a = max(0, alpha - i * 18)
        s = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        surf.blit(s, (x - r, y - r))
    pygame.draw.circle(surf, color, (x, y), max(1, radius))


def draw_glow_line(surf, color, p1, p2, width=2, alpha=120):
    s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    pygame.draw.line(s, (*color, alpha), p1, p2, width + 4)
    pygame.draw.line(s, (*color, 220), p1, p2, width)
    surf.blit(s, (0, 0))


def draw_glow_rect(surf, color, rect, radius=6, alpha=60, width=0):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    if width:
        pygame.draw.rect(s, (*color, 200), (0, 0, rect[2], rect[3]), width, border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))


def draw_neon_text(surf, text, font, color, cx, cy, alpha=255):
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,1),(-1,1),(1,-1),(-2,-2),(2,2)]:
        g = font.render(text, True, color)
        surf.blit(g, g.get_rect(center=(cx+dx, cy+dy)))
    t = font.render(text, True, C_WHITE)
    surf.blit(t, t.get_rect(center=(cx, cy)))


def draw_text_centered(surf, text, font, color, cy, x=None, shadow=True):
    cx = x if x is not None else SCREEN_W // 2
    if shadow:
        s = font.render(text, True, (0,0,0))
        surf.blit(s, s.get_rect(center=(cx+2, cy+2)))
    t = font.render(text, True, color)
    r = t.get_rect(center=(cx, cy))
    surf.blit(t, r)
    return r


def lerp(a, b, t):
    return a + (b - a) * t


def angle_to(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


# ─── Persistance ────────────────────────────────────────────────────────────

def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default or {}


def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ─── Génération de sons ─────────────────────────────────────────────────────

def _gen_sound(freq, dur_ms, wave="square", vol=0.15, decay=True):
    sr = 44100
    n  = int(sr * dur_ms / 1000)
    buf = bytearray(n * 2)
    for i in range(n):
        t = i / sr
        if wave == "square":
            v = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif wave == "sine":
            v = math.sin(2 * math.pi * freq * t)
        elif wave == "saw":
            v = 2.0 * (t * freq - math.floor(0.5 + t * freq))
        elif wave == "noise":
            v = random.uniform(-1, 1)
        else:
            v = 0.0
        env = (1.0 - i / n) if decay else 1.0
        val = int(v * env * vol * 32767)
        val = clamp(val, -32768, 32767)
        buf[i*2]   = val & 0xFF
        buf[i*2+1] = (val >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))


def create_sounds():
    sounds = {}
    try:
        sounds["shoot"]      = _gen_sound(880,  60,  "square", 0.10)
        sounds["shoot2"]     = _gen_sound(440,  60,  "square", 0.10)
        sounds["explode"]    = _gen_sound(120,  250, "noise",  0.28)
        sounds["explode_big"]= _gen_sound(60,   450, "noise",  0.35)
        sounds["powerup"]    = _gen_sound(660,  280, "sine",   0.18)
        sounds["hit"]        = _gen_sound(220,  130, "square", 0.22)
        sounds["shield_hit"] = _gen_sound(880,  100, "sine",   0.15)
        sounds["wave_start"] = _gen_sound(330,  500, "sine",   0.14)
        sounds["boss"]       = _gen_sound(110,  700, "saw",    0.20)
        sounds["gameover"]   = _gen_sound(80,   800, "noise",  0.32)
        sounds["warning"]    = _gen_sound(180,  600, "saw",    0.28)
        sounds["menu_move"]  = _gen_sound(440,  50,  "sine",   0.08)
        sounds["collect"]    = _gen_sound(990,  120, "sine",   0.12)
        sounds["laser"]      = _gen_sound(1200, 150, "saw",    0.12)
    except Exception:
        pass
    return sounds
