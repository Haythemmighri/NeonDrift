# 🌌 NEON DRIFT — Jeu de Survie Quantique

> Un shoot'em up horizontal néon avec boss, dash, power-ups, combos et difficulté progressive.

---

## 🚀 Installation & Lancement

```bash
pip install pygame
python main.py
```

---

## 🎮 Contrôles

| Touche | Action |
|--------|--------|
| `Z Q S D` / Flèches | Déplacement |
| `ESPACE` | Tir (maintenir = auto) |
| `SHIFT` | **Dash** (bref sprint invincible) |
| `P` / `ÉCHAP` | Pause / Reprendre |
| `ÉCHAP` (maintenu 2s) | Retour au menu |

---

## ⚔️ Ennemis (6 types)

| Type | Comportement | PV | Points |
|------|--------------|----|--------|
| **Basic** (magenta) | Fonce tout droit | 1 | 10 |
| **Zigzag** (vert) | Trajectoire sinusoïdale | 1 | 20 |
| **Tank** (orange) | Lent, tir ciblé | 4 | 40 |
| **Ghost** (violet) | Semi-transparent, missile à tête chercheuse | 1 | 30 |
| **Splitter** (rose) | Se divise en 2 à la mort | 1/2 | 25 |
| **Sniper** (teal) | Se poste à droite, tir précis | 1 | 35 |
| **Boss** (rouge) | 5 patterns, multi-phase, rage à 30% HP | 120+ | 500+ |

---

## ⚡ Power-ups (5 types pondérés)

| Icône | Nom | Effet |
|-------|-----|-------|
| **R** | Rapid Fire | Cadence x2 (6s) |
| **S** | Shield | Absorbe 1 coup, détruit les ennemis au contact |
| **M** | Multi-Shot | Triple tir directionnel (6s) |
| **L** | Laser | Balle large dégâts ×2 (6s) |
| **♥** | Extra Vie | +1 vie (max 3) |

---

## 🏆 Scoring

- Score multiplié par le combo (kill / 3 → multiplicateur)
- Meilleur score sauvegardé dans `highscore.json`
- Textes flottants affichant les points obtenus

---

## 🗺️ Structure du projet

```
NeonDrift/
├── main.py              # Point d'entrée
├── highscore.json       # Créé automatiquement
├── README.md
└── src/
    ├── __init__.py
    ├── constants.py     # Constantes globales
    ├── utils.py         # Fonctions utilitaires + synthèse sonore
    ├── effects.py       # Particules, shockwaves, nébuleuse, starfield
    ├── player.py        # Joueur, balles joueur, dash, power-ups
    ├── enemies.py       # Tous les ennemis + boss multi-phase
    ├── systems.py       # WaveManager, ScoreSystem, PowerUp, HUD
    ├── screens.py       # Menu, Pause, Transition vague, Game Over
    └── game.py          # Classe principale Game (boucle + collisions)
```

---

## 🎨 Architecture OOP

| Classe | Fichier | Rôle |
|--------|---------|------|
| `Game` | game.py | Orchestration, états, collisions |
| `Player` | player.py | Déplacement, dash, tir, power-ups |
| `PlayerBullet` | player.py | Projectile joueur |
| `Enemy` (base) | enemies.py | Classe de base ennemi |
| `ZigzagEnemy` | enemies.py | Héritage Enemy |
| `TankEnemy` | enemies.py | Héritage Enemy |
| `GhostEnemy` | enemies.py | Héritage Enemy |
| `SplitterEnemy` | enemies.py | Héritage Enemy |
| `SniperEnemy` | enemies.py | Héritage Enemy |
| `Boss` | enemies.py | Boss multi-phase |
| `EnemyBullet` | enemies.py | Projectile ennemi (homing ou droit) |
| `PowerUp` | systems.py | Objets ramassables |
| `WaveManager` | systems.py | Spawn et progression |
| `ScoreSystem` | systems.py | Score + textes flottants |
| `HUD` | systems.py | Interface de jeu |
| `EffectManager` | effects.py | Particules, shockwaves, lasers |
| `StarField` | effects.py | Fond étoilé parallaxe |
| `Nebula` | effects.py | Nébuleuses animées |
| `MenuScreen` | screens.py | Écran titre |
| `PauseScreen` | screens.py | Écran pause |
| `WaveTransitionScreen` | screens.py | Transition inter-vagues |
| `GameOverScreen` | screens.py | Écran fin de partie |

---

## 🔗 Nouvelles fonctionnalités

### 💥 Réaction en chaîne (Chain Reaction)
Tuer un **Tank** déclenche une explosion qui endommage tous les ennemis proches (rayon 100 px). Les ennemis touchés dans la déflagration rapportent **1.5× les points habituels**. Si un deuxième Tank se trouve dans le rayon, il explose à son tour (jusqu'à 3 niveaux de cascade).

### 🏆 Classement en ligne
Un serveur Flask léger + SQLite stocke les scores de tous les joueurs.

**Lancer le serveur** (dans un terminal séparé avant de jouer) :
```bash
pip install flask
python leaderboard_server.py
```

- Le **Menu principal** affiche le top-8 mondial en temps réel (panneau à droite).
- À la fin de la partie, le joueur **entre son nom** (10 car. max) avant de soumettre son score.
- Tout se passe dans un **thread daemon** : le serveur hors-ligne n'affecte jamais le jeu.



1. ✅ **Niveaux de difficulté progressifs** (vitesse, ennemis variés, boss)
2. ✅ **Effets sonores** (synthèse procédurale Python, 12 sons distincts)
3. ✅ **Animations** (traînée joueur, anneaux rotatifs, nébuleuse, particules, shockwaves)
4. ✅ **Meilleur score** sauvegardé en JSON
5. ✅ **Écran de pause** (P ou ÉCHAP)

---

## 🔧 Ressources

- **Sons** : 100% synthèse procédurale via `pygame.mixer.Sound`
- **Graphismes** : 100% dessinés procéduralement via `pygame.draw`
- Aucun asset externe requis
