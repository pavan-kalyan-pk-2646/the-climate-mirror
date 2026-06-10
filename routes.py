"""
routes.py — All Flask routes for The Climate Mirror.
Business logic lives in agents/ and utils.py; DB models in models.py.
"""
import json
import logging
import random
import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request,
    redirect, session, jsonify, send_from_directory,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, HistoryRecord, Note, ChatLog, AgentRun
from utils import (
    rate_limit, safe_float, sanitise_country,
    validate_username, validate_password,
    predict_climate, eco_score,
)
from agents.analyzer import analyze
from agents.advisor  import advise
from agents.disaster import assess
from agents.story    import narrate
from agents.forecast import project as forecast_project

logger = logging.getLogger(__name__)
bp     = Blueprint("main", __name__)

# ── COUNTRY POLICIES ──────────────────────────────────────
COUNTRY_POLICIES = {
    "India": {
        "flag": "🇮🇳", "gdp_context": "emerging economy",
        "current": "500 GW renewable target by 2030; Net Zero by 2070; PM Surya Ghar solar scheme",
        "gaps": "Coal still 70% of electricity; agricultural methane rising; rapid urbanisation",
        "actions": [
            "Accelerate 500 GW renewable target — currently tracking to achieve by 2027",
            "National EV policy: 30% EV sales mandate by 2030 for 2/3-wheelers",
            "Green hydrogen mission: $2.3B invested — scale up to 5Mt/year by 2030",
            "Protect Eastern Himalayan glaciers — freshwater security for 600M people",
            "Climate-smart agriculture programme covering 15M farmers by 2028",
        ],
    },
    "USA": {
        "flag": "🇺🇸", "gdp_context": "world's largest economy",
        "current": "Inflation Reduction Act: $369B climate investment; 43% emissions cut by 2035",
        "gaps": "Oil & gas production at record highs; methane regulation inconsistent; no carbon price",
        "actions": [
            "Implement federal carbon price — IRA incentives alone insufficient for 1.5°C",
            "Phase out fossil fuel subsidies ($20B/year) and redirect to clean energy",
            "Electrify federal vehicle fleet fully by 2030 — 650,000 vehicles",
            "Restore and expand national forests — absorbing less CO₂ due to drought",
            "Rejoin and lead international climate finance — $100B/year commitment",
        ],
    },
    "China": {
        "flag": "🇨🇳", "gdp_context": "world's largest emitter",
        "current": "Net Zero 2060; peak emissions 2030; world's #1 renewable installer",
        "gaps": "Still building new coal plants; BRI projects often carbon-intensive",
        "actions": [
            "Bring forward peak emissions to 2025 — technology now allows it",
            "Halt all new domestic coal plant approvals immediately",
            "Expand ETS (carbon trading) to cover all sectors including agriculture",
            "Make Belt & Road Initiative 100% green finance from 2026",
            "Deploy 1,200 GW of solar/wind by 2030 — currently on track",
        ],
    },
    "Germany": {
        "flag": "🇩🇪", "gdp_context": "Europe's largest economy",
        "current": "56% renewable electricity; Energiewende policy; coal phase-out by 2038",
        "gaps": "Re-opened coal plants post-Ukraine; natural gas dependency; slow building retrofits",
        "actions": [
            "Accelerate coal phase-out to 2030 — technically and economically feasible",
            "Deploy heat pump programme: 6M households/year, not current 1M target",
            "Hydrogen import strategy: North Africa and Australia partnerships critical",
            "Building retrofit law: mandate 35% energy efficiency improvement by 2030",
            "Lead EU carbon border mechanism expansion to cover more sectors",
        ],
    },
    "Brazil": {
        "flag": "🇧🇷", "gdp_context": "largest Latin American economy",
        "current": "85% renewable electricity; Amazon Fund reinstated; Net Zero by 2050 pledge",
        "gaps": "Amazon deforestation still occurring; beef industry emissions; Cerrado destruction",
        "actions": [
            "Achieve zero illegal deforestation in Amazon by 2026 — critical global tipping point",
            "Expand Cerrado protection — 50% already converted, affects global rainfall",
            "Decarbonise beef supply chain — Brazil's #1 export and emission source",
            "Green bonds to fund Amazon restoration at $10B/year scale",
            "Lead Global Biodiversity Framework implementation — Brazil hosts 20% of species",
        ],
    },
    "Australia": {
        "flag": "🇦🇺", "gdp_context": "high per-capita emitter",
        "current": "43% emission cut by 2030; Safeguard Mechanism; 82% renewable electricity target",
        "gaps": "World's largest coal and LNG exporter; high per-capita emissions; slow EV uptake",
        "actions": [
            "Stop approving new coal and gas projects — exported emissions are still Australia's responsibility",
            "Accelerate offshore wind: 10+ GW in pipeline, permitting bottlenecks must be resolved",
            "EV mandate: follow EU model with 100% ZEV sales target by 2035",
            "Price carbon at the border: match EU's CBAM to prevent carbon leakage",
            "First Nations-led land management: traditional burning reduces wildfire risk 40%",
        ],
    },
}
DEFAULT_POLICY = {
    "flag": "🌍", "gdp_context": "this nation",
    "current": "Various national pledges under the Paris Agreement framework",
    "gaps": "Implementation gap between pledges and action remains significant globally",
    "actions": [
        "Establish or strengthen a national carbon price mechanism",
        "Phase out fossil fuel subsidies and redirect to clean energy investment",
        "Set science-based emission reduction targets aligned with 1.5°C",
        "Invest in climate education and green skills for the workforce",
        "Join international climate finance commitments for developing nations",
    ],
}

