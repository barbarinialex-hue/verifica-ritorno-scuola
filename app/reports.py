from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import warnings

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager, selectinload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import AllegatoMultimediale, Categoria, Dossier, DossierSegnalazione, Quartiere, Segnalazione, Sostegno, Utente
from app.security import can_manage_report, current_user_from_token, roles_required

bp = Blueprint("reports", __name__)

STATES = ["Inviata", "Approvata", "Presa in Carico", "Inclusa nel Dossier", "Risolta"]
MAX_TEXT_LENGTH = 5000
ALLOWED = {
    ".jpg": ("Foto", "image"),
    ".jpeg": ("Foto", "image"),
    ".png": ("Foto", "image"),
    ".webp": ("Foto", "image"),
    ".mp4": ("Video", "mp4"),
    ".mov": ("Video", "mov"),
    ".webm": ("Video", lambda data: len(data) >= 4 and data[:4] == bytes.fromhex("1A45DFA3")),
}


def valid_upload(extension, data):
    rule = ALLOWED.get(extension)
    if not rule:
        return False
    if rule[1] == "image":
        expected_format = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[extension]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as image:
                    if image.format != expected_format:
                        return False
                    image.verify()
            return True
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            return False
    if rule[1] == "mp4":
        return len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V ", b"MSNV"}
    if rule[1] == "mov":
        return len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] == b"qt  "
    return rule[1](data)


def get_report_form_data():
    title = request.form.get("titolo", "").strip()
    description = request.form.get("descrizione_testuale", "").strip()
    address = request.form.get("indirizzo", "").strip()
    category_id = request.form.get("categoria_id", type=int)
    neighborhood_id = request.form.get("quartiere_id", type=int)
    try:
        latitude = Decimal(request.form.get("latitudine", ""))
        longitude = Decimal(request.form.get("longitudine", ""))
    except (InvalidOperation, TypeError):
        raise ValueError("Inserisci coordinate numeriche valide.")

    if not title or len(title) > 180 or not description or not address or len(address) > 255:
        raise ValueError("Compila titolo, descrizione e indirizzo rispettando le lunghezze indicate.")
    if len(description) > MAX_TEXT_LENGTH:
        raise ValueError(f"La descrizione non può superare {MAX_TEXT_LENGTH} caratteri.")
    if not latitude.is_finite() or not longitude.is_finite():
        raise ValueError("Inserisci coordinate numeriche valide.")
    if latitude.as_tuple().exponent < -6 or longitude.as_tuple().exponent < -6:
        raise ValueError("Le coordinate possono contenere al massimo sei cifre decimali.")
    if not Decimal("-90") <= latitude <= Decimal("90") or not Decimal("-180") <= longitude <= Decimal("180"):
        raise ValueError("Le coordinate devono essere comprese negli intervalli geografici validi.")
    if not db.session.get(Categoria, category_id) or not db.session.get(Quartiere, neighborhood_id):
        raise ValueError("Seleziona una categoria e un quartiere validi.")
    return title, description, address, latitude, longitude, category_id, neighborhood_id


def get_required_report_image():
    uploaded = request.files.get("immagine")
    if not uploaded or not uploaded.filename:
        raise ValueError("Carica almeno una foto valida per inviare la segnalazione.")

    extension = Path(secure_filename(uploaded.filename)).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("La foto deve essere in formato JPG, PNG o WebP.")
    data = uploaded.stream.read(current_app.config["MAX_CONTENT_LENGTH"] + 1)
    if len(data) > current_app.config["MAX_CONTENT_LENGTH"] or not valid_upload(extension, data):
        raise ValueError("Il file immagine non è valido o supera la dimensione massima consentita.")
    return extension, data


