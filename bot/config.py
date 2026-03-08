from dataclasses import dataclass


@dataclass
class BotConfig:
    game_title:              str   = "Idle Slayer"
    disable_failsafe:        bool  = False   # PyAutoGUI FailSafe deaktivieren (Maus in Ecke = Stop)
    monitor_index:           int   = 2
    d_key_interval:          float = 4.0
    r_key_interval:          float = 600.0
    space_key_interval:      float = 0.3
    space_key_interval_fast: float = 0.05
    space_key_pause:         float = 0.1
    confidence_threshold:    float = 0.60
    jump_key:                str   = "space"
    cooldown:                float = 1.0
    check_interval:          float = 0.2


@dataclass
class ChestHuntConfig:
    enabled:                 bool  = True
    template:                str   = "chest.png"
    wait_per_chest:          float = 5.0
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


@dataclass
class TargetConfig:
    filename: str
    priority: int
