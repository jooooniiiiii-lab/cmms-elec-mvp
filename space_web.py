#!/usr/bin/env python3
"""
space_web.py — Hugging Face Space web info page
Serves a project information page on port 7860 when deployed on HF Spaces.
The actual desktop app runs locally using the standard Dockerfile.
"""

import http.server
import json
import os
import sys

PORT = 7860


def get_project_info() -> dict:
    from datetime import datetime

    repo_url = "https://github.com/jooooniiiiii-lab/cmms-elec-mvp"
    return {
        "project": "CMMS Électrique — Factory Maintenance Management System",
        "version": "1.0.0",
        "description": (
            "Desktop application for managing 5 electrical technicians at "
            "an Algerian industrial cable factory. Compliant with Law 18-07 "
            "for personal data protection."
        ),
        "tech_stack": [
            "Python 3.12",
            "CustomTkinter (dark/green theme)",
            "SQLite (local-first, Law 18-07 compliant)",
            "Firebase RTDB (ephemeral transit buffer only)",
            "Meta WhatsApp Cloud API v22.0",
            "Google Gemini 2.0 Flash",
        ],
        "features": [
            "Worker management (CDD/CDI contracts, expiry tracking)",
            "Task dispatching via WhatsApp",
            "AI-powered status classification via Gemini",
            "Firebase message bridge (auto-deleted after processing)",
            "Bilingual UI (Arabic + English)",
            "Recovery balance tracking per technician",
        ],
        "how_to_run": {
            "desktop_local": [
                f"{'pip install -r requirements.txt'}",
                f"{'python main.py'}",
            ],
            "docker_local": [
                f"{'# Build and run with Docker Compose (requires X server)'}",
                f"{'docker compose up --build'}",
                "",
                f"{'# Or with plain Docker (Linux with X11):'}",
                f"{'docker build -t cmms-elec .'}",
                f"{'docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix cmms-elec'}",
            ],
            "config_required": [
                "GEMINI_API_KEY — Google Gemini API key",
                "META_ACCESS_TOKEN — Meta WhatsApp API token",
                "WHATSAPP_PHONE_ID — WhatsApp Business phone ID",
                "FIREBASE_DB_URL — Firebase Realtime Database URL",
            ],
        },
        "links": {
            "github": repo_url,
            "documentation": f"{repo_url}#readme",
        },
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


class InfoHandler(http.server.BaseHTTPRequestHandler):
    """Serves a styled HTML page with project information."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        info = get_project_info()
        html = self._build_html(info)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _build_html(self, info: dict) -> str:
        tech_badges = "".join(
            f'<span class="badge">{t}</span>' for t in info["tech_stack"]
        )
        features_list = "".join(
            f'<li>✅ {f}</li>' for f in info["features"]
        )

        run_commands = ""
        for section, cmds in info["how_to_run"].items():
            cmd_html = "".join(
                f'<code>{c}</code><br>'.replace("{", "&#123;").replace("}", "&#125;")
                for c in cmds
            )
            run_commands += f"<h3>{section.replace('_', ' ').title()}</h3><div class='code-block'>{cmd_html}</div>"

        config_items = "".join(
            f'<li><strong>{k}</strong> — {v}</li>'
            for k, v in [c.split(" — ", 1) for c in info["how_to_run"]["config_required"]]
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{info["project"]}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    line-height: 1.6;
  }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
  h1 {{ font-size: 2rem; color: #58a6ff; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.4rem; color: #f0f6fc; margin: 2rem 0 1rem; }}
  h3 {{ color: #8b949e; margin: 1.5rem 0 0.5rem; }}
  .subtitle {{ color: #8b949e; font-size: 1.1rem; margin-bottom: 2rem; }}
  .badge {{
    display: inline-block;
    background: #1f2937;
    color: #58a6ff;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    margin: 0.25rem;
    border: 1px solid #30363d;
  }}
  .code-block {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1rem;
    margin: 0.5rem 0;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9rem;
    line-height: 1.8;
  }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 0.3rem 0; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #30363d; color: #8b949e; font-size: 0.9rem; }}
  .compliance {{ background: #1a2332; border-left: 3px solid #58a6ff; padding: 1rem; margin: 1.5rem 0; border-radius: 0 6px 6px 0; }}
</style>
</head>
<body>
<div class="container">
  <h1>⚡ {info["project"]}</h1>
  <p class="subtitle">{info["description"]}</p>

  <div class="compliance">
    <strong>🔒 Law 18-07 Compliant</strong><br>
    All worker data stored locally in SQLite.<br>
    Firebase used exclusively as ephemeral transit — messages deleted after processing.
  </div>

  <h2>🛠 Tech Stack</h2>
  <div>{tech_badges}</div>

  <h2>✨ Features</h2>
  <ul>{features_list}</ul>

  <h2>🚀 Running Locally</h2>
  {run_commands}

  <h2>🔑 Required Configuration</h2>
  <ul>{config_items}</ul>

  <h2>📦 Links</h2>
  <ul>
    <li>🔗 <a href="{info['links']['github']}" target="_blank">GitHub Repository</a></li>
  </ul>

  <div class="footer">
    Last updated: {info['last_updated']} | Version {info['version']}
  </div>
</div>
</body>
</html>"""


def main():
    server = http.server.HTTPServer(("0.0.0.0", PORT), InfoHandler)
    print(f"[Space] Serving on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