def report_query():
    query = Segnalazione.query.join(Categoria).join(Quartiere).options(
        contains_eager(Segnalazione.categoria),
        contains_eager(Segnalazione.quartiere),
        selectinload(Segnalazione.allegati),
    )
    if request.args.get("quartiere", type=int):
        query = query.filter(Segnalazione.fk_quartiere == request.args.get("quartiere", type=int))
    if request.args.get("categoria", type=int):
        query = query.filter(Segnalazione.fk_categoria == request.args.get("categoria", type=int))
    if request.args.get("stato") in STATES:
        query = query.filter(Segnalazione.stato_attuale == request.args["stato"])
    search = request.args.get("q", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            Segnalazione.titolo.ilike(pattern),
            Segnalazione.indirizzo.ilike(pattern),
            Segnalazione.descrizione_testuale.ilike(pattern),
        ))
    return query.order_by(Segnalazione.data_creazione.desc(), Segnalazione.id.desc())


@bp.route("/")
def index():
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = report_query().paginate(page=page, per_page=12, error_out=False)
    map_points = [{
        "id": report.id,
        "latitude": float(report.latitudine),
        "longitude": float(report.longitudine),
        "title": report.titolo,
        "address": report.indirizzo,
        "category": report.categoria.nome_categoria,
        "status": report.stato_attuale,
        "image_url": next((item.url_file for item in report.allegati if item.tipo_file == "Foto"), None),
        "url": url_for("reports.detail", report_id=report.id),
    } for report in report_query().all()]
    return render_template("reports/index.html", pagination=pagination, map_points=map_points, categorie=Categoria.query.order_by(Categoria.nome_categoria).all(), quartieri=Quartiere.query.order_by(Quartiere.nome_quartiere).all(), stati=STATES)


