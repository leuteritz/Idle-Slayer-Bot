import os
import sys

if getattr(sys, 'frozen', False):
    _ASSETS_DIR = sys._MEIPASS
    _CONFIG_DIR = os.path.dirname(sys.executable)
else:
    _ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
    _CONFIG_DIR = _ASSETS_DIR

os.chdir(_ASSETS_DIR)

import ui.core.config_io as _cio
_cio.AUTO_SAVE_PATH = os.path.join(_CONFIG_DIR, "config.json")

from bot.config import BotConfig, ChestHuntConfig, BonusStageConfig
from ui import ConfigUI

if __name__ == "__main__":
    ui = ConfigUI(BotConfig(), ChestHuntConfig(), BonusStageConfig())
    ui.show()
