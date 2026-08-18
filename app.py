"""
app.py — The Climate Mirror v2

Flask application factory.
All routes in routes.py, models in models.py,
agents in agents/, utilities in utils.py.
"""

import os
import logging

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from models import db
from routes import bp


# ─────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# EXTENSIONS
# ─────────────────────────────────────────────────────────

csrf = CSRFProtect()


# ─────────────────────────────────────────────────────────
# APPLICATION FACTORY
# ─────────────────────────────────────────────────────────

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # ── SECURITY ─────────────────────────────────────────
    # 
    # IMPORTANT: On Vercel, each function invocation gets a fresh Python
    # process. If SECRET_KEY changes between requests, CSRF tokens will fail.
    # Use a consistent SECRET_KEY from env, or generate it once per deploy.
    #

    app.secret_key = os.environ.get(
        "SECRET_KEY",
        "climate-mirror-dev-key-2024"  # ⚠️ CHANGE THIS for production!
    )

    # ── DATABASE ─────────────────────────────────────────
    #
    # If DATABASE_URL is configured in Vercel,
    # that database will be used.
    #
    # Otherwise:
    #   Vercel  → /tmp/climate.db
    #   Local   → project/climate.db
    #

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        if os.environ.get("VERCEL"):
            database_url = "sqlite:////tmp/climate.db"
        else:
            database_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "climate.db",
            )

            database_url = f"sqlite:///{database_path}"

    # ── APPLICATION CONFIGURATION ────────────────────────

    app.config.update(
        # Security
        SESSION_COOKIE_HTTPONLY=True,

        SESSION_COOKIE_SECURE=(
            os.environ.get("FLASK_ENV") == "production"
            or bool(os.environ.get("VERCEL"))
        ),

        SESSION_COOKIE_SAMESITE="Lax",

        PERMANENT_SESSION_LIFETIME=28_800,  # 8 hours

        # SQLAlchemy
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        # File uploads
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,  # 1 MB

        # CSRF
        WTF_CSRF_TIME_LIMIT=3600,
    )

    # Allow custom configuration
    if config:
        app.config.update(config)

    # ── EXTENSIONS ────────────────────────────────────────

    db.init_app(app)
    csrf.init_app(app)

    # ── BLUEPRINTS ────────────────────────────────────────

    app.register_blueprint(bp)

    # ── DATABASE INITIALIZATION ──────────────────────────

    with app.app_context():
        try:
            db.create_all()

            logger.info(
                "Database tables verified / created."
            )

        except Exception:
            logger.exception(
                "Database initialization failed."
            )
            raise

    return app


# ─────────────────────────────────────────────────────────
# VERCEL / WSGI ENTRY POINT
# ─────────────────────────────────────────────────────────
#
# Vercel requires a top-level Flask instance named "app".
#

app = create_app()


# ─────────────────────────────────────────────────────────
# LOCAL DEVELOPMENT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )