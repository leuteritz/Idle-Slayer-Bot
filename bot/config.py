from dataclasses import dataclass, asdict, fields
import json


@dataclass
class BotConfig:
    game_title:              str   = "Idle Slayer"  # window title used to find the game process
    disable_failsafe:        bool  = False           # disable PyAutoGUI failsafe (mouse to corner = stop)
    monitor_index:           int   = 2               # mss monitor index (0 = virtual combined, 1+ = real)
    d_key_interval:          float = 2.0             # seconds between each D key press
    r_key_interval:          float = 180.0           # seconds between each R key press
    w_mode:                  int   = 1               # 1 = CPS spam, 2 = long hold + short presses
    w_key_cps:               float = 20.0            # mode 1: W key clicks per second
    w_hold_time:             float = 0.3             # mode 2: duration of the long W press (seconds)
    w_short_count:           int   = 2               # mode 2: number of short W presses after the long one


@dataclass
class ChestHuntConfig:
    enabled:                 bool  = True            # enable chest hunt minigame automation
    template:                str   = "chest.png"     # template image for chest detection
    wait_per_chest:          float = 2.0             # seconds to wait after clicking each chest
    confidence:              float = 0.70            # minimum match confidence for chest detection
    rows:                    int   = 3               # number of rows in the chest grid
    cols:                    int   = 10              # number of columns in the chest grid
    panic_button_template:   str   = "chest_close.png"  # template for the Mimik close button
    panic_button_confidence: float = 0.70            # minimum match confidence for the panic button


@dataclass
class BonusStageConfig:
    enabled:                 bool  = True                    # enable bonus stage minigame automation
    template_swipe_left:     str   = "bonus_stage_left.png"  # template for left swipe arrow
    template_swipe_right:    str   = "bonus_stage_right.png" # template for right swipe arrow
    confidence:              float = 0.70                    # minimum match confidence for swipe detection
    swipe_start_offset:      int   = 150                     # pixels from arrow center to start the swipe
    swipe_distance:          int   = 350                     # total swipe length in pixels
    swipe_duration:          float = 0.4                     # duration of the swipe drag (seconds)
    close_button_template:   str   = "bonus_stage_close.png" # template for the close button
    close_button_confidence: float = 0.70                    # minimum match confidence for close button
    jump_key:                str   = "space"                 # key pressed during the bonus stage
    jump_hold_time:          float = 0.05                    # how long the jump key is held (seconds)
    jump_interval:           float = 3.0                     # seconds between each jump key press


def export_config(bot_config: "BotConfig",
                  chest_config: "ChestHuntConfig",
                  bonus_config: "BonusStageConfig") -> str:
    """Serialize all three config objects to a JSON string."""
    return json.dumps({
        "bot":   asdict(bot_config),
        "chest": asdict(chest_config),
        "bonus": asdict(bonus_config),
    }, indent=2)


def import_config(data: dict,
                  bot_config: "BotConfig",
                  chest_config: "ChestHuntConfig",
                  bonus_config: "BonusStageConfig") -> None:
    """Update config objects in-place from a previously exported dict."""
    for key, cfg in [("bot", bot_config), ("chest", chest_config), ("bonus", bonus_config)]:
        section = data.get(key, {})
        for f in fields(cfg):
            if f.name not in section:
                continue
            val     = section[f.name]
            current = getattr(cfg, f.name)
            try:
                if isinstance(current, bool):
                    setattr(cfg, f.name, bool(val))
                elif isinstance(current, int):
                    setattr(cfg, f.name, int(val))
                elif isinstance(current, float):
                    setattr(cfg, f.name, float(val))
                else:
                    setattr(cfg, f.name, val)
            except (ValueError, TypeError):
                pass
