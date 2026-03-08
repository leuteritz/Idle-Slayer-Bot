from Bot import IdleSlayerBot
from Config import BotConfig, ChestHuntConfig, BonusStageConfig, TargetConfig
from ConfigUI import ConfigUI

bot_config = BotConfig(
    game_title              = "Idle Slayer",
    monitor_index           = 2,
    d_key_interval          = 2.0,
    space_key_interval      = 0.3,
    space_key_interval_fast = 0.05,
    space_key_pause         = 0.1,
    confidence_threshold    = 0.60,
    jump_key                = "space",
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

target_configs = [
    TargetConfig("bat.png",    1),
    TargetConfig("dragon.png", 1),
    TargetConfig("eagle.png",  1),
    TargetConfig("coin.png",   2),
]

if __name__ == "__main__":
    ui = ConfigUI(bot_config, chest_config, bonus_config, target_configs)
    confirmed = ui.show()

    if not confirmed:
        print("Abgebrochen.")
    else:
        print("Skript startet...")
        IdleSlayerBot(
            bot_config    = ui.bot_config,
            target_configs= ui.target_configs,
            chest_config  = ui.chest_config,
            bonus_config  = ui.bonus_config,
        ).run()
