from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Utente
from app.security import roles_required

bp = Blueprint("admin", __name__)
ROLES = ["Cittadino", "MembroComitato", "Admin"]


@bp.route("/amministrazione/utenti")
@roles_required("Admin")
def users():
    users = Utente.query.order_by(Utente.cognome, Utente.nome).all()
    return render_template("admin/users.html", users=users, roles=ROLES)


@bp.route("/amministrazione/utenti/<int:user_id>/ruolo", methods=["POST"])
@roles_required("Admin")
def update_role(user_id):
    user = db.get_or_404(Utente, user_id)
    role = request.form.get("tipo_ruolo")
    if role not in ROLES:
        flash("Ruolo non valido.", "danger")
    elif user.tipo_ruolo == "Admin" and role != "Admin" and Utente.query.filter_by(tipo_ruolo="Admin").count() <= 1:
        flash("Non puoi rimuovere l'ultimo amministratore del sistema.", "danger")
    else:
        user.tipo_ruolo = role
        db.session.commit()
        flash("Ruolo aggiornato.", "success")
    return redirect(url_for("admin.users"))
