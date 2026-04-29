
import pygame
import math
import random
import os

from src.constants import *
from src.utils import (load_json, save_json, create_sounds, draw_neon_text,
                        draw_text_centered, dist)
from src.effects  import StarField, Nebula, EffectManager
from src.player   import Player
from src.enemies  import Boss, SplitterEnemy, EnemyBullet
from src.systems  import WaveManager, ScoreSystem, PowerUp, HUD
from src.screens  import (MenuScreen, PauseScreen, WaveTransitionScreen, GameOverScreen, PaymentScreen)


class Game:
    # ── États ─────────────────────────────────────────────────────────────
    S_MENU       = "menu"
    S_PLAY       = "play"
    S_PAUSE      = "pause"
    S_WAVE_TRANS = "wave_trans"
    S_GAMEOVER   = "gameover"
    S_PAYMENT    = "payment"

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.fonts = {
            "title":  pygame.font.SysFont("consolas", 64, bold=True),
            "big":    pygame.font.SysFont("consolas", 44, bold=True),
            "medium": pygame.font.SysFont("consolas", 26, bold=True),
            "small":  pygame.font.SysFont("consolas", 18),
            "tiny":   pygame.font.SysFont("consolas", 13),
        }

        # Persistance
        data = load_json(HIGHSCORE_FILE, {})
        self.highscore = data.get("highscore", 0)

        settings = load_json(SETTINGS_FILE, {})
        self.games_played = settings.get("games_played", 0)
        self.unlocked = settings.get("unlocked", False)

        # Sons
        self.sounds = create_sounds()

        # ── Sons & musique depuis fichiers ───────────────────────────────
        # Son de game over personnalisé (assets/sounds/gameover.*)
        self._gameover_sound = self._load_sound_file("assets/sounds/gameover")
        # Son d'avertissement (2e vie perdue) — assets/sounds/warning.*
        self._warning_sound = self._load_sound_file("assets/sounds/warning")
        # Musique de jeu (assets/music/bgm.*)
        self._bgm_path = self._find_audio_file("assets/music/bgm")
        self._bgm_playing = False

        # Fond partagé
        self.stars  = StarField(170)
        self.nebula = Nebula(7)

        # Écrans
        self.menu_screen  = MenuScreen(self.fonts, self.highscore)
        self.pause_screen = PauseScreen(self.fonts)
        self.wave_screen  = WaveTransitionScreen(self.fonts)
        self.go_screen    = GameOverScreen(self.fonts)
        self.payment_screen = PaymentScreen(self.fonts)

        self.state = self.S_MENU
        self.pause_hold_timer = 0
        self.diff_speed = 1.0
        self.new_record = False

        self._init_session()

    # ── Initialisation d'une partie ──────────────────────────────────────

    def _init_session(self):
        self.player   = Player()
        self.enemies  = []
        self.p_bullets: list = []
        self.e_bullets: list = []
        self.powerups : list = []
        self.fx       = EffectManager()
        self.wave_mgr = WaveManager()
        self.score_sys = ScoreSystem(self.highscore)
        self.hud       = HUD()
        self.boss      = None
        self.enemy_shoot_timer = 40
        self.new_record = False

    # ── Son ──────────────────────────────────────────────────────────────

    def snd(self, name):
        s = self.sounds.get(name)
        if s:
            try: s.play()
            except: pass

    def _find_audio_file(self, base_path):
        """Cherche un fichier audio avec différentes extensions."""
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            path = base_path + ext
            if os.path.exists(path):
                return path
        return None

    def _load_sound_file(self, base_path):
        """Charge un son depuis un fichier (plusieurs extensions supportées)."""
        path = self._find_audio_file(base_path)
        if path:
            try:
                return pygame.mixer.Sound(path)
            except Exception:
                pass
        return None

    def _start_bgm(self):
        """Lance la musique de fond si disponible."""
        if self._bgm_path and not self._bgm_playing:
            try:
                pygame.mixer.music.load(self._bgm_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)  # boucle infinie
                self._bgm_playing = True
            except Exception:
                pass

    def _stop_bgm(self):
        """Arrête la musique de fond."""
        if self._bgm_playing:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self._bgm_playing = False

    def _play_gameover_sound(self):
        """Joue le son de game over personnalisé, sinon le son synthétique."""
        if self._gameover_sound:
            try:
                self._gameover_sound.play()
                return
            except Exception:
                pass
        self.snd("gameover")

    def _play_warning_sound(self):
        """Joue le son d'avertissement (2e strike), sinon le son synthétique."""
        if self._warning_sound:
            try:
                self._warning_sound.play()
                return
            except Exception:
                pass
        self.snd("warning")

    # ── Boucle principale ────────────────────────────────────────────────

    def run(self):
        while True:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self._save_and_quit()
            self._update(events)
            self._draw()
            self.clock.tick(FPS)

    # ── UPDATE ───────────────────────────────────────────────────────────

    def _update(self, events):
        spd_mult = 1.0 + (self.wave_mgr.wave - 1) * 0.08
        self.stars.update(speed=(1.5 + self.wave_mgr.wave * 0.15) * self.diff_speed)
        self.nebula.update()

        if self.state == self.S_MENU:
            result = self.menu_screen.update(events)
            if result:
                action, param = result
                if action == "start":
                    if not self.unlocked and self.games_played >= MAX_FREE_PLAYS:
                        self.state = self.S_PAYMENT
                        self.payment_screen.status = "idle"
                    else:
                        self.diff_speed = param
                        self._init_session()
                        self.state = self.S_PLAY
                        self.snd("wave_start")
                        self._start_bgm()

        elif self.state == self.S_PLAY:
            self._update_play(events)

        elif self.state == self.S_PAUSE:
            result, self.pause_hold_timer = self.pause_screen.update(events, self.pause_hold_timer)
            if result == "resume":
                self.state = self.S_PLAY
            elif result == "menu":
                self.state = self.S_MENU
                self._save_highscore()
                self._stop_bgm()

        elif self.state == self.S_WAVE_TRANS:
            done = self.wave_screen.update()
            if done:
                self.state = self.S_PLAY

        elif self.state == self.S_GAMEOVER:
            result = self.go_screen.update(events)
            if result == "restart":
                self._init_session()
                self.state = self.S_PLAY
                self.snd("wave_start")
                self._start_bgm()
            elif result == "menu":
                self.state = self.S_MENU
                
        elif self.state == self.S_PAYMENT:
            result = self.payment_screen.update(events)
            if result == "menu":
                self.state = self.S_MENU
            elif result == "success":
                self.unlocked = True
                self._save_settings()
                self.state = self.S_MENU

    def _update_play(self, events):
        # Pause
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p:
                self.state = self.S_PAUSE
                self.pause_hold_timer = 0
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.state = self.S_PAUSE
                self.pause_hold_timer = 0
                return

        # Joueur
        self.player.handle_input(events)
        self.player.update()

        # Tir joueur
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            new_bullets = self.player.get_bullets()
            if new_bullets:
                self.p_bullets.extend(new_bullets)
                self.snd("laser" if self.player.has_laser_shot else "shoot")

        # Balles joueur
        for b in self.p_bullets: b.update()
        self.p_bullets = [b for b in self.p_bullets if b.active]

        # Ennemis
        self.wave_mgr.update(self.enemies)
        new_e_bullets = []
        new_spawns    = []
        for e in self.enemies:
            e.update()
            if isinstance(e, Boss):
                self.boss = e
            # Tir ennemis
            bullets = e.get_bullets(self.player.x, self.player.y)
            new_e_bullets.extend(bullets)
            # Boss spawns
            if isinstance(e, Boss):
                spawns = e.get_spawns()
                new_spawns.extend(spawns)
                # Laser FX
                if e.laser_charging and e.laser_timer < 5:
                    self.fx.laser(e.x, e.y, *e.laser_target)

        self.enemies.extend(new_spawns)
        self.enemies = [e for e in self.enemies if e.active]

        # Suivi boss actif
        active_bosses = [e for e in self.enemies if isinstance(e, Boss)]
        self.boss = active_bosses[0] if active_bosses else None

        # Balles ennemies
        self.e_bullets.extend(new_e_bullets)
        for b in self.e_bullets:
            b.update(self.player.x, self.player.y)
        self.e_bullets = [b for b in self.e_bullets if b.active]

        # Power-ups
        for p in self.powerups: p.update()
        self.powerups = [p for p in self.powerups if p.active]

        # Collisions
        self._check_collisions()

        # Effets
        self.fx.update()
        self.score_sys.update()

        # Fin de vague
        if self.wave_mgr.check_wave_complete(self.enemies):
            self.snd("wave_start")
            next_wave = self.wave_mgr.wave + 1
            self.wave_screen.start(next_wave)
            self.state = self.S_WAVE_TRANS

        # Game over
        if self.player.lives <= 0:
            if not self.unlocked:
                self.games_played += 1
                self._save_settings()
                
            if self.score_sys.score > self.highscore:
                self.highscore = self.score_sys.score
                self.new_record = True
                self._save_highscore()
            self._stop_bgm()
            self._play_gameover_sound()
            self.fx.screen_flash(C_RED, alpha=120, decay=5)
            self.state = self.S_GAMEOVER

    # ── COLLISIONS ───────────────────────────────────────────────────────

    def _check_collisions(self):
        px, py = self.player.x, self.player.y
        pr     = self.player.radius

        # Balles joueur ↔ ennemis
        for b in list(self.p_bullets):
            if not b.active:
                continue
            for e in list(self.enemies):
                if not e.active:
                    continue
                if dist(b.x, b.y, e.x, e.y) < b.radius + e.radius:
                    b.active = False
                    destroyed = e.hit(b.damage)
                    if destroyed:
                        self._on_enemy_killed(e)
                    else:
                        self.fx.sparks(e.x, e.y, e.color, 6)
                        self.snd("hit")
                    break

        # Joueur ↔ ennemis (contact)
        for e in list(self.enemies):
            if not e.active:
                continue
            if dist(px, py, e.x, e.y) < pr + e.radius - 4:
                if self.player.has_shield:
                    e.active = False
                    self._on_enemy_killed(e)
                    self.fx.screen_flash(C_CYAN, alpha=50)
                    self.snd("shield_hit")
                else:
                    if self.player.hit():
                        self.fx.explosion(px, py, C_CYAN, 12)
                        self.fx.screen_flash(C_RED, alpha=80, decay=10)
                        self.snd("hit")
                        if self.player.lives == 1:
                            self._play_warning_sound()

        # Balles ennemies ↔ joueur
        for b in list(self.e_bullets):
            if not b.active:
                continue
            if dist(b.x, b.y, px, py) < b.radius + pr:
                b.active = False
                if self.player.has_shield:
                    self.fx.sparks(b.x, b.y, C_CYAN, 8)
                    self.snd("shield_hit")
                else:
                    if self.player.hit():
                        self.fx.explosion(px, py, C_CYAN, 12)
                        self.fx.screen_flash(C_RED, alpha=80, decay=10)
                        self.snd("hit")
                        if self.player.lives == 1:
                            self._play_warning_sound()

        # Joueur ↔ power-ups
        for p in list(self.powerups):
            if not p.active:
                continue
            if dist(px, py, p.x, p.y) < pr + p.radius:
                p.active = False
                self.fx.explosion(p.x, p.y, p.color, 16)
                self.snd("collect")
                if p.ptype == "life":
                    if self.player.lives < self.player.max_lives:
                        self.player.lives += 1
                else:
                    self.player.add_powerup(p.ptype)

    def _on_enemy_killed(self, e):
        self.player.add_kill()
        big = isinstance(e, Boss)
        self.fx.explosion(e.x, e.y, e.color, 30 if big else 20, big=big)
        self.snd("explode_big" if big else "explode")
        # Score
        self.score_sys.add(e.score_value, e.x, e.y, self.player.combo)
        self.score_sys.highscore = max(self.score_sys.highscore,
                                       self.score_sys.score)
        # Drop power-up
        if random.random() < (0.25 if big else 0.12):
            self.powerups.append(PowerUp(e.x, e.y))
        # Enfants splitter
        if isinstance(e, SplitterEnemy):
            for child in e.spawn_children():
                self.enemies.append(child)

    # ── DRAW ─────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(C_BG)
        self.nebula.draw(self.screen)
        self.stars.draw(self.screen)

        if self.state == self.S_MENU:
            self.menu_screen.draw(self.screen, self.stars, self.nebula, self.games_played, self.unlocked)
        else:
            if self.state == self.S_PAYMENT:
                self.payment_screen.draw(self.screen, self.stars, self.nebula)
            else:
                self._draw_gameplay()
                
            if self.state == self.S_PAUSE:
                self.pause_screen.draw(self.screen)
            elif self.state == self.S_WAVE_TRANS:
                self.wave_screen.draw(self.screen)
            elif self.state == self.S_GAMEOVER:
                self.go_screen.draw(
                    self.screen,
                    self.score_sys.score,
                    self.highscore,
                    self.wave_mgr.wave,
                    self.player.kills,
                    self.player.shots_fired,
                    self.player.max_combo,
                    self.new_record,
                )

        pygame.display.flip()

    def _draw_gameplay(self):
        # Ennemis
        for e in self.enemies:
            e.draw(self.screen)
        # Balles
        for b in self.p_bullets:
            b.draw(self.screen)
        for b in self.e_bullets:
            b.draw(self.screen)
        # Power-ups
        for p in self.powerups:
            p.draw(self.screen, self.fonts["small"])
        # Effets
        self.fx.draw(self.screen)
        # Joueur
        self.player.draw(self.screen, self.fx)
        # Score flottant
        self.score_sys.draw(self.screen, self.fonts)
        # HUD
        self.hud.draw(
            self.screen, self.fonts,
            self.score_sys.score,
            self.highscore,
            self.wave_mgr.wave,
            self.wave_mgr,
            self.player,
            self.boss,
        )

    # ── Persistance ──────────────────────────────────────────────────────

    def _save_highscore(self):
        save_json(HIGHSCORE_FILE, {"highscore": self.highscore})
        
    def _save_settings(self):
        save_json(SETTINGS_FILE, {"games_played": self.games_played, "unlocked": self.unlocked})

    def _save_and_quit(self):
        self._save_highscore()
        pygame.quit()
        raise SystemExit
