"""
config.py — ConfigManager for local config.json storage.
All API keys, tokens, and phone IDs are stored locally.
"""

import json
import os
import threading
from typing import Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "GEMINI_API_KEY": "",
    "META_ACCESS_TOKEN": "",
    "WHATSAPP_PHONE_ID": "",
    "FIREBASE_DB_URL": "",
}


class ConfigManager:
    """Thread-safe local config manager. Reads/writes config.json."""

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._config: dict[str, Any] = dict(DEFAULT_CONFIG)
                    cls._instance._loaded = False
                    cls._instance._mod_lock = threading.Lock()
        return cls._instance

    def load(self) -> None:
        """Load config from disk. Falls back to defaults."""
        with self._mod_lock:
            try:
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        stored = json.load(f)
                    for key in DEFAULT_CONFIG:
                        self._config[key] = stored.get(key, DEFAULT_CONFIG[key])
                else:
                    self._config = dict(DEFAULT_CONFIG)
                self._loaded = True
            except (json.JSONDecodeError, OSError):
                self._config = dict(DEFAULT_CONFIG)
                self._loaded = True

    def save(self) -> None:
        """Persist current config to disk."""
        with self._mod_lock:
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            except OSError as e:
                print(f"[Config] Failed to save: {e}")

    def get(self, key: str, default: Any = "") -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._mod_lock:
            self._config[key] = value

    def is_configured(self) -> bool:
        """Check if all required API keys are set."""
        required = ["GEMINI_API_KEY", "META_ACCESS_TOKEN", "WHATSAPP_PHONE_ID", "FIREBASE_DB_URL"]
        return all(self._config.get(k) for k in required)

    def missing_keys(self) -> list[str]:
        return [k for k in ["GEMINI_API_KEY", "META_ACCESS_TOKEN", "WHATSAPP_PHONE_ID", "FIREBASE_DB_URL"]
                if not self._config.get(k)]
