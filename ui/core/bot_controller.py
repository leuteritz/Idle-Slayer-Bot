import sys
import threading

from ui.core.hotkey import HotkeyThread
from ui.widgets.log_box import QueueStream
from ui.theme import GREEN, ORANGE, RED


class BotController:
    """Bot-Thread Start/Pause/Resume/Stop — keine Widget-Abhängigkeit."""

    def __init__(self, bot_config, chest_config, bonus_config,
                 stop_event, pause_event, log_queue, crash_queue,
                 key_data, apply_fn, schedule_fn, ui_callbacks):
        self._bot_config = bot_config
        self._chest_config = chest_config
        self._bonus_config = bonus_config
        self._stop_event = stop_event
        self._pause_event = pause_event
        self._log_queue = log_queue
        self._crash_queue = crash_queue
        self._key_data = key_data
        self._apply_fn = apply_fn
        self._schedule = schedule_fn   # lambda fn: root.after(0, fn)
        self._ui = ui_callbacks        # set_status, show_start, show_pause, show_resume, log

        self._running = False
        self._paused = False
        self._bot_thread = None
        self._hotkey_thread = None

    @property
    def running(self):
        return self._running

    @property
    def bot_thread(self):
        return self._bot_thread

    def start(self):
        self._apply_fn()
        sys.stdout = QueueStream(self._log_queue)

        self._stop_event.clear()
        self._pause_event.clear()
        self._running = True

        self._hotkey_thread = HotkeyThread(self.toggle_pause)
        self._hotkey_thread.start()

        for k in ("d", "r", "w", "chest_hunts", "chests_opened", "mimics"):
            self._key_data[k] = 0

        from bot.core.bot import IdleSlayerBot
        bot = IdleSlayerBot(self._bot_config, self._chest_config, self._bonus_config,
                            key_data=self._key_data)

        self._bot_thread = threading.Thread(
            target=bot.run,
            kwargs={"stop_event": self._stop_event,
                    "pause_event": self._pause_event,
                    "crash_queue": self._crash_queue},
            daemon=True)
        self._bot_thread.start()

        self._ui["show_pause"]()
        self._ui["set_status"]("Läuft", GREEN)
        self._ui["log"]("Bot gestartet.")

    def pause(self):
        if self._paused:
            return
        self._pause_event.set()
        self._paused = True
        self._ui["log"]("⏸ Bot pausiert – Werte können jetzt angepasst werden.")
        self._ui["show_resume"]()
        self._ui["set_status"]("Pausiert", ORANGE)

    def resume(self):
        if not self._paused:
            return
        self._apply_fn()
        self._pause_event.clear()
        self._paused = False
        self._ui["log"]("▶ Bot fortgesetzt mit neuer Konfiguration.")
        self._ui["show_pause"]()
        self._ui["set_status"]("Läuft", GREEN)

    def toggle_pause(self):
        """Wird vom globalen Hotkey (F9) aufgerufen – thread-safe via schedule."""
        if not self._running:
            return
        self._schedule(self.resume if self._paused else self.pause)

    def on_crashed(self, kind, msg):
        if not self._running:
            return
        self._running = False
        if kind == "FAILSAFE":
            self._ui["log"]("❌ PyAutoGUI FailSafe ausgelöst – Maus in Bildschirmecke! "
                            "Bot gestoppt. Option 'disable_failsafe' aktivieren, um zu umgehen.")
        else:
            self._ui["log"](f"❌ Bot abgestürzt: {msg}")
        self._ui["set_status"]("Abgestürzt", RED)
        self._ui["show_start"]()

    def stop_hotkey(self):
        if self._hotkey_thread:
            self._hotkey_thread.stop()

    def request_stop(self):
        if self._running:
            self._stop_event.set()
            self._ui["log"]("⏹ Bot wird beendet...")
