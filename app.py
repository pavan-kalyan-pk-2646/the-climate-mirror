"""
app.py — The Climate Mirror v2
Flask application factory. All routes in routes.py, models in models.py,
agents in agents/, utilities in utils.py.
"""
import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from models import db
from routes import bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

csrf = CSRFProtect()


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # ── CONFIGURATION ─────────────────────────────────────
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

    app.config.update(
        # Security
        SESSION_COOKIE_HTTPONLY  = True,
        SESSION_COOKIE_SECURE    = os.environ.get("FLASK_ENV") == "production",
        SESSION_COOKIE_SAMESITE  = "Lax",
        PERMANENT_SESSION_LIFETIME = 28_800,          # 8 hours in seconds

        # SQLAlchemy
        SQLALCHEMY_DATABASE_URI  = os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(os.path.dirname(__file__), 'climate.db')}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS = False,

        # File uploads
        MAX_CONTENT_LENGTH = 1 * 1024 * 1024,         # 1 MB max request

        # CSRF
        WTF_CSRF_TIME_LIMIT = 3600,
    )

    if config:
        app.config.update(config)

    # ── EXTENSIONS ────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    # ── BLUEPRINTS ────────────────────────────────────────
    app.register_blueprint(bp)

    # ── DB INIT ───────────────────────────────────────────
    with app.app_context():
        db.create_all()
        logger.info("Database tables verified / created.")

    return app


# ── ENTRY POINT ───────────────────────────────────────────
if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
