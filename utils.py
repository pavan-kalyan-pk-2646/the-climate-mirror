"""
utils.py — Shared utilities: validation, rate limiting, climate core model.
"""
import logging
from time import time

logger = logging.getLogger(__name__)

# ── RATE LIMITING ──────────────────────────────────────────
_rate_store: dict = {}


def rate_limit(user: str, limit_seconds: int = 3) -> bool:
    """Returns True if the request is allowed; False if rate-limited."""
    now = time()
    if now - _rate_store.get(user, 0) < limit_seconds:
        return False
    _rate_store[user] = now
    return True


# ── INPUT VALIDATION ───────────────────────────────────────
ALLOWED_COUNTRIES = [
    "India", "USA", "China", "Germany",
    "Brazil", "Australia", "UK", "Japan", "Russia",
]


def safe_float(val, default: float = 0.0, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a form value to [lo, hi], returning default on error."""
    try:
        return max(lo, min(hi, float(val)))
    except (TypeError, ValueError):
        return default


def validate_username(username: str) -> str | None:
    """Return error string or None if valid."""
    username = username.strip()
    if len(username) < 3:
        return "Username must be at least 3 characters."
    if len(username) > 40:
        return "Username must be 40 characters or fewer."
    if not username.isalnum():
        return "Username may only contain letters and numbers."
    return None


def validate_password(password: str) -> str | None:
    """Return error string or None if valid."""
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    return None


def sanitise_country(country: str) -> str:
    """Return validated country or default to India."""
    return country if country in ALLOWED_COUNTRIES else "India"


# ── CLIMATE CORE MODEL ─────────────────────────────────────
def predict_climate(e: float, en: float, t: float, i: float) -> tuple:
    """
    Weighted prediction: energy(35%) > industry(30%) > emissions(25%) > transport(10%).
    Returns (temp_rise, impact_label, color, raw_score).
    """
    score = (e * 0.25) + (en * 0.35) + (t * 0.10) + (i * 0.30)
    temp  = round(0.5 + (score / 100) * 4.5, 2)
    if   temp < 1.5: return temp, "Safe Zone 🌱",        "green",  score
    elif temp < 2.0: return temp, "Low Impact 🌿",        "teal",   score
    elif temp < 2.8: return temp, "Medium Impact ⚠️",     "yellow", score
    elif temp < 3.5: return temp, "High Impact 🔥",       "orange", score
    else:            return temp, "Critical Emergency 🚨", "red",    score


def eco_score(e: float, en: float, t: float, i: float) -> int:
    """Sustainability score 0–100 (higher = greener)."""
    raw = 100 - ((e * 0.25) + (en * 0.35) + (t * 0.10) + (i * 0.30))
    return max(0, min(100, int(raw)))


# ── COLOUR HELPERS ─────────────────────────────────────────
def score_colour(score: int) -> str:
    """Map eco score to a Tailwind-friendly colour name."""
    if score >= 75: return "green"
    if score >= 50: return "yellow"
    if score >= 25: return "orange"
    return "red"


def risk_colour(pct: int) -> str:
    if pct < 30:   return "green"
    if pct < 55:   return "yellow"
    if pct < 75:   return "orange"
    return "red"