# ── LIVE METRICS ──────────────────────────────────────────
_live = {"co2": 414.2, "temp": 1.42, "sea": 3.31, "ch4": 1910, "ice": 4.72, "forest": 4.0}

# ── HELPERS ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def policy_for(country, e, en, t, i, temp, analysis):
    pol = COUNTRY_POLICIES.get(country, DEFAULT_POLICY)
    urgent = []
    if e > 60:  urgent.append(f"⚡ URGENT: Carbon emissions ({e}/100) require immediate industrial policy action.")
    if en > 60: urgent.append(f"⚡ URGENT: Energy index ({en}/100) requires emergency renewable deployment.")
    if t > 60:  urgent.append(f"⚡ URGENT: Transport ({t}/100) requires national EV and transit strategy.")
    if i > 60:  urgent.append(f"⚡ URGENT: Industry ({i}/100) requires mandatory green manufacturing standards.")
    return {
        "country": country,
        "flag":    pol["flag"],
        "context": pol["gdp_context"],
        "current": pol["current"],
        "gaps":    pol["gaps"],
        "actions": pol["actions"],
        "urgent":  urgent,
    }


def comparator_agent(username, temp, score, e, en, t, i, history_records):
    if not history_records:
        return {
            "trend": "first run",
            "vs_last": None,
            "vs_best": None,
            "score_context": "This is your first simulation — a baseline has been established.",
            "percentile": None,
        }
    temps  = [r["temp"]  for r in history_records]
    scores = [r["score"] for r in history_records if r.get("score")]
    last   = history_records[0]
    best_temp  = min(temps)
    vs_last = round(temp - last["temp"], 2)
    vs_best = round(temp - best_temp, 2)
    below      = sum(1 for t_ in temps if t_ > temp)
    percentile = int((below / len(temps)) * 100) if temps else 50
    if vs_last < -0.2:
        trend = "improving"
        score_context = f"Your eco score ({score}/100) improved vs your last run ({last.get('score','?')}/100). Excellent progress!"
    elif vs_last > 0.2:
        trend = "worsening"
        score_context = f"Your eco score ({score}/100) dropped vs last run ({last.get('score','?')}/100). Review your highest factor."
    else:
        trend = "stable"
        score_context = f"Eco score holding steady at {score}/100. Try reducing your dominant factor to break through."
    if vs_best < 0:
        score_context += " 🏆 NEW PERSONAL BEST — this is your lowest temperature run!"
    elif vs_best < 0.3:
        score_context += f" You're close to your personal best (+{best_temp}°C)."
    return {
        "trend": trend, "vs_last": vs_last, "vs_best": vs_best,
        "best_temp": best_temp, "worst_temp": max(temps),
        "last_temp": last["temp"], "total_runs": len(history_records),
        "score_context": score_context, "percentile": percentile,
    }


