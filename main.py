from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig
from ui.config_ui import ConfigUI

if __name__ == "__main__":
    ui = ConfigUI(BotConfig(), ChestHuntConfig(), BonusStageConfig())
    ui.show()
