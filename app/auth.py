import re
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies, unset_jwt_cookies
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Quartiere, Utente

bp = Blueprint("auth", __name__)


@bp.route("/registrazione", methods=["GET", "POST"])
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


@bp.route("/esci", methods=["POST"])
@jwt_required()
def logout():
    response = redirect(url_for("reports.index"))
    unset_jwt_cookies(response)
    flash("Hai effettuato la disconnessione.", "info")
    return response


@bp.route("/profilo")
def profile():
    from flask_jwt_extended import verify_jwt_in_request
    from app.security import current_user_from_token

    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for("auth.login", next=url_for("auth.profile")))
    user = current_user_from_token()
    return render_template("auth/profile.html", user=user)
