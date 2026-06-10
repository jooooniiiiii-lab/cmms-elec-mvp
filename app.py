"""
app.py — Gradio web interface for CMMS Électrique
Deployed on HF Spaces (SDK: Gradio) or run locally for a .gradio.live link.
"""

import os
import sys

import gradio as gr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager
from config import ConfigManager

db = DatabaseManager()
db.init_db()
db.seed_default_workers()

config = ConfigManager()


def get_workers_list() -> str:
    workers = db.get_workers()
    if not workers:
        return "No workers found."
    lines = []
    for w in workers:
        status = "🟢 Active" if w["is_active"] else "🔴 Inactive"
        expiry = f" (expires {w['contract_end_date']})" if w["contract_type"] == "CDD" else ""
        lines.append(
            f"**{w['name']}** — {w['contract_type']}{expiry}\n"
            f"📞 {w['phone']} | Recovery: {w['recovery_balance']}d | {status}"
        )
    return "\n\n".join(lines)


def get_tasks_list() -> str:
    tasks = db.get_tasks()
    if not tasks:
        return "No tasks found."
    lines = []
    for t in tasks:
        emoji = {"PENDING": "⏳", "IN_PROGRESS": "🔄", "COMPLETED": "✅", "FAILED": "❌"}.get(
            t["status"], "❓"
        )
        lines.append(
            f"{emoji} **#{t['id']}** — {t['task_description']}\n"
            f"   Workers: {t['assigned_workers']} | ⏱ {t['estimated_duration']}h | {t['status']}"
        )
    return "\n\n".join(lines)


def get_stats() -> str:
    s = db.get_task_statistics()
    return (
        f"### 📊 Task Statistics\n\n"
        f"**Total:** {s['total']}\n\n"
        f"⏳ Pending: {s['pending']}\n"
        f"🔄 In Progress: {s['in_progress']}\n"
        f"✅ Completed: {s['completed']}\n"
        f"❌ Failed: {s['failed']}"
    )


def get_config_status() -> str:
    keys = {
        "Gemini API": config.get("GEMINI_API_KEY"),
        "Meta Token": config.get("META_ACCESS_TOKEN"),
        "WhatsApp Phone": config.get("WHATSAPP_PHONE_ID"),
        "Firebase URL": config.get("FIREBASE_DB_URL"),
    }
    lines = [f"{'✅' if v else '❌'} {k}" for k, v in keys.items()]
    return "### 🔑 API Configuration\n" + "\n".join(lines)


def dispatch_task(description: str, workers_csv: str, duration: int) -> str:
    if not description.strip():
        return "❌ Enter a task description."
    if not workers_csv.strip():
        return "❌ Specify at least one worker phone."

    task_id = db.add_task(description.strip(), workers_csv.strip(), int(duration) if duration else 2)
    if not task_id:
        return "❌ Failed to create task."

    # Attempt WhatsApp dispatch — best effort only
    try:
        from whatsapp_handler import WhatsAppHandler
        wa = WhatsAppHandler()
        phones = [p.strip() for p in workers_csv.replace(" ", "").split(",") if p.strip()]
        for phone in phones:
            wa.send_task_assignment(
                phone,
                phone,  # fallback name
                description.strip(),
                int(duration) if duration else 2,
            )
    except Exception:
        pass  # WhatsApp may not be configured

    return f"✅ **Task #{task_id}** dispatched!\n\n📝 {description}\n👷 {workers_csv}\n⏱ {duration or 2}h"


def save_keys(gemini: str, meta: str, phone: str, fb: str) -> str:
    if gemini:
        config.set("GEMINI_API_KEY", gemini)
    if meta:
        config.set("META_ACCESS_TOKEN", meta)
    if phone:
        config.set("WHATSAPP_PHONE_ID", phone)
    if fb:
        config.set("FIREBASE_DB_URL", fb)
    config.save()
    return "✅ Config saved!"


def refresh_all():
    return get_workers_list(), get_tasks_list(), get_stats(), get_config_status()


demo = gr.Blocks(title="CMMS Électrique")

with demo:
    gr.Markdown("# ⚡ CMMS Électrique — Factory Maintenance")
    gr.Markdown("*Algerian cable factory · Law 18-07 compliant · Bilingual AR/EN*")

    # ── Dashboard ──
    with gr.Tab("📊 Dashboard"):
        with gr.Row():
            workers_md = gr.Markdown(get_workers_list())
        with gr.Row():
            with gr.Column(scale=2):
                stats_md = gr.Markdown(get_stats())
            with gr.Column(scale=1):
                config_md = gr.Markdown(get_config_status())

    # ── Tasks ──
    with gr.Tab("📝 Tasks"):
        tasks_md = gr.Markdown(get_tasks_list())

    # ── Dispatch ──
    with gr.Tab("🚀 Dispatch"):
        desc_in = gr.Textbox(label="Task Description", placeholder="e.g., Replace faulty breaker Panel #3", lines=3)
        with gr.Row():
            workers_in = gr.Textbox(
                label="Worker Phones (comma separated)", placeholder="+213555000001, +213555000002", scale=2
            )
            dur_in = gr.Number(label="Duration (hours)", value=2, minimum=1, maximum=24, scale=1)
        dispatch_btn = gr.Button("🚀 Dispatch via WhatsApp", variant="primary")
        result_md = gr.Markdown("")

    # ── Settings ──
    with gr.Tab("🔧 Settings"):
        gemini_in = gr.Textbox(label="Gemini API Key", type="password", value=config.get("GEMINI_API_KEY") or "")
        meta_in = gr.Textbox(label="Meta Access Token", type="password", value=config.get("META_ACCESS_TOKEN") or "")
        phone_in = gr.Textbox(label="WhatsApp Phone ID", type="password", value=config.get("WHATSAPP_PHONE_ID") or "")
        fb_in = gr.Textbox(label="Firebase DB URL", type="password", value=config.get("FIREBASE_DB_URL") or "")
        save_btn = gr.Button("💾 Save")
        save_md = gr.Markdown("")

    # ── About ──
    with gr.Tab("ℹ️ About"):
        gr.Markdown(
            "**Tech Stack:** Python 3.12 · CustomTkinter · SQLite · Firebase RTDB · "
            "Meta WhatsApp API v22.0 · Gemini 2.0 Flash\n\n"
            "**Run desktop GUI:** `pip install -r requirements.txt && python main.py`\n\n"
            "**Docker:** `docker compose up --build`\n\n"
            "[GitHub](https://github.com/jooooniiiiii-lab/cmms-elec-mvp)"
        )

    # ── Events ──
    demo.load(fn=refresh_all, outputs=[workers_md, tasks_md, stats_md, config_md])

    dispatch_btn.click(
        fn=dispatch_task,
        inputs=[desc_in, workers_in, dur_in],
        outputs=[result_md],
    ).then(fn=get_tasks_list, outputs=[tasks_md]).then(fn=get_stats, outputs=[stats_md])

    save_btn.click(fn=save_keys, inputs=[gemini_in, meta_in, phone_in, fb_in], outputs=[save_md])

# Mount Gradio on FastAPI (same pattern as working HF Docker Spaces)
from fastapi import FastAPI

app = FastAPI(title="CMMS Électrique")
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = 7860
    print(f"[CMMS] Starting uvicorn on 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
