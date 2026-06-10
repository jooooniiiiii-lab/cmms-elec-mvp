"""
app.py — Gradio web interface for CMMS Électrique
Used when deployed on Hugging Face Spaces (SDK: Gradio).
The desktop GUI (CustomTkinter) runs locally via python main.py.
"""

import os
from datetime import datetime

import gradio as gr

PROJECT_INFO = {
    "project": "CMMS Electrique -- Factory Maintenance Management System",
    "version": "1.0.0",
    "description": (
        "Desktop application for managing **5 electrical technicians** at "
        "an Algerian industrial cable factory. Bilingual (Arabic + English), "
        "local-first, and compliant with **Law 18-07** for personal data protection."
    ),
    "tech_stack": [
        ("Python 3.12", "🐍"),
        ("CustomTkinter", "🖥️"),
        ("SQLite (local)", "🗄️"),
        ("Firebase RTDB", "🔥"),
        ("Meta WhatsApp API v22.0", "💬"),
        ("Google Gemini 2.0 Flash", "🤖"),
    ],
    "features": [
        "Worker management (CDD/CDI contracts with expiry tracking)",
        "Task dispatching via WhatsApp with Arabic messages",
        "AI-powered status classification via Gemini",
        "Firebase message bridge (auto-deleted after processing)",
        "Bilingual UI (Arabic + English)",
        "Recovery balance tracking per technician",
    ],
    "architecture": """
```
+--------------------------+
|      CMMS Desktop App     |
|  +---------+ +---------+ |
|  |Dashboard| |Task Mgr | |
|  +----+----+ +----+----+ |
|       +-------+----+     |
|               |          |
|      +--------+--------+ |
|      |  Local SQLite   | |
|      +--------+--------+ |
|    +---------+ +------+  |
|    |WhatsApp | |Fireb.|  |
|    |Handler  | |Bridge|  |
|    +----+----+ +--+---+  |
|         |          |     |
|    +----+---+ +----+---+ |
|    | Gemini | | Firebase| |
|    | Agent  | |  RTDB   | |
|    +--------+ +--------+ |
+--------------------------+
```""",
    "how_to_run": """### Local (Python)
```bash
pip install -r requirements.txt
python main.py
```

### Docker (requires X server)
```bash
docker compose up --build
```

### Configure 4 API keys in Settings tab:
- GEMINI_API_KEY -- Google Gemini
- META_ACCESS_TOKEN -- Meta WhatsApp
- WHATSAPP_PHONE_ID -- WhatsApp Business
- FIREBASE_DB_URL -- Firebase RTDB""",
}


def build_tabs():
    with gr.Blocks(
        title=PROJECT_INFO["project"],
        theme=gr.themes.Monochrome(primary_hue="blue", neutral_hue="slate"),
        css="footer { display: none !important; }",
    ) as demo:
        gr.Markdown(f"# ⚡ {PROJECT_INFO['project']}")
        gr.Markdown(f"*{PROJECT_INFO['description']}*")

        with gr.Tab("Overview"):
            gr.Markdown("## Tech Stack")
            tech_md = "\n".join(
                f"- {emoji} {name}" for name, emoji in PROJECT_INFO["tech_stack"]
            )
            gr.Markdown(tech_md)

            gr.Markdown("## Features")
            feat_md = "\n".join(f"- {f}" for f in PROJECT_INFO["features"])
            gr.Markdown(feat_md)

            gr.Markdown("## Law 18-07 Compliance")
            gr.Markdown(
                "> All worker data stored **locally** in SQLite. "
                "Firebase used as **ephemeral transit** -- messages deleted after processing."
            )

        with gr.Tab("Architecture"):
            gr.Markdown(PROJECT_INFO["architecture"])

        with gr.Tab("Usage"):
            gr.Markdown(PROJECT_INFO["how_to_run"])

        with gr.Tab("Links"):
            gr.Markdown(
                "- [GitHub Repository](https://github.com/jooooniiiiii-lab/cmms-elec-mvp)\n"
                "- License: MIT\n"
                f"- Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            )

        gr.Markdown("---")
        gr.Markdown(
            f"*Version {PROJECT_INFO['version']} -- "
            "Run `python main.py` locally for the full desktop GUI*"
        )

    return demo


demo = build_tabs()

if __name__ == "__main__":
    demo.launch()
