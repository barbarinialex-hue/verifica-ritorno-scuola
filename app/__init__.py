import os
import secrets
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import sqlite3

from app.extensions import csrf, db, jwt, migrate
from app import models  # noqa: F401


@event.listens_for(Engine, "connect")
def set_sqlite_foreign_keys(connection, _record):
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    elif connection.__class__.__module__.startswith("pymysql"):
        cursor = connection.cursor()
        cursor.execute("SET time_zone = '+00:00'")
        cursor.close()


def normalize_database_url(raw_url):
    if not raw_url:
        return raw_url, {}

    parsed = urlparse(raw_url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        return raw_url, {}

    filtered_params = []
    ssl_required = False
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = key.lower()
        if normalized_key in {"ssl", "ssl-mode"}:
            if value.lower() in {"true", "required", "1"}:
                ssl_required = True
            continue
        filtered_params.append((key, value))

    cleaned_query = urlencode(filtered_params, doseq=True)
    cleaned_url = urlunparse(parsed._replace(query=cleaned_query))
    connect_args = {"ssl": {}} if ssl_required else {}
    return cleaned_url, connect_args


def create_app(test_config=None):
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    candidate_database_url = (test_config or {}).get("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL", "sqlite:///verifica_ritorno_scuola.db")
    database_url, db_connect_args = normalize_database_url(candidate_database_url)

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": db_connect_args} if db_connect_args else {},
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32),
        JWT_TOKEN_LOCATION=["cookies"],
        JWT_ACCESS_COOKIE_NAME="access_token_cookie",
        JWT_COOKIE_CSRF_PROTECT=False,
        JWT_COOKIE_SECURE=os.getenv("JWT_COOKIE_SECURE", "0").lower() in {"1", "true", "yes"},
        JWT_COOKIE_SAMESITE="Lax",
        JWT_ACCESS_TOKEN_EXPIRES=60 * 60 * 8,
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024))),
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "instance/uploads"),
    )
    if test_config:
        app.config.update(test_config)
        if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    if not upload_folder.is_absolute():
        upload_folder = Path(app.root_path).parent / upload_folder
    upload_folder.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_folder.resolve())

    db.init_app(app)
    migrate.init_app(app, db, compare_server_default=True)
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            app.logger.exception("Impossibile creare automaticamente le tabelle mancanti del database.")
    jwt.init_app(app)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    from app.reports import bp as reports_bp
    from app.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return redirect(url_for("auth.login", next=request.path))

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return redirect(url_for("auth.login", next=request.path))

    @app.context_processor
    def inject_template_context():
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        from app.models import Utente

        user = db.session.get(Utente, int(identity)) if identity else None
        return {"current_user": user}

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", message="Il file supera la dimensione massima consentita."), 413

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="La pagina richiesta non esiste."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("error.html", message="Si è verificato un errore. Riprova più tardi."), 500

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db.session.rollback()
            return jsonify(status="degraded", database="unavailable"), 503
        return jsonify(status="ok", database="connected")

    from app.commands import register_commands

    register_commands(app)

    return app
