from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig
from ui.config_ui import ConfigUI

bot_config = BotConfig(
    game_title              = "Idle Slayer",
    monitor_index           = 2,
    d_key_interval          = 2.0,
    r_key_interval          = 180.0,
    w_key_cps               = 20.0,
)

chest_config = ChestHuntConfig(
    enabled                  = True,
    template                 = "chest.png",
    wait_per_chest           = 2.0,
    confidence               = 0.70,
    panic_button_template    = "chest_close.png",
    panic_button_confidence  = 0.70,
)


bonus_config = BonusStageConfig(
    enabled                  = True,
    template_swipe_left      = "bonus_stage_left.png",
    template_swipe_right     = "bonus_stage_right.png",
    confidence               = 0.70,
    swipe_start_offset       = 150,
    swipe_distance           = 350,
    swipe_duration           = 0.4,
    close_button_template    = "bonus_stage_close.png",
    close_button_confidence  = 0.70,
    jump_key                 = "space",
    jump_hold_time           = 0.05,
    jump_interval            = 3.0,
)

if __name__ == "__main__":
    ui = ConfigUI(bot_config, chest_config, bonus_config)
    ui.show()
