"""
firebase_bridge.py — Firebase Realtime Database bridge via REST API.
Polls for new WhatsApp messages, passes them to a callback, then
deletes them from the cloud (transit buffer only — no data persisted).
"""

import requests
import threading
import time
import logging
from config import ConfigManager

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5.0  # seconds


class FirebaseBridge:
    """Polls Firebase RTDB for incoming messages and dispatches them."""

    def __init__(self):
        self._db_url = ""
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._refresh_config()

    def _refresh_config(self) -> None:
        cfg = ConfigManager()
        self._db_url = cfg.get("FIREBASE_DB_URL", "").rstrip("/")

    def refresh_config(self) -> None:
        self._refresh_config()

    def is_configured(self) -> bool:
        return bool(self._db_url)

    # ── CRUD helpers ────────────────────────────────────────────

    def push_message(self, message_data: dict) -> bool:
        """POST a new message to /messages.json (testing / manual use)."""
        if not self.is_configured():
            return False
        try:
            resp = requests.post(
                f"{self._db_url}/messages.json",
                json=message_data,
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            logger.error(f"[Firebase] push_message failed: {e}")
            return False

    def fetch_new_messages(self) -> list[dict]:
        """
        GET latest messages from /messages.json.
        Returns list of dicts with keys: key, from, text, timestamp.
        """
        if not self.is_configured():
            return []
        try:
            resp = requests.get(
                f"{self._db_url}/messages.json?orderBy=%22$key%22&limitToLast=10",
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(f"[Firebase] fetch status {resp.status_code}")
                return []
            data = resp.json()
            if not isinstance(data, dict):
                return []
            results = []
            for key, msg in data.items():
                if isinstance(msg, dict):
                    msg["key"] = key
                    results.append(msg)
            return results
        except requests.RequestException as e:
            logger.error(f"[Firebase] fetch_new_messages failed: {e}")
            return []

    def delete_message(self, message_key: str) -> bool:
        """DELETE a single message by its Firebase key."""
        if not self.is_configured():
            return False
        try:
            resp = requests.delete(
                f"{self._db_url}/messages/{message_key}.json",
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            logger.error(f"[Firebase] delete_message failed: {e}")
            return False

    def delete_all_messages(self) -> bool:
        """DELETE the entire /messages node. Use for cleanup."""
        if not self.is_configured():
            return False
        try:
            resp = requests.delete(
                f"{self._db_url}/messages.json",
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            logger.error(f"[Firebase] delete_all_messages failed: {e}")
            return False

    # ── Background listener ─────────────────────────────────────

    def start_listening(
        self,
        callback,
        interval: float = POLL_INTERVAL,
    ) -> None:
        """
        Start a background thread that polls Firebase every `interval` seconds.
        For each new message, calls callback(message_dict) then deletes it.
        The callback should accept a single dict argument.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("[Firebase] Listener already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            args=(callback, interval),
            daemon=True,
            name="firebase-listener",
        )
        self._thread.start()
        logger.info("[Firebase] Listener started")

    def stop_listening(self) -> None:
        """Signal the listener thread to stop (non-blocking)."""
        self._stop_event.set()
        logger.info("[Firebase] Listener stopping")

    def _poll_loop(self, callback, interval: float) -> None:
        while not self._stop_event.is_set():
            try:
                messages = self.fetch_new_messages()
                for msg in messages:
                    if self._stop_event.is_set():
                        break
                    try:
                        callback(msg)
                    except Exception as e:
                        logger.error(f"[Firebase] Callback error: {e}")
                    # Delete after processing
                    key = msg.get("key")
                    if key:
                        self.delete_message(key)
            except Exception as e:
                logger.error(f"[Firebase] Poll loop error: {e}")
            self._stop_event.wait(interval)
