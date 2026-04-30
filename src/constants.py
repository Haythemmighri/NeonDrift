

SCREEN_W   = 900
SCREEN_H   = 600
FPS        = 60
TITLE      = "NEON DRIFT"

C_BG         = (4,   4,  20)
C_BG2        = (8,   8,  30)
C_CYAN       = (0,  220, 255)
C_MAGENTA    = (255,  0, 200)
C_YELLOW     = (255, 210,   0)
C_GREEN      = (0,  255, 110)
C_WHITE      = (255, 255, 255)
C_DARK_CYAN  = (0,   70,  80)
C_ORANGE     = (255, 140,   0)
C_RED        = (255,  40,  40)
C_PURPLE     = (180,  0,  255)
C_PINK       = (255,  80, 160)
C_TEAL       = (0,  200, 170)
C_DARK_GREY  = (30,  30,  50)
C_GREY       = (100, 100, 130)

PLAYER_SPEED         = 5
PLAYER_SHOOT_COOLDOWN = 10
BULLET_SPEED         = 13
ENEMY_BULLET_SPEED   = 4.5

POWERUP_DURATION     = 360 
SHIELD_DURATION      = 300
RAPID_FIRE_COOLDOWN  = 5

BOSS_APPEAR_WAVE     = 5     
WAVE_PAUSE_FRAMES    = 200

SCORE_BASIC    = 10
SCORE_ZIGZAG   = 20
SCORE_TANK     = 40
SCORE_GHOST    = 30
SCORE_SPLITTER = 25
SCORE_SNIPER   = 35
SCORE_BOSS     = 500

HIGHSCORE_FILE = "highscore.json"
SETTINGS_FILE  = "settings.json"

# ── Konnect Payment Config ────────────────────────────────────────────────────
KONNECT_WALLET_ID  = "68036ba4c4f4ab1d9ffb00ef"
KONNECT_API_KEY    = "68036ba4c4f4ab1d9ffb00e7:TZYBj46FXgRwyF9A8x5Df2vIenLMaBZ"
KONNECT_INIT_URL   = "https://api.preprod.konnect.network/api/v2/payments/init-payment"
KONNECT_STATUS_URL = "https://api.preprod.konnect.network/api/v2/payments/"
KONNECT_SANDBOX_URL = "https://sandbox.knct.me/qs_gaQd1I"
KONNECT_AMOUNT     = 100          # millimes (100 = 1,00 TND)
MAX_FREE_PLAYS     = 3
PLAYS_FILE         = "plays.json"
UNLOCK_FILE        = "unlock.json"