def orchestrate(username, country, e, en, t, i, history_records=None):
    """Run all agents in sequence and return full outputs dict."""
    log = []
    log.append(f"[ORCHESTRATOR] Starting pipeline for {username} / {country}")

    temp, impact, color, raw_score = predict_climate(e, en, t, i)
    score = eco_score(e, en, t, i)

    analysis   = analyze(e, en, t, i, temp, country)
    advice     = advise(e, en, t, i, temp, country, analysis)
    disasters  = assess(temp, e, en, t, i, analysis)
    policy     = policy_for(country, e, en, t, i, temp, analysis)
    comparator = comparator_agent(username, temp, score, e, en, t, i, history_records or [])
    story      = narrate(username, country, temp, e, en, t, i, analysis, disasters, comparator)
    forecast   = forecast_project(history_records or [], temp, score)

    dominant = analysis["dominant"]
    summary = (
        f"AI orchestrated 8 agents in sequence. "
        f"{impact} detected for {country} — +{temp}°C projected rise. "
        f"Dominant driver: {dominant['name']} ({dominant['value']}/100). "
        f"Eco score: {score}/100. "
        f"Highest disaster risk: {disasters['highest'].upper()} ({disasters['risks'][disasters['highest']]}%). "
        f"Trend: {comparator['trend']}."
    )
    log.append("[ORCHESTRATOR] Pipeline complete — all 8 agents finished.")

    return {
        "temp": temp, "impact": impact, "color": color,
        "score": score, "summary": summary,
        "analysis": analysis, "advice": advice, "disasters": disasters,
        "policy": policy, "comparator": comparator, "story": story,
        "forecast": forecast, "orchestrator_log": log, "agents_run": 8,
    }


# ═════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ═════════════════════════════════════════════════════════
@bp.route("/")
def root(): return redirect("/intro")

@bp.route("/intro")
def intro(): return render_template("intro.html", user=session.get("user", ""))

@bp.route("/home")
def home(): return render_template("home.html", user=session.get("user", ""))

@bp.route("/narrative")
def narrative(): return render_template("narrative.html", user=session.get("user", ""))

@bp.route("/image")
def image(): return render_template("image.html", user=session.get("user", ""))

@bp.route("/videos/<path:fn>")
def serve_video(fn):
    import os
    VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    return send_from_directory(VIDEO_DIR, secure_filename(fn))


# ═════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═════════════════════════════════════════════════════════
@bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd   = request.form.get("password", "").strip()
        error = validate_username(uname) or validate_password(pwd)
        if not error:
            try:
                user = User(username=uname, password=generate_password_hash(pwd))
                db.session.add(user)
                db.session.commit()
                return redirect("/login")
            except Exception:
                db.session.rollback()
                error = "Username already exists."
    return render_template("register.html", error=error)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd   = request.form.get("password", "")
        user  = User.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password, pwd):
            session["user"] = user.username
            logger.info("Login success: %s", uname)
            return redirect("/stories")
        logger.warning("Login failed: %s", uname)
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ═════════════════════════════════════════════════════════
#  PROTECTED PAGES
# ═════════════════════════════════════════════════════════
@bp.route("/stories")
@login_required
def stories(): return render_template("stories.html", user=session["user"])

@bp.route("/behaviors")
@login_required
def behaviors(): return render_template("behavior_mirror.html", user=session["user"])

@bp.route("/disaster")
@login_required
def disaster(): return render_template("disaster.html", user=session["user"])

