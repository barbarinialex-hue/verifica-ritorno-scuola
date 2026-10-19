import re
import hashlib
import hmac
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter, oauth
from app.models import Quartiere, Segnalazione, Utente

bp = Blueprint("auth", __name__)
RESET_TOKEN_MAX_AGE = 1800


def reset_token_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")


def send_password_reset_email(user, reset_url):
    host = current_app.config["SMTP_HOST"]
    sender = current_app.config["MAIL_FROM"]
    if not host or not sender:
        current_app.logger.warning("SMTP non configurato: impossibile inviare un link di recupero password.")
        return

    message = EmailMessage()
    message["Subject"] = "Reimposta la password"
    message["From"] = sender
    message["To"] = user.email
    message.set_content(
        f"Ciao {user.nome},\n\n"
        f"Per scegliere una nuova password apri questo link entro 30 minuti:\n{reset_url}\n\n"
        "Se non hai richiesto il reset, ignora questa email."
    )
    port = current_app.config["SMTP_PORT"]
    if current_app.config["SMTP_USE_SSL"]:
        connection = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=15)
    else:
        connection = smtplib.SMTP(host, port, timeout=15)
    with connection:
        if current_app.config["SMTP_USE_TLS"] and not current_app.config["SMTP_USE_SSL"]:
            connection.starttls(context=ssl.create_default_context())
        username = current_app.config["SMTP_USERNAME"]
        if username:
            connection.login(username, current_app.config["SMTP_PASSWORD"])
        connection.send_message(message)


def password_reset_fingerprint(password_hash):
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, password_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def get_reset_user(token):
    try:
        payload = reset_token_serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
    except (BadSignature, TypeError):
        return None
    user = db.session.get(Utente, payload.get("user_id"))
    if not user or not hmac.compare_digest(
        payload.get("fingerprint", ""), password_reset_fingerprint(user.password_hash)
    ):
        return None
    return user


@bp.route("/registrazione", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cognome = request.form.get("cognome", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        quartiere_id = request.form.get("quartiere_id", type=int)
        quartiere = db.session.get(Quartiere, quartiere_id) if quartiere_id else None
        error = None
        if not nome or not cognome or len(nome) > 100 or len(cognome) > 100:
            error = "Inserisci nome e cognome validi."
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
            error = "Inserisci un indirizzo email valido."
        elif len(password) < 10:
            error = "La password deve contenere almeno 10 caratteri."
        elif not quartiere:
            error = "Seleziona un quartiere valido."
        elif db.session.query(Utente.id).filter(func.lower(Utente.email) == email).first():
            error = "Esiste già un account con questa email."

        if error:
            flash(error, "danger")
        else:
            user = Utente(nome=nome, cognome=cognome, email=email, fk_quartiere=quartiere.id, tipo_ruolo="Cittadino")
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Esiste già un account con questa email.", "danger")
            else:
                flash("Account creato. Ora puoi accedere.", "success")
                return redirect(url_for("auth.login"))

    return render_template("auth/register.html", quartieri=Quartiere.query.order_by(Quartiere.nome_quartiere).all())


@bp.route("/accesso", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = Utente.query.filter(func.lower(Utente.email) == email).first()
        if not user or not user.check_password(password):
            flash("Email o password non corretti.", "danger")
            return render_template("auth/login.html"), 401

        target = request.args.get("next", "")
        parsed_target = urlsplit(target)
        if not target.startswith("/") or target.startswith("//") or "\\" in target or parsed_target.netloc or parsed_target.scheme:
            target = url_for("reports.index")
        response = redirect(target)
        set_access_cookies(response, create_access_token(identity=str(user.id)))
        return response

    return render_template("auth/login.html")


@bp.get("/accesso/google")
def google_login():
    if not current_app.config["GOOGLE_OAUTH_ENABLED"]:
        flash("Accesso Google non configurato.", "warning")
        return redirect(url_for("auth.login"))
    callback_path = url_for("auth.google_callback")
    public_base_url = current_app.config["PUBLIC_BASE_URL"]
    callback_url = f"{public_base_url}{callback_path}" if public_base_url else url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(callback_url)


@bp.get("/accesso/google/callback")
def google_callback():
    if not current_app.config["GOOGLE_OAUTH_ENABLED"]:
        return redirect(url_for("auth.login"))
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.userinfo()
        email = str(userinfo.get("email", "")).strip().lower()
        if not userinfo.get("email_verified") or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Google non ha verificato un indirizzo email valido.", "danger")
            return redirect(url_for("auth.login"))
        user = Utente.query.filter(func.lower(Utente.email) == email).first()
        if not user:
            flash("Crea prima un account con questo indirizzo email, poi potrai accedere con Google.", "warning")
            return redirect(url_for("auth.register"))
        response = redirect(url_for("reports.index"))
        set_access_cookies(response, create_access_token(identity=str(user.id)))
        return response
    except Exception:
        current_app.logger.exception("Autenticazione Google non riuscita.")
        flash("Accesso Google non riuscito. Riprova.", "danger")
        return redirect(url_for("auth.login"))


@bp.route("/password-dimenticata", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) and len(email) <= 254:
            user = Utente.query.filter(func.lower(Utente.email) == email).first()
            if user:
                token = reset_token_serializer().dumps({
                    "user_id": user.id,
                    "fingerprint": password_reset_fingerprint(user.password_hash),
                })
                reset_path = url_for("auth.reset_password", token=token)
                public_base_url = current_app.config["PUBLIC_BASE_URL"]
                reset_url = f"{public_base_url}{reset_path}" if public_base_url else url_for("auth.reset_password", token=token, _external=True)
                try:
                    send_password_reset_email(user, reset_url)
                except (OSError, smtplib.SMTPException):
                    current_app.logger.exception("Invio email di recupero password non riuscito.")
        flash("Se l'indirizzo è associato a un account, riceverai un link per reimpostare la password.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("auth/forgot_password.html")


@bp.route("/password-ripristino/<token>", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def reset_password(token):
    user = get_reset_user(token)
    if not user:
        flash("Il link non è valido o è scaduto. Richiedine uno nuovo.", "warning")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirmation = request.form.get("conferma_password", "")
        if len(password) < 10:
            flash("La password deve contenere almeno 10 caratteri.", "danger")
        elif password != confirmation:
            flash("Le password non coincidono.", "danger")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Password aggiornata. Ora puoi accedere.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@bp.route("/esci", methods=["POST"])
@jwt_required()
def logout():
    response = redirect(url_for("reports.index"))
    unset_jwt_cookies(response)
    flash("Hai effettuato la disconnessione.", "info")
    return response


@bp.route("/profilo")
def profile():
    from app.security import current_user_from_token

    try:
        verify_jwt_in_request()
    except JWTExtendedException:
        return redirect(url_for("auth.login", next=url_for("auth.profile")))
    user = current_user_from_token()
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = Segnalazione.query.filter_by(fk_utente_autore=user.id).order_by(
        Segnalazione.data_creazione.desc()
    ).paginate(page=page, per_page=12, error_out=False)
    return render_template("auth/profile.html", user=user, pagination=pagination)
