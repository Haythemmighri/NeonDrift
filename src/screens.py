
import pygame
import math
import random
import webbrowser

from src.constants import *
from src.utils import draw_neon_text, draw_text_centered, draw_glow_circle, draw_glow_rect
from src.payment import init_payment, check_payment_status


class MenuScreen:
    """Écran titre animé avec sélection de difficulté."""
    DIFFICULTIES = ["FACILE", "NORMAL", "DIFFICILE"]
    DIFF_SPEEDS  = [0.7, 1.0, 1.5]

    def __init__(self, fonts, highscore=0):
        self.fonts = fonts
        self.highscore = highscore
        self.selected = 1   # Normal par défaut
        self.t = 0
        self.particles = []
        self._spawn_timer = 0

    def update(self, events):
        self.t += 1
        self._spawn_timer -= 1
        if self._spawn_timer <= 0:
            self._spawn_timer = 8
            self.particles.append({
                "x": random.randint(0, SCREEN_W),
                "y": SCREEN_H + 10,
                "vy": -random.uniform(0.5, 2.0),
                "r": random.randint(1, 3),
                "col": random.choice([C_CYAN, C_MAGENTA, C_YELLOW, C_PURPLE]),
                "life": random.randint(80, 180),
            })
        for p in self.particles:
            p["y"] += p["vy"]
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

        action = None
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_LEFT, pygame.K_q):
                    self.selected = (self.selected - 1) % 3
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = (self.selected + 1) % 3
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    action = ("start", self.DIFF_SPEEDS[self.selected])
        return action

    def draw(self, surf, stars, nebula, games_played=0, unlocked=False):
        surf.fill(C_BG)
        nebula.draw(surf)
        stars.draw(surf)

        # Particules de fond
        for p in self.particles:
            alpha = int(200 * p["life"] / 180)
            s = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["col"], alpha), (p["r"], p["r"]), p["r"])
            surf.blit(s, (p["x"]-p["r"], int(p["y"])-p["r"]))

        # Titre
        pulse = 0.93 + 0.07 * math.sin(self.t * 0.04)
        colors = [C_CYAN, C_MAGENTA, C_YELLOW, C_GREEN, C_PURPLE]
        col = colors[(self.t // 70) % len(colors)]
        draw_neon_text(surf, "NEON", self.fonts["title"], col, SCREEN_W//2 - 130, 130)
        draw_neon_text(surf, "DRIFT", self.fonts["title"], C_WHITE, SCREEN_W//2 + 110, 130)

        # Ligne déco sous titre
        lx = SCREEN_W//2 - 220
        s = pygame.Surface((440, 3), pygame.SRCALPHA)
        for i in range(440):
            ratio = i / 440
            a = int(255 * math.sin(ratio * math.pi))
            s.set_at((i, 0), (*col, a))
            s.set_at((i, 1), (*col, a // 2))
        surf.blit(s, (lx, 170))

        # Sous-titre
        sub_lines = [
            "Survivez à la tempête quantique fractale.",
            f"Meilleur score :  {self.highscore:07d}",
        ]
        if not unlocked:
            sub_lines.append(f"Essais gratuits : {games_played}/{MAX_FREE_PLAYS}")
        else:
            sub_lines.append("Jeu Complet Débloqué !")
            
        for i, line in enumerate(sub_lines):
            t = self.fonts["small"].render(line, True, C_WHITE if i == 0 else C_YELLOW)
            surf.blit(t, t.get_rect(center=(SCREEN_W//2, 200 + i*28)))

        # Sélection de difficulté
        draw_text_centered(surf, "─── Difficulté ───", self.fonts["small"], C_GREY, 270)
        for i, label in enumerate(self.DIFFICULTIES):
            cx = SCREEN_W//2 - 160 + i*160
            selected = (i == self.selected)
            color = [C_GREEN, C_YELLOW, C_RED][i]
            if selected:
                draw_glow_rect(surf, color, (cx-55, 283, 110, 34), radius=8, alpha=40, width=2)
                draw_neon_text(surf, label, self.fonts["medium"], color, cx, 300)
            else:
                t = self.fonts["small"].render(label, True, C_GREY)
                surf.blit(t, t.get_rect(center=(cx, 300)))
        # Flèches
        if (self.t // 25) % 2 == 0:
            draw_text_centered(surf, "◄   ►  pour changer", self.fonts["tiny"], C_GREY, 325)

        # Contrôles
        controls = [
            ("ZQSD / Flèches",    "Déplacement"),
            ("ESPACE",            "Tir (maintenir)"),
            ("SHIFT",             "Dash (invincible)"),
            ("P / ÉCHAP",         "Pause"),
        ]
        y0 = 360
        for key, desc in controls:
            k = self.fonts["small"].render(key, True, C_YELLOW)
            d = self.fonts["small"].render(f"  →  {desc}", True, C_WHITE)
            total = k.get_width() + d.get_width()
            x = SCREEN_W//2 - total//2
            surf.blit(k, (x, y0))
            surf.blit(d, (x + k.get_width(), y0))
            y0 += 26

        # Power-ups légende
        y0 += 10
        defs = [("R", C_YELLOW, "Tir Rapide"), ("S", C_CYAN, "Bouclier"),
                ("M", C_MAGENTA, "Tir Triple"), ("L", C_GREEN, "Laser"), ("♥", C_RED, "+1 Vie")]
        x0 = SCREEN_W//2 - len(defs)*55//2
        for lbl, col, desc in defs:
            draw_glow_circle(surf, col, (x0+8, y0+8), 10, alpha=60, layers=2)
            t = self.fonts["tiny"].render(lbl, True, C_WHITE)
            surf.blit(t, t.get_rect(center=(x0+8, y0+8)))
            t2 = self.fonts["tiny"].render(desc, True, col)
            surf.blit(t2, (x0-t2.get_width()//2+8, y0+22))
            x0 += 110

        # Bouton démarrer
        if (self.t // 30) % 2 == 0:
            draw_text_centered(surf, "[ ENTRÉE ou ESPACE pour jouer ]",
                               self.fonts["medium"], C_GREEN, SCREEN_H - 35)


class PauseScreen:
    def __init__(self, fonts):
        self.fonts = fonts

    def draw(self, surf):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 175))
        surf.blit(overlay, (0, 0))
        draw_neon_text(surf, "PAUSE", self.fonts["big"], C_CYAN, SCREEN_W//2, SCREEN_H//2 - 40)
        draw_text_centered(surf, "P / ÉCHAP  →  Reprendre",
                           self.fonts["medium"], C_WHITE, SCREEN_H//2 + 20)
        draw_text_centered(surf, "ÉCHAP (menu)  →  Maintenez 2s",
                           self.fonts["small"], C_GREY, SCREEN_H//2 + 55)

    def update(self, events, hold_timer):
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_p,):
                    return "resume", 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            hold_timer += 1
            if hold_timer >= 120:
                return "menu", 0
        else:
            hold_timer = max(0, hold_timer - 2)
        return None, hold_timer


class WaveTransitionScreen:
    def __init__(self, fonts):
        self.fonts = fonts
        self.timer = 0
        self.duration = WAVE_PAUSE_FRAMES

    def start(self, wave):
        self.wave = wave
        self.timer = self.duration

    def update(self):
        self.timer -= 1
        return self.timer <= 0

    def draw(self, surf):
        ratio = self.timer / self.duration
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        alpha = int(140 * math.sin(ratio * math.pi))
        overlay.fill((0, 0, 20, alpha))
        surf.blit(overlay, (0, 0))

        wave_msgs = {
            2:  "Les Zigzags arrivent !",
            3:  "Les Tanks débarquent !",
            4:  "Les Fantômes rôdent !",
            5:  "⚠  BOSS  ⚠",
            6:  "Les Snipers visent !",
            7:  "Les Splitteurs envahissent !",
            10: "⚠  BOSS ULTIME  ⚠",
        }
        sub = wave_msgs.get(self.wave, "Bonne chance !")
        col = C_RED if "BOSS" in sub else C_MAGENTA
        scale = 0.7 + 0.3 * math.sin(ratio * math.pi)
        draw_neon_text(surf, f"VAGUE  {self.wave}", self.fonts["big"], col,
                       SCREEN_W//2, SCREEN_H//2 - 25)
        draw_text_centered(surf, sub, self.fonts["medium"], C_WHITE, SCREEN_H//2 + 30)


class GameOverScreen:
    def __init__(self, fonts):
        self.fonts = fonts
        self.t = 0

    def update(self, events):
        self.t += 1
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "restart"
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
        return None

    def draw(self, surf, score, highscore, wave, kills, shots, max_combo, new_record):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((25, 0, 0, 185))
        surf.blit(overlay, (0, 0))

        # GAME OVER
        draw_neon_text(surf, "GAME  OVER", self.fonts["big"], C_RED, SCREEN_W//2, 120)

        # Score
        draw_neon_text(surf, f"SCORE  {score:07d}", self.fonts["medium"],
                       C_YELLOW, SCREEN_W//2, 185)
        if new_record:
            if (self.t // 20) % 2 == 0:
                draw_neon_text(surf, "✦  NOUVEAU RECORD !  ✦", self.fonts["medium"],
                               C_GREEN, SCREEN_W//2, 218)
        else:
            t = self.fonts["small"].render(f"Meilleur : {highscore:07d}", True, C_DARK_CYAN)
            surf.blit(t, t.get_rect(center=(SCREEN_W//2, 218)))

        # Stats
        stats = [
            (f"Vague atteinte",  str(wave),      C_CYAN),
            (f"Ennemis tués",    str(kills),     C_GREEN),
            (f"Tirs effectués",  str(shots),     C_YELLOW),
            (f"Meilleur combo",  f"x{max_combo}", C_ORANGE),
        ]
        y0 = 260
        bx, bw, bh = SCREEN_W//2 - 140, 280, 30
        draw_glow_rect(surf, C_DARK_GREY, (bx-10, y0-10, bw+20, len(stats)*bh+20), radius=8, alpha=60)
        for label, value, color in stats:
            tl = self.fonts["small"].render(label, True, C_GREY)
            tv = self.fonts["small"].render(value, True, color)
            surf.blit(tl, (bx, y0 + 4))
            surf.blit(tv, (bx + bw - tv.get_width(), y0 + 4))
            y0 += bh

        # Boutons
        y0 += 20
        if (self.t // 28) % 2 == 0:
            draw_text_centered(surf, "ENTRÉE / ESPACE  →  Rejouer",
                               self.fonts["medium"], C_WHITE, y0 + 10)
        draw_text_centered(surf, "ÉCHAP  →  Menu principal",
                           self.fonts["small"], C_GREY, y0 + 44)


class PaymentScreen:
    def __init__(self, fonts):
        self.fonts = fonts
        self.t = 0
        self.pay_url = None
        self.payment_ref = None
        self.status = "idle" # idle, loading, waiting, success, error
        self.check_timer = 0
        
    def update(self, events):
        self.t += 1
        
        if self.status == "waiting":
            self.check_timer -= 1
            if self.check_timer <= 0:
                self.check_timer = 180 # Check every 3 seconds
                if check_payment_status(self.payment_ref):
                    self.status = "success"
                    return "success"
                    
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE) and self.status in ("idle", "error"):
                    self.status = "loading"
                    url, ref = init_payment()
                    if url and ref:
                        self.pay_url = url
                        self.payment_ref = ref
                        self.status = "waiting"
                        webbrowser.open(url)
                    else:
                        self.status = "error"
        return None

    def draw(self, surf, stars, nebula):
        surf.fill(C_BG)
        nebula.draw(surf)
        stars.draw(surf)
        
        draw_neon_text(surf, "JEU VERROUILLÉ", self.fonts["big"], C_RED, SCREEN_W//2, 150)
        draw_text_centered(surf, "Vous avez atteint la limite de 3 parties gratuites.", self.fonts["medium"], C_WHITE, 220)
        
        if self.status == "idle":
            draw_text_centered(surf, "[ ENTRÉE ou ESPACE pour Payer (2 TND) ]", self.fonts["medium"], C_GREEN, 320)
        elif self.status == "loading":
            draw_text_centered(surf, "Création du lien de paiement...", self.fonts["medium"], C_YELLOW, 320)
        elif self.status == "waiting":
            draw_text_centered(surf, "Paiement en cours dans le navigateur...", self.fonts["medium"], C_YELLOW, 300)
            draw_text_centered(surf, "Vérification automatique en cours.", self.fonts["small"], C_GREY, 340)
        elif self.status == "error":
            draw_text_centered(surf, "Erreur de connexion à Konnect.", self.fonts["medium"], C_RED, 300)
            draw_text_centered(surf, "[ ENTRÉE pour réessayer ]", self.fonts["medium"], C_GREEN, 340)
        elif self.status == "success":
            draw_text_centered(surf, "Paiement réussi ! Jeu débloqué.", self.fonts["medium"], C_GREEN, 320)
            
        draw_text_centered(surf, "ÉCHAP  →  Menu principal", self.fonts["small"], C_GREY, SCREEN_H - 50)