@bp.route("/notebook")
@login_required
def notebook():
    notes = Note.query.filter_by(username=session["user"]).order_by(Note.id.desc()).limit(10).all()
    return render_template("notebook.html", user=session["user"],
                           notes=[{"id": n.id, "title": n.title, "content": n.content, "created": n.created_at} for n in notes])

@bp.route("/save_note", methods=["POST"])
@login_required
def save_note():
    try:
        note = Note(
            username=session["user"],
            title=request.form.get("title", "Untitled")[:200],
            content=request.form.get("content", "")[:5000],
        )
        db.session.add(note)
        db.session.commit()
    except Exception as exc:
        logger.error("save_note error: %s", exc)
        db.session.rollback()
    return redirect("/notebook")


# ═════════════════════════════════════════════════════════
#  CLIMATE DASHBOARD
# ═════════════════════════════════════════════════════════
@bp.route("/climate")
@login_required
def climate():
    records = (HistoryRecord.query
               .filter_by(username=session["user"])
               .order_by(HistoryRecord.id.desc())
               .limit(8).all())
    recs = [r.to_dict() for r in records]
    cur_temp  = recs[0]["temp"]  if recs else 2.0
    cur_score = recs[0]["score"] if recs else 50
    forecast  = forecast_project(recs, cur_temp, cur_score)
    total     = HistoryRecord.query.filter_by(username=session["user"]).count()
    dates     = db.session.execute(
        db.text("SELECT DISTINCT DATE(created_at) as d FROM history WHERE username=:u ORDER BY d DESC"),
        {"u": session["user"]},
    ).fetchall()
    return render_template("climate.html",
        user=session["user"],
        dates=[str(d[0]) for d in dates],
        total_simulations=total,
        last_record=recs[0] if recs else None,
        ai_forecast=forecast["label"],
    )


# ═════════════════════════════════════════════════════════
#  PREDICT — ORCHESTRATOR ENTRY POINT
# ═════════════════════════════════════════════════════════
@bp.route("/predict", methods=["POST"])
@login_required
def predict():
    if not rate_limit(session["user"], limit_seconds=3):
        logger.warning("Rate limit hit: %s", session["user"])
        return "Too many requests. Please wait a moment.", 429

    try:
        e  = safe_float(request.form.get("emission",  0))
        en = safe_float(request.form.get("energy",    0))
        t  = safe_float(request.form.get("transport", 0))
        i  = safe_float(request.form.get("industry",  0))
        country = sanitise_country(request.form.get("country", "India"))

        prev = (HistoryRecord.query
                .filter_by(username=session["user"])
                .order_by(HistoryRecord.id.desc())
                .limit(10).all())
        history_records = [r.to_dict() for r in prev]

        out = orchestrate(session["user"], country, e, en, t, i, history_records)

        record = HistoryRecord(
            username=session["user"], country=country,
            emission=e, energy=en, transport=t, industry=i,
            temp=out["temp"], impact=out["impact"], summary=out["summary"],
            agent_advice=json.dumps(out["advice"]),
            disaster_risk=json.dumps(out["disasters"]["risks"]),
            story=json.dumps(out["story"]),
            policy=json.dumps(out["policy"]),
            comparator=json.dumps(out["comparator"]),
            analysis=json.dumps(out["analysis"]),
            score=out["score"],
        )
        db.session.add(record)
        db.session.flush()

        agent_run = AgentRun(
            username=session["user"],
            history_id=record.id,
            orchestrator_log=json.dumps(out["orchestrator_log"]),
            total_agents_run=out["agents_run"],
        )
        db.session.add(agent_run)
        db.session.commit()

        today = datetime.date.today().isoformat()
        now   = datetime.datetime.now().strftime("%H:%M")
        return render_template("result.html",
            user=session["user"], country=country,
            e=e, en=en, t=t, i=i,
            temp=out["temp"], impact=out["impact"], color=out["color"],
            score=out["score"], summary=out["summary"],
            analysis=out["analysis"], advice=out["advice"],
            disasters=out["disasters"], policy=out["policy"],
            comparator=out["comparator"], story=out["story"],
            forecast=out["forecast"], orch_log=out["orchestrator_log"],
            agents_run=out["agents_run"], date=today, time=now,
        )
    except Exception as exc:
        logger.error("predict error: %s", exc, exc_info=True)
        db.session.rollback()
        return "An internal error occurred. Please try again.", 500


