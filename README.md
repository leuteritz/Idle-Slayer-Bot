# Idle Slayer Bot

An automation bot for the game [Idle Slayer](https://store.steampowered.com/app/1353300/Idle_Slayer/). It captures the screen, detects game elements via template matching, and automates repetitive actions — key presses, minigames, and SP scanning — through a Tkinter configuration UI.

![Python 3.x](https://img.shields.io/badge/python-3.x-blue) ![Windows only](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## Features

-   **Automated key presses** — D key (attack), R key (prestige/rebirth), W key (movement/combat)
-   **Two W-key modes** — CPS spam or long-hold + short-press burst
-   **Chest Hunt automation** — detects the chest grid, clicks all chests, handles the Mimik panic button
-   **Bonus Stage automation** — detects swipe arrows, performs drag swipes, presses jump key, closes the stage
-   **SP Scanner** — reads game process memory to find your current SP (Soul Points) value in real time
-   **Pause / Resume / Stop** — full bot lifecycle control from the UI
-   **Global F9 hotkey** — pause/resume without switching windows
-   **Config import / export** — save and load settings as JSON
-   **Live log view** — colored, scrollable log output inside the UI

---

## Requirements

-   **Windows** (win32 APIs are used throughout)
-   **Python 3.9+**

Install dependencies:

```bash
pip install opencv-python mss pyautogui pywin32
```

---

## Installation

```bash
git clone https://github.com/your-username/idle-slayer-bot.git
cd idle-slayer-bot
pip install opencv-python mss pyautogui pywin32
```

---

## Usage

```bash
python main.py
```

This opens the configuration UI. From there:

1. Adjust settings on the **Quick** or **Config** tabs.
2. Click **Start** to launch the bot in a background thread.
3. Use **Pause** / **Resume** / **Stop** to control the bot.
4. Press **F9** at any time to toggle pause/resume globally.

---

## Configuration

All settings are stored in three dataclasses in `bot/config.py`. They can be edited in the UI and exported/imported as JSON.

### BotConfig

| Field              | Type    | Default         | Description                                                      |
| ------------------ | ------- | --------------- | ---------------------------------------------------------------- |
| `game_title`       | `str`   | `"Idle Slayer"` | Window title used to locate the game process                     |
| `disable_failsafe` | `bool`  | `False`         | Disable PyAutoGUI failsafe (mouse to corner = emergency stop)    |
| `monitor_index`    | `int`   | `2`             | mss monitor index — `0` = virtual combined, `1+` = real monitors |
| `d_key_interval`   | `float` | `2.0`           | Seconds between each D key press                                 |
| `r_key_interval`   | `float` | `180.0`         | Seconds between each R key press                                 |
| `w_mode`           | `int`   | `1`             | W-key mode: `1` = CPS spam, `2` = hold + short bursts            |
| `w_key_cps`        | `float` | `20.0`          | Mode 1: W key clicks per second                                  |
| `w_hold_time`      | `float` | `0.3`           | Mode 2: duration of the long W press (seconds)                   |
| `w_short_count`    | `int`   | `2`             | Mode 2: number of short W presses after the long hold            |

### ChestHuntConfig

| Field                     | Type    | Default             | Description                                   |
| ------------------------- | ------- | ------------------- | --------------------------------------------- |
| `enabled`                 | `bool`  | `True`              | Enable Chest Hunt minigame automation         |
| `template`                | `str`   | `"chest.png"`       | Template image for chest detection            |
| `wait_per_chest`          | `float` | `2.0`               | Seconds to wait after clicking each chest     |
| `confidence`              | `float` | `0.70`              | Minimum match confidence for chest detection  |
| `rows`                    | `int`   | `3`                 | Number of rows in the chest grid              |
| `cols`                    | `int`   | `10`                | Number of columns in the chest grid           |
| `panic_button_template`   | `str`   | `"chest_close.png"` | Template for the Mimik close button           |
| `panic_button_confidence` | `float` | `0.70`              | Minimum match confidence for the panic button |

### BonusStageConfig

| Field                     | Type    | Default                   | Description                                       |
| ------------------------- | ------- | ------------------------- | ------------------------------------------------- |
| `enabled`                 | `bool`  | `True`                    | Enable Bonus Stage minigame automation            |
| `template_swipe_left`     | `str`   | `"bonus_stage_left.png"`  | Template for left swipe arrow                     |
| `template_swipe_right`    | `str`   | `"bonus_stage_right.png"` | Template for right swipe arrow                    |
| `confidence`              | `float` | `0.70`                    | Minimum match confidence for swipe detection      |
| `swipe_start_offset`      | `int`   | `150`                     | Pixels from arrow center to start the swipe       |
| `swipe_distance`          | `int`   | `350`                     | Total swipe length in pixels                      |
| `swipe_duration`          | `float` | `0.4`                     | Duration of the swipe drag (seconds)              |
| `close_button_template`   | `str`   | `"bonus_stage_close.png"` | Template for the close button                     |
| `close_button_confidence` | `float` | `0.70`                    | Minimum match confidence for close button         |
| `jump_key`                | `str`   | `"space"`                 | Key pressed repeatedly during the bonus stage     |
| `jump_hold_time`          | `float` | `0.05`                    | How long the jump key is held per press (seconds) |
| `jump_interval`           | `float` | `3.0`                     | Seconds between each jump key press               |

---

## W-Key Modes

| Mode | Name         | Behaviour                                                                                      |
| ---- | ------------ | ---------------------------------------------------------------------------------------------- |
| `1`  | CPS Spam     | Sends W at `w_key_cps` clicks per second — no window focus change per press                    |
| `2`  | Hold + Burst | Focuses window → holds W for `w_hold_time` s → sends `w_short_count` quick presses → unfocuses |

---

## Minigames

### Chest Hunt

When the Chest Hunt minigame appears, the bot:

1. Detects the chest grid using template matching (`chest.png`).
2. Clicks every chest in sequence, waiting `wait_per_chest` seconds between clicks.
3. Watches for the Mimik enemy close button (`chest_close.png`) and clicks it immediately if found.

### Bonus Stage

When the Bonus Stage minigame appears, the bot:

1. Detects left/right swipe arrows (`bonus_stage_left.png` / `bonus_stage_right.png`).
2. Performs a drag swipe in the indicated direction.
3. Presses the jump key (`space` by default) at regular intervals.
4. Clicks the close button (`bonus_stage_close.png`) when the stage ends.

---

## SP Scanner

The SP Scanner tab reads the game's process memory directly to find the current SP (Soul Points) value.

-   Performs a full memory scan on the first run to find candidate addresses.
-   Uses a two-pass filter to narrow candidates to the live value.
-   Displays results as dashboard cards with live updates.
-   No game files are modified — read-only memory access only.

---

## Assets

Template images must be present in `assets/minigames/` for minigame detection to work:

| File                    | Used for                           |
| ----------------------- | ---------------------------------- |
| `chest.png`             | Chest grid detection               |
| `chest_close.png`       | Mimik panic button detection       |
| `bonus_stage_left.png`  | Left swipe arrow detection         |
| `bonus_stage_right.png` | Right swipe arrow detection        |
| `bonus_stage_close.png` | Bonus stage close button detection |

These are screenshots cropped from the game. If detection fails, recapture the templates at your screen resolution.

---

## Project Structure

```
Idle Slayer/
├── main.py                        # Entry point
├── bot/
│   ├── config.py                  # BotConfig, ChestHuntConfig, BonusStageConfig dataclasses
│   ├── bot.py                     # Main bot loop
│   ├── game_window.py             # Win32 focus management + pyautogui wrappers
│   ├── template_matcher.py        # OpenCV template matching base class
│   ├── memory_reader.py           # GameMemory — reads SP from process memory
│   └── minigames/
│       ├── chest_hunt.py          # Chest Hunt automation
│       └── bonus_stage.py         # Bonus Stage automation
├── ui/
│   ├── __init__.py                # Re-exports ConfigUI
│   ├── theme.py                   # Colors, fonts, ScrollableFrame
│   ├── core/
│   │   ├── app.py                 # ConfigUI orchestrator
│   │   ├── navigation.py          # Sidebar, header, SP pill, page switching
│   │   ├── config_io.py           # Config load/save/export/import
│   │   ├── bot_controller.py      # Bot thread lifecycle
│   │   └── hotkey.py              # Global F9 hotkey listener
│   ├── tabs/
│   │   ├── quick_tab.py           # Quick overview tab
│   │   ├── config_tab.py          # Full per-section config editor
│   │   ├── sp_scanner_tab.py      # SP Scanner UI
│   │   └── sp_scanner_logic.py    # SP Scanner memory scan logic
│   └── widgets/
│       └── log_box.py             # Colored log widget + QueueStream
└── assets/
    └── minigames/                 # Template PNG images
```

---

## Architecture

```
main.py
  └─ ConfigUI (ui/core/app.py)
       ├─ NavigationManager   – sidebar, header, SP pill, page switching
       ├─ ConfigIO            – config load/save/export/import
       ├─ BotController       – bot thread start/pause/resume/stop
       ├─ HotkeyThread        – global F9 hotkey
       └─ IdleSlayerBot (bot/bot.py)  [daemon thread]
            ├─ GameWindow      – win32 focus + key/click sending
            ├─ ChestHunt       – chest minigame automation
            └─ BonusStage      – bonus stage minigame automation
```

Log output is redirected via `QueueStream → queue.Queue`, polled by `root.after(100, ...)` on the main thread. The SP scanner runs its own daemon thread and pushes updates back to the UI via `parent.after(0, ...)`.

---

## Disclaimer

This bot is provided for educational and personal use only. Automating games may violate the game's terms of service. Use at your own risk. The authors are not responsible for any consequences arising from its use.
