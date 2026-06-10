"""
whatsapp_handler.py — Meta WhatsApp Cloud API integration.
Sends task assignment messages to technicians.
"""

import requests
import logging
from config import ConfigManager

logger = logging.getLogger(__name__)

API_VERSION = "v22.0"


class WhatsAppHandler:
    """Manages outbound WhatsApp messages via Meta Cloud API."""

    def __init__(self):
        self._refresh_config()

    def _refresh_config(self) -> None:
        cfg = ConfigManager()
        self._access_token = cfg.get("META_ACCESS_TOKEN", "")
        self._phone_id = cfg.get("WHATSAPP_PHONE_ID", "")
        self._base_url = (
            f"https://graph.facebook.com/{API_VERSION}/{self._phone_id}/messages"
            if self._phone_id
            else ""
        )

    def refresh_config(self) -> None:
        """Call after settings are updated to reload tokens."""
        self._refresh_config()

    def is_configured(self) -> bool:
        return bool(self._access_token) and bool(self._phone_id)

    # ── Core sender ─────────────────────────────────────────────

    def send_message(self, to_phone: str, message: str) -> bool:
        """Send a plain-text WhatsApp message. Returns True on success."""
        if not self.is_configured():
            logger.warning("[WhatsApp] Not configured — message not sent")
            return False

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message},
        }

        try:
            resp = requests.post(
                self._base_url, headers=headers, json=payload, timeout=15
            )
            if resp.status_code == 200:
                logger.info(f"[WhatsApp] Message sent to {to_phone}")
                return True
            else:
                logger.error(
                    f"[WhatsApp] API error {resp.status_code}: {resp.text}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"[WhatsApp] Request failed: {e}")
            return False

    # ── Convenience ─────────────────────────────────────────────

    def send_task_assignment(
        self,
        to_phone: str,
        worker_name: str,
        task_description: str,
        estimated_duration: int,
    ) -> bool:
        """Send a formatted task assignment message in Arabic."""
        msg = (
            f"مرحباً {worker_name}، تم تعيينك للمهمة التالية:\n"
            f"📋 {task_description}\n"
            f"⏱ المدة المقدرة: {estimated_duration} دقيقة\n\n"
            "الرجاء الرد بـ 'تم' عند الانتهاء أو 'قيد التنفيذ' إذا كنت تعمل عليها."
        )
        return self.send_message(to_phone, msg)