# ═════════════════════════════════════════════════════════
#  HISTORY
# ═════════════════════════════════════════════════════════
@bp.route("/history")
@login_required
def history():
    records = (HistoryRecord.query
               .filter_by(username=session["user"])
               .order_by(HistoryRecord.id.desc())
               .limit(30).all())
    rows = [r.to_dict() for r in records]
    cur_temp  = rows[0]["temp"]  if rows else 2.0
    cur_score = rows[0]["score"] if rows else 50
    forecast  = forecast_project(rows, cur_temp, cur_score) if rows else {"label": "No data yet.", "trend": "none"}
    return render_template("history.html", records=rows, user=session["user"], ai_forecast=forecast["label"])


@bp.route("/delete_record/<int:rid>", methods=["POST"])
@login_required
def delete_record(rid):
    try:
        record = HistoryRecord.query.filter_by(id=rid, username=session["user"]).first()
        if record:
            db.session.delete(record)
            db.session.commit()
    except Exception as exc:
        logger.error("delete_record error: %s", exc)
        db.session.rollback()
    return redirect("/history")


# ═════════════════════════════════════════════════════════
#  LEADERBOARD
# ═════════════════════════════════════════════════════════
@bp.route("/leaderboard")
@login_required
def leaderboard():
    rows = db.session.execute(db.text(
        "SELECT username, ROUND(AVG(score),1) as avg_score, COUNT(*) as runs, "
        "MIN(temp) as best_temp FROM history GROUP BY username ORDER BY avg_score DESC LIMIT 10"
    )).fetchall()
    return render_template("leaderboard.html", user=session["user"],
                           rows=[dict(r._mapping) for r in rows])


# ═════════════════════════════════════════════════════════
#  API ENDPOINTS
# ═════════════════════════════════════════════════════════
@bp.route("/api/live")
def api_live():
    _live["co2"]    = round(_live["co2"]    + random.uniform(-0.04, 0.09), 2)
    _live["temp"]   = round(min(2.1, max(1.3, _live["temp"] + random.uniform(-0.003, 0.006))), 3)
    _live["sea"]    = round(_live["sea"]    + random.uniform(-0.01, 0.05), 2)
    _live["ch4"]    = round(_live["ch4"]    + random.uniform(-0.8,  1.2),  1)
    _live["ice"]    = round(max(3.5, _live["ice"]    + random.uniform(-0.02, 0.01)), 2)
    _live["forest"] = round(max(3.0, _live["forest"] + random.uniform(-0.03, 0.01)), 2)
    return jsonify({
        "co2": _live["co2"], "temp": _live["temp"], "sea_level": _live["sea"],
        "methane": _live["ch4"], "arctic_ice": _live["ice"], "forest_loss": _live["forest"],
        "risk_index": random.randint(72, 90), "confidence": random.randint(94, 99),
        "renewables_pct": random.randint(29, 35), "deforestation": random.randint(8, 15),
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
    })


@bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    try:
        data = request.get_json() or {}
        q    = data.get("message", "").strip()[:500]
        if not q:
            return jsonify({"reply": "Please ask a question."})
        row = (HistoryRecord.query
               .filter_by(username=session["user"])
               .order_by(HistoryRecord.id.desc())
               .first())
        user_data = row.to_dict() if row else None
        # Simple keyword chat (original logic preserved)
        reply = _chat_response(q, user_data)
        log = ChatLog(username=session["user"], message=q, response=reply)
        db.session.add(log)
        db.session.commit()
        return jsonify({"reply": reply})
    except Exception as exc:
        logger.error("api_chat error: %s", exc)
        db.session.rollback()
        return jsonify({"reply": "An error occurred. Please try again."}), 500


