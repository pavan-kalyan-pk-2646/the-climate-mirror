
# 🌍 The Climate Mirror — v2 (Refactored)

An agentic AI climate intelligence platform that analyses personal/national climate
inputs and generates multi-agent outputs: risk scores, action plans, disaster
assessments, policy recommendations, and personalised 2050 narratives.

---

## 🆕 What's New in v2

| Area | v1 | v2 |
|---|---|---|
| **Security** | `SESSION_COOKIE_SECURE=False`, no CSRF | Secure cookies in prod, Flask-WTF CSRF, input validation |
| **Architecture** | 1 × 1 115-line `app.py` | Factory pattern: `app.py` + `routes.py` + `models.py` + `utils.py` + `agents/` |
| **Database** | Raw `sqlite3` calls, no ORM | SQLAlchemy ORM with proper relational models |
| **Agents** | Monolithic functions inside `app.py` | Dedicated modules: `analyzer.py`, `advisor.py`, `disaster.py`, `story.py`, `forecast.py` |
| **Validation** | Minimal `safe_float()` | Full username/password/country validation in `utils.py` |
| **Error handling** | Sparse | `try/except` + `logger.error()` on every DB write and route |
| **Configuration** | Hard-coded | Environment variables via `.env.example` |
| **Deployment** | Debug mode unclear | `FLASK_ENV=production` enables HTTPS-only cookies automatically |

---

## 📁 Project Structure

```
THE_CLIMATE_MIRROR_V2/
├── app.py              # Flask factory (create_app), extension init, entry point
├── routes.py           # All URL routes (Blueprint)
├── models.py           # SQLAlchemy ORM models: User, HistoryRecord, Note, ChatLog, AgentRun
├── utils.py            # Shared utilities: rate limiter, validators, climate core model
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
│
├── agents/             # One file per agent — import and call from routes.py
│   ├── __init__.py
│   ├── analyzer.py     # Agent 1 — deep factor analysis
│   ├── advisor.py      # Agent 2 — prioritised action plan
│   ├── disaster.py     # Agent 3 — 6-category disaster risk matrix
│   ├── story.py        # Agent 4 — personalised 2050 narrative
│   └── forecast.py     # Agent 6 — linear regression trend projection
│
├── templates/          # Jinja2 HTML templates (unchanged from v1)
├── static/             # Images, CSS, JS
└── videos/             # MP4 assets (not included in source zip)
```

---

## 🚀 Quick Start

```bash
# 1. Clone / extract
cd THE_CLIMATE_MIRROR_V2

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY at minimum

# 5. Run (development)
python app.py
```

Visit `http://localhost:5000`

---

## 🔐 Security Checklist (Pre-Deployment)

- [ ] Set a strong random `SECRET_KEY` in `.env`
- [ ] Set `FLASK_ENV=production` to enable `SESSION_COOKIE_SECURE=True`
- [ ] Serve behind HTTPS (nginx + Let's Encrypt, or any cloud provider)
- [ ] Set `DATABASE_URL` to PostgreSQL for production
- [ ] Review `MAX_CONTENT_LENGTH` — currently 1MB

---

## 🤖 Agent Architecture

All agents are pure Python functions — no classes, no side effects, easy to unit test.

```
orchestrate()               ← entry point in routes.py
    ├── analyze()           ← agents/analyzer.py
    ├── advise()            ← agents/advisor.py
    ├── assess()            ← agents/disaster.py
    ├── policy_for()        ← routes.py (country policy dict)
    ├── comparator_agent()  ← routes.py (history comparison)
    ├── narrate()           ← agents/story.py
    └── project()           ← agents/forecast.py
```

To add a new agent:
1. Create `agents/my_agent.py` with a function `def run(...) -> dict`
2. Import it in `routes.py`: `from agents.my_agent import run`
3. Call it inside `orchestrate()` and add its output to the return dict

---

## 🗄️ Database Models

| Model | Key Fields |
|---|---|
| `User` | `username`, `password` (hashed), `created_at` |
| `HistoryRecord` | All 4 climate inputs, `temp`, `score`, JSON agent outputs, `created_at` |
| `Note` | `username`, `title`, `content` |
| `ChatLog` | `username`, `message`, `response` |
| `AgentRun` | `history_id`, `orchestrator_log` (JSON), `total_agents_run` |

---

## 🧪 Running Tests (example)

```bash
pip install pytest
pytest tests/
```

Example test structure:
```python
# tests/test_analyzer.py
from agents.analyzer import analyze

def test_high_emission():
    result = analyze(90, 50, 30, 40, 3.2, "India")
    assert result["severity"] in ("High", "Critical")
    assert result["dominant"]["name"] == "Energy Use"  # energy has highest weighted value
