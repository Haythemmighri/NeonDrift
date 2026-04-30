
import pygame
import math
import random
import webbrowser
import threading

from src.constants import *
from src.utils import draw_neon_text, draw_text_centered, draw_glow_circle, draw_glow_rect
from src.payment import init_payment, check_payment_status, validate_cash_code


def _get_clipboard_text():
    """Lit le presse-papier de façon fiable — ne crash jamais."""
    import sys
    # Windows : PowerShell (100% safe, pas de ctypes)
    if sys.platform == "win32":
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=3,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            return result.stdout.strip()
        except Exception:
            return ""
    # Linux : xclip / xsel
    try:
        import subprocess
        r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                           capture_output=True, timeout=1)
        return r.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass
    try:
        import subprocess
        r = subprocess.run(["xsel", "--clipboard", "--output"],
                           capture_output=True, timeout=1)
        return r.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass
    return ""


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
        self._leaderboard_entries = []
        self._leaderboard_status  = "idle"
        # Trial counter info — set each frame by Game
        self._trial_unlocked  = False
        self._trial_remaining = MAX_FREE_PLAYS
        self._trial_max       = MAX_FREE_PLAYS

    def set_trial_info(self, unlocked: bool, plays_count: int):
        """Called each frame from Game with up-to-date trial state."""
        self._trial_unlocked  = unlocked
        self._trial_remaining = max(0, MAX_FREE_PLAYS - plays_count)
        self._trial_max       = MAX_FREE_PLAYS

    def set_leaderboard(self, entries, status):
        """Called each frame from Game with fresh leaderboard data."""
        self._leaderboard_entries = entries
        self._leaderboard_status  = status

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

    def draw(self, surf, stars, nebula):
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

        # ── Trial counter (bottom-left panel) ───────────────────────────
        self._draw_trial_counter(surf)

        # Bouton démarrer
        if (self.t // 30) % 2 == 0:
            draw_text_centered(surf, "[ ENTRÉE ou ESPACE pour jouer ]",
                               self.fonts["medium"], C_GREEN, SCREEN_H - 35)

        # ── Leaderboard panel (right side) ──────────────────────────────
        self._draw_leaderboard(surf)

    def _draw_trial_counter(self, surf):
        """Bottom-left neon panel showing remaining free plays or unlock badge."""
        PAD   = 10
        pw    = 200
        ph    = 52
        px    = PAD
        py    = SCREEN_H - ph - PAD - 30   # sit above the start button

        # Panel BG
        draw_glow_rect(surf, C_DARK_GREY, (px, py, pw, ph), radius=8, alpha=150)

        cx = px + pw // 2

        if self._trial_unlocked:
            # ── Unlocked badge ───────────────────────────────────────────
            draw_glow_rect(surf, C_GREEN, (px, py, pw, ph), radius=8, alpha=0, width=1)
            badge = self.fonts["tiny"].render("✓  ACCÈS COMPLET", True, C_GREEN)
            surf.blit(badge, badge.get_rect(center=(cx, py + 16)))
            sub = self.fonts["tiny"].render("Jeu débloqué", True, C_TEAL)
            surf.blit(sub, sub.get_rect(center=(cx, py + 34)))
        else:
            remaining = self._trial_remaining
            # Border colour shifts green → orange → red
            if remaining > 1:
                border_col = C_GREEN
            elif remaining == 1:
                border_col = C_ORANGE
            else:
                border_col = C_RED
            draw_glow_rect(surf, border_col, (px, py, pw, ph), radius=8, alpha=0, width=1)

            # Label
            lbl = self.fonts["tiny"].render("ESSAIS GRATUITS", True, C_GREY)
            surf.blit(lbl, lbl.get_rect(center=(cx, py + 11)))

            # Dot indicators
            dot_r   = 6
            spacing = dot_r * 2 + 5
            total_w = self._trial_max * spacing - 5
            dot_x0  = cx - total_w // 2 + dot_r
            dot_y   = py + 36
            for i in range(self._trial_max):
                used = i >= remaining
                col  = C_DARK_GREY if used else border_col
                # Glow for active dots
                if not used:
                    glow = pygame.Surface((dot_r * 4, dot_r * 4), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*col, 40),
                                       (dot_r * 2, dot_r * 2), dot_r * 2)
                    surf.blit(glow, (dot_x0 + i * spacing - dot_r * 2,
                                     dot_y - dot_r * 2))
                pygame.draw.circle(surf, col,
                                   (dot_x0 + i * spacing, dot_y), dot_r)
                pygame.draw.circle(surf, C_WHITE if not used else C_DARK_GREY,
                                   (dot_x0 + i * spacing, dot_y), dot_r, 1)

            # Numeric label to the right of dots
            num_col = C_WHITE if remaining > 0 else C_RED
            num_t = self.fonts["tiny"].render(
                f"{remaining}/{self._trial_max}", True, num_col)
            surf.blit(num_t, (dot_x0 + self._trial_max * spacing + 4,
                               dot_y - num_t.get_height() // 2))

    def _draw_leaderboard(self, surf):
        RANK_COLORS = [C_YELLOW, (200, 200, 200), C_ORANGE]  # or, argent, bronze
        RANK_MEDALS = ["1", "2", "3"]

        entries  = self._leaderboard_entries
        n        = len(entries)
        ROW_H    = 24
        PAD      = 12
        TITLE_H  = 42   # space for title + status dot
        EMPTY_H  = 38   # shown when no entries yet

        lw = 230
        lh = TITLE_H + (n * ROW_H if n else EMPTY_H) + PAD
        lx = SCREEN_W - lw - 10
        ly = 100

        # ── Panel background + border ────────────────────────────────────
        draw_glow_rect(surf, C_DARK_GREY, (lx, ly, lw, lh), radius=8, alpha=170)
        draw_glow_rect(surf, C_CYAN,      (lx, ly, lw, lh), radius=8, alpha=0, width=1)

        # ── Title row ────────────────────────────────────────────────────
        cx = lx + lw // 2
        title_surf = self.fonts["tiny"].render("MEILLEURS SCORES", True, C_CYAN)
        surf.blit(title_surf, title_surf.get_rect(center=(cx, ly + 12)))

        # Status indicator dot
        status_color = {
            "ok":      C_GREEN,
            "loading": C_YELLOW,
            "error":   C_RED,
        }.get(self._leaderboard_status, C_GREY)
        status_label = {
            "ok":      "sauvegarde active",
            "loading": "chargement...",
            "error":   "erreur base de donnees",
        }.get(self._leaderboard_status, "...")
        pygame.draw.circle(surf, status_color, (lx + PAD + 4, ly + 30), 4)
        st = self.fonts["tiny"].render(status_label, True, status_color)
        surf.blit(st, (lx + PAD + 14, ly + 23))

        # ── Separator ────────────────────────────────────────────────────
        sep_y = ly + TITLE_H - 2
        s = pygame.Surface((lw - PAD * 2, 1), pygame.SRCALPHA)
        s.fill((*C_CYAN, 60))
        surf.blit(s, (lx + PAD, sep_y))

        # ── Empty state ──────────────────────────────────────────────────
        if not entries:
            msg = self.fonts["tiny"].render("Aucun score enregistre", True, C_GREY)
            surf.blit(msg, msg.get_rect(center=(cx, sep_y + EMPTY_H // 2 + 4)))
            return

        # ── Score rows ───────────────────────────────────────────────────
        row_y = sep_y + 6
        for i, entry in enumerate(entries):
            # Alternate row tint
            if i % 2 == 0:
                row_bg = pygame.Surface((lw - 4, ROW_H - 2), pygame.SRCALPHA)
                row_bg.fill((255, 255, 255, 8))
                surf.blit(row_bg, (lx + 2, row_y))

            col = RANK_COLORS[i] if i < 3 else C_GREY

            # Rank number
            rank_str = f"{i+1}."
            rt = self.fonts["tiny"].render(rank_str, True, col)
            surf.blit(rt, (lx + PAD, row_y + 4))

            # Player name
            raw_name  = entry.get("name", "???")[:12]
            nt = self.fonts["tiny"].render(raw_name, True, C_WHITE)
            surf.blit(nt, (lx + PAD + 28, row_y + 4))

            # Score (right-aligned)
            score_str = f"{entry.get('score', 0):,}".replace(",", " ")
            sc_t = self.fonts["tiny"].render(score_str, True, col)
            surf.blit(sc_t, (lx + lw - PAD - sc_t.get_width(), row_y + 4))

            row_y += ROW_H


class PauseScreen:
    def __init__(self, fonts):
        self.fonts = fonts
        self.escape_released = False

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
                    self.escape_released = False
                    return "resume", 0
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_ESCAPE and self.escape_released:
                    if hold_timer < 120:
                        self.escape_released = False
                        return "resume", 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            hold_timer += 1
            if hold_timer >= 120:
                self.escape_released = False
                return "menu", 0
        else:
            self.escape_released = True
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
    MAX_NAME_LEN = 10

    def __init__(self, fonts):
        self.fonts = fonts
        self.t = 0
        self.name_input  = ""
        self.name_done   = False   # True once player confirmed name
        self.submitted   = False
        self.victory     = False

    def reset(self):
        self.t          = 0
        self.name_input  = ""
        self.name_done   = False
        self.submitted   = False
        self.victory     = False

    def update(self, events):
        self.t += 1
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                    
                if not self.name_done:
                    if ev.key == pygame.K_RETURN:
                        if len(self.name_input.strip()) > 0:
                            self.name_done = True
                    elif ev.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif len(self.name_input) < self.MAX_NAME_LEN:
                        ch = ev.unicode
                        if ch and ch.isprintable() and ch not in ("/", "\\", "'", '"'):
                            self.name_input += ch
                else:
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return "restart"
        return None

    def draw(self, surf, score, highscore, wave, kills, shots, max_combo, new_record):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((25, 0, 0, 185))
        surf.blit(overlay, (0, 0))

        # GAME OVER / VICTORY
        if getattr(self, "victory", False):
            draw_neon_text(surf, "VICTOIRE !", self.fonts["big"], C_GREEN, SCREEN_W//2, 100)
        else:
            draw_neon_text(surf, "GAME  OVER", self.fonts["big"], C_RED, SCREEN_W//2, 100)

        # Score
        draw_neon_text(surf, f"SCORE  {score:07d}", self.fonts["medium"],
                       C_YELLOW, SCREEN_W//2, 158)
        if new_record:
            if (self.t // 20) % 2 == 0:
                draw_neon_text(surf, "✦  NOUVEAU RECORD !  ✦", self.fonts["medium"],
                               C_GREEN, SCREEN_W//2, 191)
        else:
            t = self.fonts["small"].render(f"Meilleur : {highscore:07d}", True, C_DARK_CYAN)
            surf.blit(t, t.get_rect(center=(SCREEN_W//2, 191)))

        # Stats
        stats = [
            (f"Vague atteinte",  str(wave),      C_CYAN),
            (f"Ennemis tués",    str(kills),     C_GREEN),
            (f"Tirs effectués",  str(shots),     C_YELLOW),
            (f"Meilleur combo",  f"x{max_combo}", C_ORANGE),
        ]
        y0 = 220
        bx, bw, bh = SCREEN_W//2 - 140, 280, 28
        draw_glow_rect(surf, C_DARK_GREY, (bx-10, y0-6, bw+20, len(stats)*bh+12), radius=8, alpha=60)
        for label, value, color in stats:
            tl = self.fonts["small"].render(label, True, C_GREY)
            tv = self.fonts["small"].render(value, True, color)
            surf.blit(tl, (bx, y0 + 2))
            surf.blit(tv, (bx + bw - tv.get_width(), y0 + 2))
            y0 += bh

        # ── Name entry / leaderboard submit ─────────────────────────────
        y0 += 14
        if not self.name_done:
            prompt_col = C_CYAN if (self.t // 20) % 2 == 0 else C_WHITE
            draw_text_centered(surf, "Entrez votre nom : ", self.fonts["small"], C_WHITE, y0)
            y0 += 26
            display_name = self.name_input + ("|" if (self.t // 15) % 2 == 0 else " ")
            draw_glow_rect(surf, C_DARK_GREY, (SCREEN_W//2 - 100, y0 - 4, 200, 32),
                           radius=6, alpha=140, width=1)
            draw_neon_text(surf, display_name or " ", self.fonts["medium"],
                           prompt_col, SCREEN_W//2, y0 + 12)
            y0 += 42
            if len(self.name_input.strip()) > 0:
                draw_text_centered(surf, "ENTRÉE pour confirmer le score", self.fonts["tiny"], C_CYAN, y0)
            else:
                draw_text_centered(surf, "Veuillez entrer un nom", self.fonts["tiny"], C_RED, y0)
        else:
            if self.submitted:
                draw_text_centered(surf, f"✓ {self.name_input} — score soumis !",
                                   self.fonts["small"], C_GREEN, y0)
            else:
                if len(self.name_input.strip()) > 0:
                    draw_text_centered(surf, f"Joueur : {self.name_input}",
                                       self.fonts["small"], C_CYAN, y0)
                else:
                    draw_text_centered(surf, "Score non sauvegardé",
                                       self.fonts["small"], C_GREY, y0)
            y0 += 32
            if (self.t // 28) % 2 == 0:
                draw_text_centered(surf, "ENTRÉE / ESPACE  →  Rejouer",
                                   self.fonts["medium"], C_WHITE, y0)
            draw_text_centered(surf, "ÉCHAP  →  Menu principal",
                               self.fonts["small"], C_GREY, y0 + 34)


class PaywallScreen:
    """
    Écran de paywall affiché après MAX_FREE_PLAYS essais gratuits.
    Gère : affichage, ouverture du lien de paiement, polling du statut.
    Retourne :
      "unlocked"  → paiement confirmé, lancer la partie
      "menu"      → retour menu (ÉCHAP)
    """

    # États internes
    ST_IDLE       = "idle"        # Avant que le joueur clique sur Payer
    ST_WAITING    = "waiting"     # Lien ouvert, on attend la confirmation
    ST_CHECKING   = "checking"    # Poll en cours (thread)
    ST_CONFIRMED  = "confirmed"   # Paiement OK

    def __init__(self, fonts):
        self.fonts = fonts
        self.reset()

    def reset(self):
        self.t            = 0
        self.state        = self.ST_IDLE
        self.pay_url      = None
        self.payment_ref  = None
        self.cash_code    = None
        self._check_timer = 0
        self._error_msg   = None
        self._init_thread = None
        self._cash_copied = False   # True après avoir copié le code
        self._copy_flash  = 0       # frames restantes pour le flash "Copié !"

    # ── Démarrage : on initialise le paiement en arrière-plan ────────────
    def start(self):
        """Appelé par Game juste avant de switcher sur cet écran."""
        self.reset()
        self._init_thread = threading.Thread(target=self._bg_init_payment, daemon=True)
        self._init_thread.start()

    def _bg_init_payment(self):
        """Thread : récupère l'URL de paiement depuis Konnect."""
        try:
            url, ref, cash = init_payment()   # lit KONNECT_AMOUNT depuis constants
            self.pay_url     = url
            self.payment_ref = ref
            self.cash_code   = cash
        except Exception as e:
            self._error_msg = str(e)

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, events):
        self.t += 1
        if self._copy_flash > 0:
            self._copy_flash -= 1

        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"

                # ENTRÉE / ESPACE → ouvrir le lien de paiement
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.state == self.ST_IDLE and self.pay_url:
                        webbrowser.open(self.pay_url)
                        self.state = self.ST_WAITING
                        self._check_timer = 0

                # C → copier le cash_code dans le presse-papier
                if ev.key == pygame.K_c and self.cash_code:
                    try:
                        pygame.scrap.init()
                        pygame.scrap.put(pygame.SCRAP_TEXT,
                                         self.cash_code.encode("utf-8"))
                    except Exception:
                        # Fallback : subprocess xclip/xsel sur Linux
                        try:
                            import subprocess
                            subprocess.run(["xclip", "-selection", "clipboard"],
                                           input=self.cash_code.encode(), check=False)
                        except Exception:
                            pass
                    self._cash_copied = True
                    self._copy_flash  = 120   # 2 secondes

                # V → saisir le code manuellement (reçu par email)
                if ev.key == pygame.K_v:
                    return "code_entry"

                # R → relancer le polling manuellement
                if ev.key == pygame.K_r and self.state == self.ST_WAITING:
                    self._poll_once()

        # Polling automatique toutes les 3 secondes quand on attend
        if self.state == self.ST_WAITING:
            self._check_timer += 1
            if self._check_timer >= 180:   # 3s à 60 FPS
                self._check_timer = 0
                self._poll_once()

        if self.state == self.ST_CONFIRMED:
            return "unlocked"

        return None

    def _poll_once(self):
        """Lance un thread de vérification du paiement (non bloquant)."""
        if self.payment_ref:
            threading.Thread(target=self._bg_check_status, daemon=True).start()

    def _bg_check_status(self):
        completed, cash = check_payment_status(self.payment_ref)
        if completed:
            self.state = self.ST_CONFIRMED

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, surf):
        # Overlay sombre
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 215))
        surf.blit(overlay, (0, 0))

        cx = SCREEN_W // 2

        # ── Titre ────────────────────────────────────────────────────────
        pulse_col = C_YELLOW if (self.t // 30) % 2 == 0 else C_ORANGE
        draw_neon_text(surf, "ESSAIS GRATUITS ÉPUISÉS",
                       self.fonts["big"], pulse_col, cx, 72)

        lines = [
            f"Vous avez utilisé vos {MAX_FREE_PLAYS} parties gratuites.",
            "Débloquez l'accès complet pour continuer à jouer.",
        ]
        y = 128
        for line in lines:
            t = self.fonts["small"].render(line, True, C_WHITE)
            surf.blit(t, t.get_rect(center=(cx, y)))
            y += 26

        # ─────────────────────────────────────────────────────────────────
        # Layout : si cash_code disponible, deux colonnes côte à côte.
        # Sinon, panel unique centré.
        # ─────────────────────────────────────────────────────────────────
        panel_top = y + 10
        has_cash  = bool(self.cash_code)

        if has_cash:
            # ── Colonne gauche : paiement en ligne ───────────────────────
            lw, lh = 390, 210
            lx     = cx - lw - 8
            self._draw_online_panel(surf, lx, panel_top, lw, lh, cx_hint=lx + lw // 2)

            # ── Colonne droite : Wafacash / espèces ──────────────────────
            rw, rh = 390, 210
            rx     = cx + 8
            self._draw_cash_panel(surf, rx, panel_top, rw, rh)
        else:
            # ── Panel unique centré ───────────────────────────────────────
            pw, ph = 480, 220
            px = cx - pw // 2
            self._draw_online_panel(surf, px, panel_top, pw, ph, cx_hint=cx)

        # ── Pied de page ──────────────────────────────────────────────────
        footer_y = panel_top + (210 if has_cash else 220) + 18
        if has_cash:
            draw_text_centered(surf,
                "[ C ] Copier code  ·  [ ENTRÉE ] Paiement carte  ·  [ R ] Vérifier paiement espèces",
                self.fonts["tiny"], C_CYAN, footer_y)
            draw_text_centered(surf, "ÉCHAP  →  Retour au menu",
                self.fonts["tiny"], C_GREY, footer_y + 18)
        else:
            draw_text_centered(surf, "ÉCHAP  →  Retour au menu",
                self.fonts["tiny"], C_GREY, footer_y)

    # ── Sous-panel : paiement en ligne ────────────────────────────────────
    def _draw_online_panel(self, surf, px, py, pw, ph, cx_hint):
        draw_glow_rect(surf, C_DARK_GREY, (px, py, pw, ph), radius=10, alpha=160)
        draw_glow_rect(surf, C_CYAN,      (px, py, pw, ph), radius=10, alpha=0, width=1)

        cx = cx_hint
        inner_y = py + 14

        if self.state == self.ST_IDLE:
            if self.pay_url is None and self._error_msg is None:
                dots = "." * (1 + (self.t // 20) % 3)
                msg = self.fonts["small"].render(f"Connexion{dots}", True, C_GREY)
                surf.blit(msg, msg.get_rect(center=(cx, py + ph // 2)))
                return

            if self._error_msg:
                err = self.fonts["small"].render("Erreur réseau.", True, C_RED)
                surf.blit(err, err.get_rect(center=(cx, py + ph // 2)))
                return

            # Lien prêt
            draw_neon_text(surf, "PAIEMENT EN LIGNE", self.fonts["small"], C_CYAN, cx, inner_y + 6)
            inner_y += 30

            price_t = self.fonts["big"].render("0,10 TND", True, C_YELLOW)
            surf.blit(price_t, price_t.get_rect(center=(cx, inner_y)))
            inner_y += 46

            # Séparateur
            sep = pygame.Surface((pw - 30, 1), pygame.SRCALPHA)
            sep.fill((*C_CYAN, 40))
            surf.blit(sep, (px + 15, inner_y))
            inner_y += 10

            hint = self.fonts["tiny"].render("Carte bancaire · Paiement sécurisé Konnect", True, C_GREY)
            surf.blit(hint, hint.get_rect(center=(cx, inner_y)))
            inner_y += 24

            btn_col = C_GREEN if (self.t // 25) % 2 == 0 else C_TEAL
            bw = pw - 40
            draw_glow_rect(surf, btn_col, (px + 20, inner_y, bw, 38), radius=8, alpha=50, width=2)
            btn_t = self.fonts["medium"].render("[ ENTRÉE ]  Ouvrir", True, btn_col)
            surf.blit(btn_t, btn_t.get_rect(center=(cx, inner_y + 19)))

        elif self.state == self.ST_WAITING:
            draw_neon_text(surf, "EN ATTENTE...", self.fonts["small"], C_CYAN, cx, inner_y + 6)
            inner_y += 32
            spinner = ["◐", "◓", "◑", "◒"][(self.t // 10) % 4]
            sp_t = self.fonts["big"].render(spinner, True, C_YELLOW)
            surf.blit(sp_t, sp_t.get_rect(center=(cx, inner_y + 14)))
            inner_y += 50
            for line in ("Paiement en cours dans le navigateur.",
                         "", "[ R ]  Vérifier maintenant"):
                col = C_CYAN if line.startswith("[") else C_WHITE
                t = self.fonts["tiny"].render(line, True, col)
                surf.blit(t, t.get_rect(center=(cx, inner_y)))
                inner_y += 18

        elif self.state == self.ST_CONFIRMED:
            draw_neon_text(surf, "✓  CONFIRMÉ !", self.fonts["medium"], C_GREEN, cx, py + ph // 2 - 10)
            ok_t = self.fonts["tiny"].render("Lancement...", True, C_WHITE)
            surf.blit(ok_t, ok_t.get_rect(center=(cx, py + ph // 2 + 26)))

    # ── Sous-panel : Wafacash / paiement en espèces ───────────────────────
    def _draw_cash_panel(self, surf, px, py, pw, ph):
        # Bordure orange Wafacash
        draw_glow_rect(surf, C_DARK_GREY, (px, py, pw, ph), radius=10, alpha=160)
        draw_glow_rect(surf, C_ORANGE,    (px, py, pw, ph), radius=10, alpha=0, width=1)

        cx     = px + pw // 2
        PAD    = 14
        inner_y = py + PAD

        # ── En-tête ───────────────────────────────────────────────────────
        draw_neon_text(surf, "PAIEMENT EN ESPÈCES",
                       self.fonts["small"], C_ORANGE, cx, inner_y + 6)
        inner_y += 26
        wf_t = self.fonts["tiny"].render("Wafacash  ·  0,10 TND", True, C_GREY)
        surf.blit(wf_t, wf_t.get_rect(center=(cx, inner_y)))
        inner_y += 16

        sep = pygame.Surface((pw - 24, 1), pygame.SRCALPHA)
        sep.fill((*C_ORANGE, 50))
        surf.blit(sep, (px + 12, inner_y))
        inner_y += 8

        # ── Étape 1 : noter / copier le code ─────────────────────────────
        lbl1 = self.fonts["tiny"].render("① NOTEZ CE CODE :", True, C_ORANGE)
        surf.blit(lbl1, (px + PAD, inner_y))
        inner_y += 16

        # Boîte du code
        code_bw = pw - PAD * 2
        code_bh = 32
        draw_glow_rect(surf, (8, 8, 28),
                       (px + PAD, inner_y, code_bw, code_bh), radius=6, alpha=230)
        draw_glow_rect(surf, C_ORANGE,
                       (px + PAD, inner_y, code_bw, code_bh), radius=6, alpha=0, width=1)

        code_col = C_GREEN if self._copy_flash > 0 else C_YELLOW
        code_t   = self.fonts["medium"].render(self.cash_code or "", True, code_col)
        # code centré légèrement à gauche pour laisser place au bouton copier
        surf.blit(code_t, code_t.get_rect(
            center=(px + PAD + (code_bw - 52) // 2, inner_y + code_bh // 2)))

        # Bouton [ C ] copier
        copy_col = C_GREEN if self._copy_flash > 0 else C_GREY
        copy_str = "✓" if self._copy_flash > 0 else "[ C ]"
        cp_t = self.fonts["tiny"].render(copy_str, True, copy_col)
        surf.blit(cp_t, (px + PAD + code_bw - cp_t.get_width() - 5,
                          inner_y + (code_bh - cp_t.get_height()) // 2))
        inner_y += code_bh + 8

        # ── Étape 2 : aller à l'agence ────────────────────────────────────
        steps = [
            ("②", "Rendez-vous dans une agence Wafacash"),
            ("③", "Montrez le code à l'agent et payez"),
        ]
        for num, txt in steps:
            n_t = self.fonts["tiny"].render(num, True, C_ORANGE)
            s_t = self.fonts["tiny"].render(txt, True, C_WHITE)
            surf.blit(n_t, (px + PAD,     inner_y))
            surf.blit(s_t, (px + PAD + 18, inner_y))
            inner_y += 15

        # ── Séparateur ────────────────────────────────────────────────────
        inner_y += 4
        sep2 = pygame.Surface((pw - 24, 1), pygame.SRCALPHA)
        sep2.fill((*C_ORANGE, 35))
        surf.blit(sep2, (px + 12, inner_y))
        inner_y += 8

        # ── Étape 4 : revenu de l'agence — appuyer sur R ─────────────────
        lbl4_col = C_CYAN if (self.t // 25) % 2 == 0 else C_WHITE
        lbl4 = self.fonts["tiny"].render(
            "④ Une fois payé, revenez ici et appuyez sur :", True, C_GREY)
        surf.blit(lbl4, lbl4.get_rect(center=(cx, inner_y)))
        inner_y += 15

        # Gros bouton R
        rbw, rbh = 200, 28
        rbx = cx - rbw // 2
        draw_glow_rect(surf, lbl4_col, (rbx, inner_y, rbw, rbh),
                       radius=6, alpha=35, width=2)
        rb_t = self.fonts["small"].render("[ R ]  Vérifier le paiement", True, lbl4_col)
        surf.blit(rb_t, rb_t.get_rect(center=(cx, inner_y + rbh // 2)))
        inner_y += rbh + 6

        # ── Avertissement délai ───────────────────────────────────────────
        warn_col = C_ORANGE if (self.t // 40) % 2 == 0 else (170, 90, 0)
        w_t = self.fonts["tiny"].render("⚠  À effectuer dans les 24h", True, warn_col)
        surf.blit(w_t, w_t.get_rect(center=(cx, inner_y)))

        # ── Bouton : saisir code ───────────────────────────────────────────
        inner_y += 18
        v_col = C_CYAN if (self.t // 30) % 2 == 0 else C_WHITE
        draw_glow_rect(surf, v_col, (px + 20, inner_y, pw - 40, 26), radius=6, alpha=20, width=1)
        v_t = self.fonts["tiny"].render("[ V ]  J'ai déjà payé — saisir mon code", True, v_col)
        surf.blit(v_t, v_t.get_rect(center=(cx, inner_y + 13)))


class CodeEntryScreen:
    """
    Interface permettant de coller/saisir le code de paiement reçu par email.
    Valide via l'API Konnect en arrière-plan.
    Retourne :
      "unlocked"  → code valide, paiement confirmé
      "back"      → retour au paywall (ÉCHAP)
    """

    def __init__(self, fonts):
        self.fonts = fonts
        self.reset()

    def reset(self):
        self.t = 0
        self.code_input = ""
        self.status = "idle"   # idle | checking | error | success
        self.error_msg = ""
        self._check_thread = None
        self._success_t = 0

    def update(self, events):
        self.t += 1
        for ev in events:
            if ev.type == pygame.KEYDOWN:

                if ev.key == pygame.K_ESCAPE:
                    if self.status != "checking":
                        return "back"

                elif ev.key == pygame.K_RETURN:
                    if self.status == "checking":
                        pass  # attendre le thread
                    elif self.status != "success":
                        if len(self.code_input.strip()) >= 6:
                            self._start_check(self.code_input.strip())
                        else:
                            self.status = "error"
                            self.error_msg = "Code trop court (min. 6 chiffres)."

                elif ev.key == pygame.K_BACKSPACE:
                    if self.status not in ("checking", "success"):
                        self.code_input = self.code_input[:-1]
                        self.status = "idle"

                elif ev.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if self.status not in ("checking", "success"):
                        text = _get_clipboard_text()
                        for char in text:
                            if char.isdigit() and len(self.code_input) < 20:
                                self.code_input += char
                        # Remettre en idle pour éviter déclenchement accidentel
                        if self.status == "error":
                            self.status = "idle"
                        break  # ignorer les autres events du même frame

                else:
                    if self.status not in ("checking", "success") and len(self.code_input) < 20:
                        ch = ev.unicode
                        if ch and ch.isdigit():
                            self.code_input += ch

        if self.status == "success":
            if self.t >= self._success_t + 90:  # ~1.5s d'animation
                return "unlocked"

        return None

    def _start_check(self, code):
        """Lance la validation Konnect en arrière-plan."""
        self.status = "checking"
        self._success_t = 0
        self._check_thread = threading.Thread(
            target=self._bg_validate, args=(code,), daemon=True
        )
        self._check_thread.start()

    def _bg_validate(self, code):
        try:
            ok = validate_cash_code(code)
        except Exception as e:
            print("[CodeEntry] erreur:", e)
            ok = False

        if ok:
            self.status = "success"
            self._success_t = self.t
        else:
            self.status = "error"
            self.error_msg = "Code invalide ou paiement non confirmé."

    def draw(self, surf):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 40, 235))
        surf.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        draw_neon_text(surf, "VALIDATION DU CODE", self.fonts["big"], C_CYAN, cx, 100)

        y = 175
        msg = "Entrez le code de paiement reçu par email :"
        t = self.fonts["small"].render(msg, True, C_WHITE)
        surf.blit(t, t.get_rect(center=(cx, y)))

        # ── Boîte de saisie ───────────────────────────────────────────────
        y += 55
        bw, bh = 420, 54
        bx = cx - bw // 2
        border_col = (
            C_GREEN  if self.status == "success"  else
            C_RED    if self.status == "error"    else
            C_YELLOW if self.status == "checking" else
            C_CYAN
        )
        draw_glow_rect(surf, C_DARK_GREY, (bx, y, bw, bh), radius=8, alpha=150)
        draw_glow_rect(surf, border_col,  (bx, y, bw, bh), radius=8, alpha=0, width=2)

        if self.status == "checking":
            spinner = ["◐", "◓", "◑", "◒"][(self.t // 8) % 4]
            sp = self.fonts["medium"].render(spinner, True, C_YELLOW)
            surf.blit(sp, sp.get_rect(center=(cx, y + bh // 2)))
        else:
            cursor = "|" if (self.t // 20) % 2 == 0 and self.status == "idle" else ""
            txt_surf = self.fonts["medium"].render(
                (self.code_input + cursor) or " ", True, C_YELLOW)
            surf.blit(txt_surf, txt_surf.get_rect(center=(cx, y + bh // 2)))

        # ── Statut ────────────────────────────────────────────────────────
        y += 80
        if self.status == "error":
            err = self.fonts["small"].render(f"✗  {self.error_msg}", True, C_RED)
            surf.blit(err, err.get_rect(center=(cx, y)))
            y += 28
            retry = self.fonts["tiny"].render(
                "Modifiez le code et réessayez", True, C_GREY)
            surf.blit(retry, retry.get_rect(center=(cx, y)))
        elif self.status == "checking":
            chk = self.fonts["small"].render("Vérification en cours...", True, C_YELLOW)
            surf.blit(chk, chk.get_rect(center=(cx, y)))
        elif self.status == "success":
            ok = self.fonts["medium"].render("✓  CODE VALIDÉ !  Démarrage...", True, C_GREEN)
            surf.blit(ok, ok.get_rect(center=(cx, y)))
        else:
            for line in [
                "Ctrl+V  pour coller  |  ENTRÉE pour valider",
                "Le code est dans votre email de confirmation Wafacash",
            ]:
                hint = self.fonts["tiny"].render(line, True, C_GREY)
                surf.blit(hint, hint.get_rect(center=(cx, y)))
                y += 22

        draw_text_centered(surf, "ÉCHAP  →  Retour", self.fonts["tiny"], C_GREY, SCREEN_H - 40)