@bp.route("/api/stats")
@login_required
def api_stats():
    rows = db.session.execute(db.text(
        "SELECT DATE(created_at) as date, ROUND(AVG(temp),2) as avg_temp, "
        "MAX(temp) as max_temp, MIN(temp) as min_temp, COUNT(*) as runs, "
        "ROUND(AVG(score),1) as avg_score FROM history "
        "WHERE username=:u GROUP BY DATE(created_at) ORDER BY date ASC LIMIT 14"
    ), {"u": session["user"]}).fetchall()
    return jsonify([dict(r._mapping) for r in rows])


@bp.route("/api/leaderboard")
def api_leaderboard():
    rows = db.session.execute(db.text(
        "SELECT username, ROUND(AVG(score),1) as avg_score, COUNT(*) as runs, "
        "MIN(temp) as best_temp FROM history GROUP BY username ORDER BY avg_score DESC LIMIT 10"
    )).fetchall()
    return jsonify([dict(r._mapping) for r in rows])


@bp.route("/api/agent_log/<int:hid>")
@login_required
def api_agent_log(hid):
    run = AgentRun.query.filter_by(history_id=hid, username=session["user"]).first()
    if not run:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"log": json.loads(run.orchestrator_log), "agents": run.total_agents_run})


# ═════════════════════════════════════════════════════════
#  VIEW BY DATE
# ═════════════════════════════════════════════════════════
@bp.route("/view/<date>")
@login_required
def view_date(date):
    rows = db.session.execute(db.text(
        "SELECT * FROM history WHERE username=:u AND DATE(created_at)=:d ORDER BY id DESC"
    ), {"u": session["user"], "d": date}).fetchall()
    records = [dict(r._mapping) for r in rows]
    return render_template("climate.html",
        user=session["user"], dates=[date],
        total_simulations=len(records),
        last_record=records[0] if records else None,
        ai_forecast=f"Viewing records for {date}",
        records=records, selected_date=date,
    )


# ─── MINIMAL CHAT LOGIC ───────────────────────────────────
def _chat_response(question: str, user_data: dict | None) -> str:
    q = question.lower()
    ctx = ""
    if user_data:
        ctx = (
            f" [Context: Your last run for {user_data.get('country','?')} showed "
            f"+{user_data.get('temp','?')}°C, {user_data.get('impact','?')}, "
            f"eco score: {user_data.get('score','?')}/100]"
        )
    topics = {
        "solar":        "☀️ Solar PV costs have fallen 90% since 2010 — now the cheapest electricity in history at $0.02/kWh in many regions.",
        "wind":         "🌬️ Wind now supplies 20%+ of global electricity. Offshore wind is growing fastest with turbines exceeding 15MW.",
        "electric":     "🚗 EVs will be cheaper to buy than petrol cars by 2026 in most markets due to falling battery costs.",
        "carbon":       "🏭 A $50/tonne carbon price drives meaningful industrial decarbonisation — the EU ETS is already there.",
        "temperature":  "🌡️ Every 0.1°C of warming beyond 1.5°C significantly increases extreme weather risk and ecosystem damage.",
        "deforestation":"🌲 Tropical forests absorb 2.6 billion tonnes of CO₂/year — more than the entire annual emissions of China.",
        "hydrogen":     "⚡ Green hydrogen made with renewable electricity is key for decarbonising steel, shipping, and aviation.",
        "coal":         "🏭 Coal must phase out by 2040 globally to stay below 2°C. It's the single largest climate lever.",
        "methane":      "💨 Methane is 84x more potent than CO₂ over 20 years. Cutting methane is the fastest near-term climate win.",
        "net zero":     "🎯 Net Zero means balancing emissions produced with emissions removed. 140+ countries have net zero pledges.",
    }
    for kw, resp in topics.items():
        if kw in q:
            return f"🤖 Climate AI: {resp}{ctx}"
    return (
        f"🤖 Climate AI: Great question about '{question[:60]}'. "
        f"Type a keyword (solar, wind, carbon, methane, hydrogen, coal, etc.) for detailed climate insights.{ctx}"
    )
