# CMMS Électrique — Factory Maintenance Management System

<a href="https://huggingface.co/spaces/jooooniiiiii-lab/cmms-elec-mvp">
  <img src="https://img.shields.io/badge/🤗%20Hugging%20Face-Space-blue" alt="Hugging Face Space">
</a>

Desktop application for managing **5 electrical technicians** at an Algerian industrial cable factory. Bilingual (Arabic + English), local-first, and compliant with **Law 18-07** for personal data protection.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CMMS Desktop App                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Dashboard │  │ Task Manager │  │ Settings          │   │
│  │ (workers) │  │ (dispatch)   │  │ (API keys)        │   │
│  └─────┬─────┘  └──────┬───────┘  └────────┬─────────┘   │
│        └───────────────┬┴───────────────────┘             │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Local SQLite Database                    │  │
│  │  workers (CDD/CDI, recovery_balance)                 │  │
│  │  tasks (PENDING/IN_PROGRESS/COMPLETED/FAILED)        │  │
│  └─────────────────────────────────────────────────────┘  │
│                        │                                   │
│  ┌─────────────────────┼─────────────────────────────┐    │
│  │  WhatsApp Handler   │  Firebase Bridge             │    │
│  │  (Meta API v22.0)   │  (REST polling, 5s)         │    │
│  └──────────┬──────────┘  └──────────┬────────────────┘    │
│             │                         │                     │
│             ▼                         ▼                     │
│        ┌─────────┐            ┌──────────┐                  │
│        │  Gemini  │◄──────────│ Firebase  │                  │
│        │  Agent   │           │   RTDB    │                  │
│        └─────────┘            └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Protection (Law 18-07)
- **ALL** worker profiles, contracts, and task records stored **only** in local SQLite
- Firebase RTDB = **ephemeral transit buffer** — messages deleted immediately after processing
- API keys stored in local `config.json` — no cloud credential storage

## Quick Start

### Local (Python)

```bash
pip install -r requirements.txt
python main.py
```

### Docker (requires X server)

```bash
# Linux with X11
docker compose up --build

# Or plain Docker
docker build -t cmms-elec .
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v ./config.json:/app/config.json \
  -v ./local_factory.db:/app/local_factory.db \
  cmms-elec
```

### Windows (Docker)
1. Install **VcXsrv** or enable **WSLg**
2. Set `DISPLAY=host.docker.internal:0`
3. `docker compose up --build`

### macOS (Docker)
1. Install **XQuartz**
2. Enable "Allow connections from network clients"
3. `export DISPLAY=host.docker.internal:0`
4. `docker compose up --build`

## Configuration

Configure these **4 API keys** in the Settings tab:

| Key | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini 2.0 Flash (message classification) |
| `META_ACCESS_TOKEN` | Meta WhatsApp Cloud API access token |
| `WHATSAPP_PHONE_ID` | WhatsApp Business phone number ID |
| `FIREBASE_DB_URL` | Firebase Realtime Database URL |

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| GUI Framework | CustomTkinter (dark/green theme) |
| Database | SQLite (WAL mode, local-first) |
| AI Classification | Google Gemini 2.0 Flash |
| Messaging | Meta WhatsApp Cloud API v22.0 |
| Transit Buffer | Firebase Realtime DB (REST) |

## Project Structure

```
cmms-elec-mvp/
├── main.py                 # Entry point — orchestrates all subsystems
├── config.py               # ConfigManager — thread-safe JSON config
├── database.py             # DatabaseManager — SQLite CRUD + seed data
├── gemini_agent.py         # GeminiAgent — AI status classifier
├── whatsapp_handler.py     # WhatsAppHandler — Meta Cloud API sender
├── firebase_bridge.py      # FirebaseBridge — REST polling listener
├── space_web.py            # HF Space web info page
├── gui/
│   ├── app.py              # MainApp — CTk window (1000x700)
│   ├── dashboard_tab.py    # Worker grid, task progress, stats
│   ├── task_manager_tab.py # Task dispatch with WhatsApp
│   └── settings_tab.py     # API key management
├── Dockerfile              # Local desktop Docker image
├── Dockerfile.huggingface  # HF Space Docker image
├── docker-compose.yml      # Local Docker Compose
├── requirements.txt
└── .gitignore
```

## License

MIT
