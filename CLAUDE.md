# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Bot

```bash
python main.py
```

This opens the Tkinter config UI. The bot runs in a background thread once started from the UI. There is no separate test suite or build step.

## Architecture

The bot automates the game "Idle Slayer" via screen capture (mss) and template matching (OpenCV). It interacts with the game window using pyautogui and win32gui (Windows-only).

### Data flow

```
main.py
  └─ ConfigUI (tkinter UI, ConfigUI.py)
       ├─ reads/writes config dataclasses (Config.py)
       └─ spawns IdleSlayerBot in daemon thread (Bot.py)
            ├─ GameWindow  – win32 focus + pyautogui key/click
            ├─ Target      – enemy template matching (enemies/*.png)
            ├─ ChestHunt   – chest minigame automation (minigames/)
            └─ BonusStage  – bonus stage minigame automation (minigames/)
```

### Key files

| File | Purpose |
|------|---------|
| `main.py` | Entry point; hardcoded default config values |
| `Config.py` | `@dataclass` config objects: `BotConfig`, `ChestHuntConfig`, `BonusStageConfig`, `TargetConfig` |
| `Bot.py` | `IdleSlayerBot.run()` — main loop: screenshot → detect → act |
| `GameWindow.py` | Win32 focus management + pyautogui key/click wrapper |
| `TemplateMatcher.py` | Base class with `_load_template`, `_find_one`, `_find_all`, `_deduplicate` |
| `Target.py` | Extends `TemplateMatcher`; wraps a single enemy PNG with priority |
| `minigames/ChestHunt.py` | Detects chest grid, clicks all chests, handles "Mimik" panic button |
| `minigames/BonusStage.py` | Detects swipe arrows, performs drag swipe, handles close button |
| `ConfigUI.py` | Tkinter UI with notebook tabs; runs bot in daemon thread |
| `ui/QuickTab.py` | Overview tab showing the most-used config fields |
| `ui/ConfigTab.py` | Per-section full config editor (auto-generated from dataclass fields) |
| `ui/TargetTab.py` | Target list editor (add/remove enemy PNGs with priority) |

### Template assets

- `enemies/*.png` — enemy/coin images used by `Target` (loaded from `ENEMIES_DIR`)
- `minigames/assets/*.png` — chest, chest_close, bonus_stage_left/right/close images

### Threading model

`ConfigUI` holds `stop_event` and `pause_event` (`threading.Event`). The bot's `run()` loop checks these every iteration and after each chest click. Log output is redirected via `QueueStream` → `queue.Queue` → polled by `root.after(100, ...)` on the main thread.

### Monitor index

`monitor_index` in `BotConfig` selects the screen via `mss.monitors[index]`. Index 0 is the virtual combined monitor; real monitors start at 1. Default in `main.py` is `2`.

## Dependencies

All Windows-only. Key packages: `opencv-python`, `mss`, `pyautogui`, `pywin32`.
