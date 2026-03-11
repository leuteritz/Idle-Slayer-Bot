import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig
from ui import ConfigUI

if __name__ == "__main__":
    ui = ConfigUI(BotConfig(), ChestHuntConfig(), BonusStageConfig())
    ui.show()
