#!/usr/bin/env python3
"""
main.py — CMMS Desktop Application Entry Point
Algerian Factory CMMS — Local Desktop Command Station

Architecture:
  - Local SQLite database for all sensitive worker data (Law 18-07 compliant)
  - Firebase RTDB used ONLY as transit buffer for WhatsApp Meta API messages
  - Gemini AI classifies technician replies locally
  - All API keys managed through Settings tab → stored in config.json

Data Protection Compliance (Law 18-07):
  - ALL worker profiles, task records, and contract data stored ONLY in local SQLite
  - Firebase used exclusively as ephemeral transit buffer — messages are deleted
    immediately after local processing
  - config.json stores API keys locally — NO cloud storage of credentials

Usage:
  python main.py
"""

import logging
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Logging setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CMMS")


def main() -> None:
    """Application entry point — initialises all subsystems and launches GUI."""

    # ── 1. Initialise Config ────────────────────────────────────
    logger.info("Loading configuration...")
    from config import ConfigManager

    cfg = ConfigManager()
    cfg.load()

    # Warn if not fully configured
    missing = cfg.missing_keys()
    if missing:
        logger.warning(f"Missing configuration keys: {', '.join(missing)}")
        print(
            "\n⚠️  Configuration incomplete. Please set the following in Settings tab:\n"
            f"   {', '.join(missing)}\n"
        )
    else:
        logger.info("All API keys are configured.")

    # ── 2. Initialise Database ──────────────────────────────────
    logger.info("Initialising database...")
    from database import DatabaseManager

    db = DatabaseManager()
    db.init_db()
    db.seed_default_workers()
    logger.info("Database ready.")

    # ── 3. Check CDD Contract Expiry ────────────────────────────
    logger.info("Checking CDD contract expiry...")
    expired = db.check_cdd_expiry()
    for worker in expired:
        db.expire_worker(worker["phone"])
        logger.warning(
            f"CDD EXPIRED — {worker['name']} ({worker['phone']}), "
            f"ended {worker['contract_end_date']}"
        )
    if expired:
        print(
            f"\n⚠️  CDD Contract Expiry Alert: {len(expired)} technician(s) "
            "have expired contracts and have been deactivated.\n"
        )

    # ── 4. Initialise Services ──────────────────────────────────
    logger.info("Initialising services...")
    from whatsapp_handler import WhatsAppHandler
    from gemini_agent import GeminiAgent
    from firebase_bridge import FirebaseBridge

    wh = WhatsAppHandler()
    ga = GeminiAgent()
    fb = FirebaseBridge()

    if not wh.is_configured():
        logger.warning("WhatsApp handler not configured — task dispatch disabled.")
    if not ga.is_configured():
        logger.warning("Gemini agent not configured — AI message parsing disabled.")
    if not fb.is_configured():
        logger.warning("Firebase bridge not configured — message listening disabled.")

    # ── 5. Launch GUI ───────────────────────────────────────────
    logger.info("Launching GUI...")
    from gui.app import MainApp

    app = MainApp(
        db_manager=db,
        whatsapp_handler=wh,
        gemini_agent=ga,
        firebase_bridge=fb,
        config_manager=cfg,
    )

    # ── 6. Start Firebase listener (if configured) ──────────────
    if fb.is_configured() and ga.is_configured():

        def on_firebase_message(msg: dict) -> None:
            """Process an incoming WhatsApp message from Firebase bridge."""
            text = msg.get("text", "")
            sender = msg.get("from", "unknown")
            logger.info(f"Firebase message from {sender}: {text[:60]}...")

            # Classify with Gemini
            status = ga.classify_message(text)
            logger.info(f"Gemini classification: {status}")

            if status in ("COMPLETED", "IN_PROGRESS", "FAILED"):
                # Update the most recent PENDING/IN_PROGRESS task for this worker
                sender_clean = sender.replace("whatsapp:", "")
                tasks = db.get_tasks_by_worker(sender_clean)
                pending = [t for t in tasks if t["status"] in ("PENDING", "IN_PROGRESS")]
                if pending:
                    latest = pending[0]
                    db.update_task_status(latest["id"], status)
                    logger.info(f"Task #{latest['id']} updated to {status}")
                    app.refresh_all()
                else:
                    logger.info(f"No active task found for {sender}")

        logger.info("Starting Firebase listener...")
        fb.start_listening(on_firebase_message, interval=5.0)
    else:
        logger.info(
            "Firebase listener not started (configure Gemini API + Firebase URL in Settings tab)."
        )

    # ── 7. Run main loop ───────────────────────────────────────
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        fb.stop_listening()
        db.close()
        logger.info("Application stopped.")


if __name__ == "__main__":
    main()
