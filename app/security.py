from functools import wraps

from flask import abort, redirect, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Utente


def current_user_from_token():
    identity = get_jwt_identity()
    return db.session.get(Utente, int(identity)) if identity else None


def roles_required(*roles):
    def decorator(view):
        @jwt_required()
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user_from_token()
            if user is None:
                return redirect(url_for("auth.login", next=request.path))
            if user.tipo_ruolo not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def can_manage_report(user, report):
    return user and (report.fk_utente_autore == user.id or user.tipo_ruolo in {"MembroComitato", "Admin"})