@bp.route("/segnalazioni/<int:report_id>")
def detail(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    try:
        verify_jwt_in_request(optional=True)
        user = current_user_from_token()
    except JWTExtendedException:
        user = None
    has_supported = bool(user and Sostegno.query.filter_by(fk_utente=user.id, fk_segnalazione=report.id).first())
    support_count = db.session.query(func.count(Sostegno.id)).filter(
        Sostegno.fk_segnalazione == report.id
    ).scalar()
    return render_template("reports/detail.html", report=report, has_supported=has_supported, support_count=support_count)


@bp.route("/segnalazioni/nuova", methods=["GET", "POST"])
@roles_required("Cittadino", "MembroComitato", "Admin")
def create():
    user = current_user_from_token()
    if request.method == "POST":
        try:
            values = get_report_form_data()
            image_extension, image_data = get_required_report_image()
        except ValueError as error:
            flash(str(error), "danger")
        else:
            report = Segnalazione(titolo=values[0], descrizione_testuale=values[1], indirizzo=values[2], latitudine=values[3], longitudine=values[4], fk_categoria=values[5], fk_quartiere=values[6], fk_utente_autore=user.id)
            filename = f"{uuid4().hex}{image_extension}"
            destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
            try:
                destination.write_bytes(image_data)
                db.session.add(report)
                db.session.flush()
                db.session.add(AllegatoMultimediale(
                    url_file=f"/uploads/{filename}",
                    tipo_file="Foto",
                    fk_segnalazione=report.id,
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()
                try:
                    destination.unlink(missing_ok=True)
                except OSError:
                    current_app.logger.exception("Impossibile rimuovere la foto dopo il fallimento della creazione.")
                raise
            flash("Segnalazione inviata.", "success")
            return redirect(url_for("reports.detail", report_id=report.id))
    return render_report_form()


def render_report_form(report=None):
    return render_template("reports/form.html", report=report, categorie=Categoria.query.order_by(Categoria.nome_categoria).all(), quartieri=Quartiere.query.order_by(Quartiere.nome_quartiere).all())


@bp.route("/segnalazioni/<int:report_id>/modifica", methods=["GET", "POST"])
@roles_required("Cittadino", "MembroComitato", "Admin")
def edit(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    user = current_user_from_token()
    if not can_manage_report(user, report):
        abort(403)
    if request.method == "POST":
        try:
            values = get_report_form_data()
        except ValueError as error:
            flash(str(error), "danger")
        else:
            report.titolo, report.descrizione_testuale, report.indirizzo = values[0], values[1], values[2]
            report.latitudine, report.longitudine = values[3], values[4]
            report.fk_categoria, report.fk_quartiere = values[5], values[6]
            db.session.commit()
            flash("Segnalazione aggiornata.", "success")
            return redirect(url_for("reports.detail", report_id=report.id))
    return render_report_form(report)


@bp.route("/segnalazioni/<int:report_id>/elimina", methods=["POST"])
@roles_required("Cittadino", "MembroComitato", "Admin")
def delete(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    if not can_manage_report(current_user_from_token(), report):
        abort(403)
    file_paths = [Path(current_app.config["UPLOAD_FOLDER"]) / Path(item.url_file).name for item in report.allegati]
    db.session.delete(report)
    db.session.commit()
    for path in file_paths:
        path.unlink(missing_ok=True)
    flash("Segnalazione eliminata.", "success")
    return redirect(url_for("reports.index"))


@bp.route("/segnalazioni/<int:report_id>/allegati", methods=["POST"])
@roles_required("Cittadino", "MembroComitato", "Admin")
def upload(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    if not can_manage_report(current_user_from_token(), report):
        abort(403)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Seleziona un file da caricare.", "danger")
        return redirect(url_for("reports.detail", report_id=report.id))
    extension = Path(secure_filename(uploaded.filename)).suffix.lower()
    rule = ALLOWED.get(extension)
    data = uploaded.stream.read(current_app.config["MAX_CONTENT_LENGTH"] + 1)
    if not rule or len(data) > current_app.config["MAX_CONTENT_LENGTH"] or not valid_upload(extension, data):
        flash("Formato non supportato o file non valido.", "danger")
        return redirect(url_for("reports.detail", report_id=report.id))
    filename = f"{uuid4().hex}{extension}"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    try:
        destination.write_bytes(data)
        db.session.add(AllegatoMultimediale(url_file=f"/uploads/{filename}", tipo_file=rule[0], fk_segnalazione=report.id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            current_app.logger.exception("Impossibile rimuovere il file dopo il fallimento dell'upload.")
        raise
    flash("Allegato caricato.", "success")
    return redirect(url_for("reports.detail", report_id=report.id))


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False, conditional=True)


@bp.route("/segnalazioni/<int:report_id>/sostegno", methods=["POST"])
@roles_required("Cittadino", "MembroComitato", "Admin")
def support(report_id):
    db.get_or_404(Segnalazione, report_id)
    user = current_user_from_token()
    existing = Sostegno.query.filter_by(fk_utente=user.id, fk_segnalazione=report_id).first()
    if existing:
        db.session.delete(existing)
        flash("Sostegno rimosso.", "info")
    else:
        db.session.add(Sostegno(fk_utente=user.id, fk_segnalazione=report_id))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Hai già sostenuto questa segnalazione.", "info")
        else:
            flash("Sostegno registrato.", "success")
        return redirect(url_for("reports.detail", report_id=report_id))
    db.session.commit()
    return redirect(url_for("reports.detail", report_id=report_id))


@bp.route("/comitato/segnalazioni")
@roles_required("MembroComitato", "Admin")
def moderation():
    reports = Segnalazione.query.order_by(Segnalazione.data_creazione.desc()).limit(100).all()
    return render_template("reports/moderation.html", reports=reports, stati=STATES)


@bp.route("/comitato/segnalazioni/<int:report_id>/stato", methods=["POST"])
@roles_required("MembroComitato", "Admin")
def update_status(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    new_state = request.form.get("stato")
    if new_state not in STATES:
        flash("Stato non valido.", "danger")
    else:
        report.stato_attuale = new_state
        db.session.commit()
        flash("Stato aggiornato.", "success")
    return redirect(url_for("reports.moderation"))


@bp.route("/comitato/segnalazioni/<int:report_id>/duplicato", methods=["POST"])
@roles_required("MembroComitato", "Admin")
def set_duplicate(report_id):
    report = db.get_or_404(Segnalazione, report_id)
    parent_id = request.form.get("padre_id", type=int)
    parent = db.session.get(Segnalazione, parent_id) if parent_id else None
    if not parent or parent.id == report.id:
        flash("Seleziona una segnalazione principale valida.", "danger")
        return redirect(url_for("reports.moderation"))
    ancestor = parent
    visited = set()
    while ancestor:
        if ancestor.id in visited or ancestor.id == report.id:
            flash("Il collegamento creerebbe un ciclo tra duplicati.", "danger")
            return redirect(url_for("reports.moderation"))
        visited.add(ancestor.id)
        ancestor = db.session.get(Segnalazione, ancestor.fk_segnalazione_padre) if ancestor.fk_segnalazione_padre else None
    report.fk_segnalazione_padre = parent.id
    db.session.commit()
    flash("Segnalazione collegata come duplicato.", "success")
    return redirect(url_for("reports.moderation"))


@bp.route("/dossier", methods=["GET", "POST"])
@roles_required("MembroComitato", "Admin")
def dossiers():
    user = current_user_from_token()
    if request.method == "POST":
        title = request.form.get("titolo", "").strip()
        notes = request.form.get("note_comitato", "").strip() or None
        if not title or len(title) > 180 or (notes and len(notes) > MAX_TEXT_LENGTH):
            flash(f"Inserisci un titolo valido e limita le note a {MAX_TEXT_LENGTH} caratteri.", "danger")
        else:
            dossier = Dossier(titolo=title, note_comitato=notes, fk_utente_creatore=user.id)
            db.session.add(dossier)
            db.session.commit()
            flash("Dossier creato.", "success")
            return redirect(url_for("reports.dossier_detail", dossier_id=dossier.id))
    page = max(request.args.get("page", 1, type=int), 1)
    dossier_counts = db.session.query(
        DossierSegnalazione.fk_dossier.label("dossier_id"),
        func.count(DossierSegnalazione.fk_segnalazione).label("report_count"),
    ).group_by(DossierSegnalazione.fk_dossier).subquery()
    dossier_query = db.session.query(
        Dossier,
        func.coalesce(dossier_counts.c.report_count, 0).label("report_count"),
    ).outerjoin(dossier_counts, dossier_counts.c.dossier_id == Dossier.id).order_by(
        Dossier.data_creazione.desc(), Dossier.id.desc()
    )
    pagination = dossier_query.paginate(page=page, per_page=12, error_out=False)
    return render_template("reports/dossiers.html", pagination=pagination)


@bp.route("/dossier/<int:dossier_id>", methods=["GET", "POST"])
@roles_required("MembroComitato", "Admin")
def dossier_detail(dossier_id):
    dossier = db.get_or_404(Dossier, dossier_id)
    if request.method == "POST":
        report_id = request.form.get("segnalazione_id", type=int)
        report = db.session.get(Segnalazione, report_id) if report_id else None
        if not report:
            flash("Seleziona una segnalazione valida.", "danger")
        else:
            db.session.add(DossierSegnalazione(fk_dossier=dossier.id, fk_segnalazione=report.id))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("La segnalazione è già presente nel dossier.", "info")
            else:
                flash("Segnalazione aggiunta al dossier.", "success")
        return redirect(url_for("reports.dossier_detail", dossier_id=dossier.id))
    reports = Segnalazione.query.order_by(Segnalazione.data_creazione.desc()).limit(200).all()
    return render_template("reports/dossier_detail.html", dossier=dossier, reports=reports)


@bp.route("/dossier/<int:dossier_id>/rimuovi/<int:report_id>", methods=["POST"])
@roles_required("MembroComitato", "Admin")
def remove_from_dossier(dossier_id, report_id):
    item = db.session.get(DossierSegnalazione, (dossier_id, report_id))
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Segnalazione rimossa dal dossier.", "success")
    return redirect(url_for("reports.dossier_detail", dossier_id=dossier_id))
