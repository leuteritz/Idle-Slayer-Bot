# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instructions

Keep going until the job is completely solved before ending your turn.
If you’re unsure about code or files, open them—do not hallucinate.
Plan thoroughly before every tool call and reflect on the outcome after.

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
  └─ ui/config_ui.py (ConfigUI – tkinter UI)
       ├─ reads/writes config dataclasses (bot/config.py)
       └─ spawns IdleSlayerBot in daemon thread (bot/bot.py)
            ├─ GameWindow  – win32 focus + pyautogui key/click
            ├─ Target      – enemy template matching (assets/enemies/*.png)
            ├─ ChestHunt   – chest minigame automation (bot/minigames/)
            └─ BonusStage  – bonus stage minigame automation (bot/minigames/)
```

### Key files

| File                           | Purpose                                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| `main.py`                      | Entry point; hardcoded default config values                                                    |
| `bot/config.py`                | `@dataclass` config objects: `BotConfig`, `ChestHuntConfig`, `BonusStageConfig`, `TargetConfig` |
| `bot/bot.py`                   | `IdleSlayerBot.run()` — main loop: screenshot → detect → act                                    |
| `bot/game_window.py`           | Win32 focus management + pyautogui key/click wrapper                                            |
| `bot/template_matcher.py`      | Base class with `_load_template`, `_find_one`, `_find_all`, `_deduplicate`                      |
| `bot/target.py`                | Extends `TemplateMatcher`; wraps a single enemy PNG with priority                               |
| `bot/minigames/chest_hunt.py`  | Detects chest grid, clicks all chests, handles "Mimik" panic button                             |
| `bot/minigames/bonus_stage.py` | Detects swipe arrows, performs drag swipe, handles close button                                 |
| `ui/config_ui.py`              | Tkinter UI with notebook tabs; runs bot in daemon thread                                        |
| `ui/quick_tab.py`              | Overview tab showing the most-used config fields                                                |
| `ui/config_tab.py`             | Per-section full config editor (auto-generated from dataclass fields)                           |
| `ui/target_tab.py`             | Target list editor (add/remove enemy PNGs with priority)                                        |

### Template assets

-   `assets/enemies/*.png` — enemy/coin images used by `Target`
-   `assets/minigames/*.png` — chest, chest_close, bonus_stage_left/right/close images

### Threading model

`ConfigUI` holds `stop_event` and `pause_event` (`threading.Event`). The bot's `run()` loop checks these every iteration and after each chest click. Log output is redirected via `QueueStream` → `queue.Queue` → polled by `root.after(100, ...)` on the main thread.

### Monitor index

`monitor_index` in `BotConfig` selects the screen via `mss.monitors[index]`. Index 0 is the virtual combined monitor; real monitors start at 1. Default in `main.py` is `2`.

## Dependencies

All Windows-only. Key packages: `opencv-python`, `mss`, `pyautogui`, `pywin32`.
