"""
gemini_agent.py — Google Generative AI agent that classifies
technician WhatsApp replies into COMPLETED / IN_PROGRESS / FAILED.
"""

from config import ConfigManager
import logging

logger = logging.getLogger(__name__)


class GeminiAgent:
    """Local AI agent that uses Gemini to parse technician message intent."""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._model = None
        self._configured = False
        if not api_key:
            self._load_from_config()
        if self._api_key:
            self._init_model()

    # ── Configuration ───────────────────────────────────────────

    def _load_from_config(self) -> None:
        cfg = ConfigManager()
        self._api_key = cfg.get("GEMINI_API_KEY", "")

    def configure(self, api_key: str) -> None:
        """Re-configure with a new API key at runtime."""
        self._api_key = api_key
        self._init_model()

    def _init_model(self) -> None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash")
            self._configured = True
        except Exception as e:
            logger.warning(f"[Gemini] Failed to initialise model: {e}")
            self._configured = False

    def is_configured(self) -> bool:
        return self._configured and bool(self._api_key)

    # ── Classification ──────────────────────────────────────────

    def classify_message(self, text: str) -> str:
        """
        Classify a technician's message into one of:
        COMPLETED | IN_PROGRESS | FAILED | UNKNOWN

        Uses Gemini with a strict one-word response prompt.
        """
        if not self.is_configured():
            logger.warning("[Gemini] Not configured — returning UNKNOWN")
            return "UNKNOWN"

        prompt = (
            "You are a maintenance task classifier. A technician sent a WhatsApp message "
            "about a task they were assigned. Determine the task status from the message.\n\n"
            "Rules:\n"
            "- Return EXACTLY one word: COMPLETED, IN_PROGRESS, or FAILED\n"
            "- COMPLETED = technician says they finished, task is done, 'done', 'تم', 'خلصت', 'كملت'\n"
            "- IN_PROGRESS = technician says they are working on it, 'working', 'في العمل', 'قيد التنفيز', 'باشرت'\n"
            "- FAILED = technician reports a problem, can't do it, equipment broken, 'فشل', 'مشكلة', 'عطل', 'ماقدرتش'\n"
            "- If the message is ambiguous, unclear, or not about a task, return UNKNOWN\n"
            "- Do NOT include any explanation, punctuation, markdown, or extra text\n\n"
            f"Technician message: {text}\n\n"
            "Classification:"
        )

        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 10,
                    "top_p": 0.95,
                },
            )
            raw = response.text.strip().upper()
            # Strip any markdown backticks or formatting
            raw = raw.replace("```", "").replace("`", "").strip()
            # Take only the first word
            first_word = raw.split()[0] if raw else ""
            # Normalise
            for valid in ("COMPLETED", "IN_PROGRESS", "FAILED"):
                if first_word == valid:
                    return valid
            # Fuzzy match
            if "COMPLET" in first_word or first_word == "DONE":
                return "COMPLETED"
            if "PROGRESS" in first_word or "WORKING" in first_word:
                return "IN_PROGRESS"
            if "FAIL" in first_word:
                return "FAILED"
            return "UNKNOWN"
        except Exception as e:
            logger.error(f"[Gemini] API call failed: {e}")
            return "UNKNOWN"
