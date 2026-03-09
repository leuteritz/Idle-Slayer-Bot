from dataclasses import dataclass


@dataclass
class BotConfig:
    game_title:              str   = "Idle Slayer"
    disable_failsafe:        bool  = False   # PyAutoGUI FailSafe deaktivieren (Maus in Ecke = Stop)
    monitor_index:           int   = 2
    d_key_interval:          float = 2.0
    r_key_interval:          float = 180.0
    w_mode:                  int   = 1       # 1 = CPS-Spam, 2 = Lang + 2× Kurz
    w_key_cps:               float = 20.0    # Modus 1: Clicks pro Sekunde
    w_hold_time:             float = 0.5     # Modus 2: langer Druck (s)
    w_short_count:           int   = 2       # Modus 2: Anzahl kurze Drücke danach


@dataclass
class ChestHuntConfig:
    enabled:                 bool  = True
    template:                str   = "chest.png"
    wait_per_chest:          float = 2.0
    confidence:              float = 0.70
    rows:                    int   = 3
    cols:                    int   = 10
    panic_button_template:   str   = "chest_close.png"
    panic_button_confidence: float = 0.70



@dataclass
class BonusStageConfig:
    enabled:                 bool  = True
    template_swipe_left:     str   = "bonus_stage_left.png"
    template_swipe_right:    str   = "bonus_stage_right.png"
    confidence:              float = 0.70
    swipe_start_offset:      int   = 150
    swipe_distance:          int   = 350
    swipe_duration:          float = 0.4
    close_button_template:   str   = "bonus_stage_close.png"
    close_button_confidence: float = 0.70
    jump_key:                str   = "space"       # Taste die im Minispiel gedrückt wird
    jump_hold_time:          float = 0.05          # Wie lange die Taste gehalten wird
    jump_interval:           float = 3.0           # Alle X Sekunden springen


