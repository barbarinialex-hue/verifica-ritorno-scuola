from io import BytesIO
import re
from decimal import Decimal
from pathlib import Path

from PIL import Image
import pytest

from app import create_app
from app.extensions import db
from app.models import AllegatoMultimediale, Dossier, DossierSegnalazione, Quartiere, Segnalazione, Sostegno, Utente


def csrf_token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match, f"CSRF field not found on {path}"
    return match.group(1).decode()


def register(client, email):
    token = csrf_token(client, "/registrazione")
    return client.post("/registrazione", data={
        "csrf_token": token,
        "nome": "Ada",
        "cognome": "Luna",
        "email": email,
        "password": "password-sicura-123",
        "quartiere_id": "1",
    }, follow_redirects=False)


def login(client, email):
    token = csrf_token(client, "/accesso")
    return client.post("/accesso", data={
        "csrf_token": token,
        "email": email,
        "password": "password-sicura-123",
    }, follow_redirects=False)


def create_report(client, title="Marciapiede danneggiato", description="Il marciapiede è danneggiato e difficile da percorrere.", include_image=True):
    token = csrf_token(client, "/segnalazioni/nuova")
    data = {
        "csrf_token": token,
        "titolo": title,
        "descrizione_testuale": description,
        "latitudine": "45.123456",
        "longitudine": "9.123456",
        "indirizzo": "Via Roma 10",
        "categoria_id": "1",
        "quartiere_id": "1",
    }
    if include_image:
        image = BytesIO()
        Image.new("RGB", (2, 2), color="green").save(image, format="PNG")
        image.seek(0)
        data["immagine"] = (image, "segnalazione.png", "image/png")
    return client.post("/segnalazioni/nuova", data=data, follow_redirects=False)


def test_public_pages_and_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert client.get("/registrazione").status_code == 200
    assert client.get("/accesso").status_code == 200
    assert client.get("/health").json == {"status": "ok", "database": "connected"}


def test_report_map_contains_coordinates_and_filtered_markers(client):
    register(client, "map@example.test")
    login(client, "map@example.test")
    assert create_report(client).status_code == 302

    response = client.get("/")
    assert response.status_code == 200
    assert b"data-report-map" in response.data
    assert b"45.123456" in response.data
    assert b"9.123456" in response.data
    assert b"OpenStreetMap" in response.data
    assert b'class="report-thumb"' in response.data
    assert b'"image_url": "/uploads/' in response.data
    assert b'data-mobile-view="map"' in response.data
    assert b'data-mobile-view="list"' in response.data
    assert b'data-map-target=' in response.data
    with client.application.app_context():
        report_id = Segnalazione.query.one().id
    detail = client.get(f"/segnalazioni/{report_id}")
    assert detail.status_code == 200
    assert b"data-report-map" in detail.data
    assert b"45.123456" in detail.data
    assert b"imageViewerModal" in detail.data
    assert b"data-lightbox-group" in detail.data


def test_report_search_filters_list_and_map(client):
    register(client, "search@example.test")
    login(client, "search@example.test")
    assert create_report(client, title="Marciapiede dissestato").status_code == 302
    assert create_report(client, title="Illuminazione guasta").status_code == 302

    response = client.get("/?q=Illuminazione")
    assert response.status_code == 200
    assert b"Illuminazione guasta" in response.data
    assert b"Marciapiede dissestato" not in response.data
    assert b'"id": 2' in response.data
    assert b"Ricerca: Illuminazione" in response.data


def test_report_form_contains_map_picker_and_photo_preview(client):
    register(client, "map-picker@example.test")
    login(client, "map-picker@example.test")
    response = client.get("/segnalazioni/nuova")
    assert response.status_code == 200
    assert b"data-location-map" in response.data
    assert b"data-geocode" in response.data
    assert b"data-geolocate" in response.data
    assert b"data-image-preview" in response.data


def test_report_creation_requires_a_valid_image(client):
    register(client, "missing-image@example.test")
    login(client, "missing-image@example.test")

    response = create_report(client, include_image=False)
    assert response.status_code == 200
    assert b"Carica almeno una foto valida" in response.data
    with client.application.app_context():
        assert Segnalazione.query.count() == 0


def test_report_creation_rejects_fake_image(client):
    register(client, "fake-image@example.test")
    login(client, "fake-image@example.test")
    token = csrf_token(client, "/segnalazioni/nuova")
    response = client.post("/segnalazioni/nuova", data={
        "csrf_token": token,
        "titolo": "Foto finta",
        "descrizione_testuale": "Descrizione valida",
        "latitudine": "45.123456",
        "longitudine": "9.123456",
        "indirizzo": "Via Roma 10",
        "categoria_id": "1",
        "quartiere_id": "1",
        "immagine": (BytesIO(b"not an image"), "foto.png", "image/png"),
    }, follow_redirects=False)
    assert response.status_code == 200
    assert b"Il file immagine non" in response.data
    with client.application.app_context():
        assert Segnalazione.query.count() == 0


def test_password_reset_is_generic_temporary_and_invalidated_after_use(client, app, monkeypatch):
    register(client, "reset@example.test")
    sent_messages = []
    monkeypatch.setattr("app.auth.send_password_reset_email", lambda user, reset_url: sent_messages.append(reset_url))

    token = csrf_token(client, "/password-dimenticata")
    known_post = client.post(
        "/password-dimenticata",
        data={"csrf_token": token, "email": "reset@example.test"},
    )
    assert known_post.status_code == 302
    with client.session_transaction() as session:
        assert session.get("_flashes")
    known_response = client.get(known_post.location)
    assert b"Se l&#39;indirizzo" in known_response.data
    assert len(sent_messages) == 1

    token = csrf_token(client, "/password-dimenticata")
    unknown_post = client.post(
        "/password-dimenticata",
        data={"csrf_token": token, "email": "missing@example.test"},
    )
    unknown_response = client.get(unknown_post.location)
    assert b"Se l&#39;indirizzo" in unknown_response.data
    assert len(sent_messages) == 1

    reset_path = "/" + sent_messages[0].split("/", 3)[3]
    assert client.get(reset_path).status_code == 200
    token = csrf_token(client, reset_path)
    response = client.post(reset_path, data={
        "csrf_token": token,
        "password": "nuova-password-123",
        "conferma_password": "nuova-password-123",
    })
    assert response.status_code == 302
    with app.app_context():
        assert Utente.query.filter_by(email="reset@example.test").one().check_password("nuova-password-123")
    assert client.get(reset_path).status_code == 302


def test_google_login_redirects_when_oauth_is_not_configured(client):
    response = client.get("/accesso/google", follow_redirects=True)
    assert response.status_code == 200
    assert b"Accesso Google non configurato" in response.data


def test_app_startup_does_not_create_tables(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'uninitialized.db'}",
    })
    with app.app_context():
        assert db.inspect(db.engine).get_table_names() == []


def test_production_requires_stable_secrets_and_secure_cookies(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.setenv("JWT_SECRET_KEY", "")
    monkeypatch.setenv("JWT_COOKIE_SECURE", "0")
    config = {
        "APP_ENV": "production",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'production.db'}",
        "UPLOAD_FOLDER": str(tmp_path / "production-uploads"),
    }
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(config)

    config.update(SECRET_KEY="stable-secret", JWT_SECRET_KEY="stable-jwt-secret")
    with pytest.raises(RuntimeError, match="JWT_COOKIE_SECURE"):
        create_app(config)

    config["JWT_COOKIE_SECURE"] = True
    config["RATELIMIT_STORAGE_URI"] = "redis://localhost:6379/0"
    app = create_app(config)
    assert app.config["APP_ENV"] == "production"
    assert app.config["JWT_COOKIE_SECURE"] is True


def test_registration_login_and_profile(client):
    assert register(client, "ada@example.test").status_code == 302
    assert login(client, "ada@example.test").status_code == 302
    response = client.get("/profilo")
    assert response.status_code == 200
    assert b"ada@example.test" in response.data
    with client.application.app_context():
        user = Utente.query.filter_by(email="ada@example.test").one()
        assert user.tipo_ruolo == "Cittadino"
        assert user.password_hash != "password-sicura-123"
        assert user.check_password("password-sicura-123")


def test_login_rate_limit_returns_too_many_requests(client):
    token = csrf_token(client, "/accesso")
    responses = [
        client.post("/accesso", data={
            "csrf_token": token,
            "email": "missing@example.test",
            "password": "wrong-password",
        })
        for _ in range(6)
    ]
    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429


def test_registration_rejects_duplicate_email(client):
    assert register(client, "ada@example.test").status_code == 302
    response = register(client, "ada@example.test")
    assert response.status_code == 200
    assert "Esiste già un account".encode() in response.data
    with client.application.app_context():
        assert Utente.query.filter_by(email="ada@example.test").count() == 1


def test_report_creation_and_owner_authorization(app):
    owner = app.test_client()
    register(owner, "owner@example.test")
    login(owner, "owner@example.test")
    response = create_report(owner)
    assert response.status_code == 302
    with app.app_context():
        report = Segnalazione.query.one()
        report_id = report.id
        assert report.stato_attuale == "Inviata"
        assert report.latitudine == Decimal("45.123456")
        attachment = AllegatoMultimediale.query.filter_by(fk_segnalazione=report_id).one()
        assert attachment.tipo_file == "Foto"
        assert (Path(app.config["UPLOAD_FOLDER"]) / Path(attachment.url_file).name).is_file()

    other = app.test_client()
    register(other, "other@example.test")
    login(other, "other@example.test")
    token = csrf_token(other, "/accesso")
    denied = other.post(f"/segnalazioni/{report_id}/modifica", data={"csrf_token": token})
    assert denied.status_code == 403, denied.data[:500]


@pytest.mark.parametrize("latitude", ["NaN", "Infinity"])
def test_report_rejects_non_finite_coordinates(client, latitude):
    register(client, "coordinates@example.test")
    login(client, "coordinates@example.test")
    token = csrf_token(client, "/segnalazioni/nuova")
    response = client.post("/segnalazioni/nuova", data={
        "csrf_token": token,
        "titolo": "Coordinate non valide",
        "descrizione_testuale": "Descrizione valida",
        "latitudine": latitude,
        "longitudine": "9.123456",
        "indirizzo": "Via Roma 10",
        "categoria_id": "1",
        "quartiere_id": "1",
    })
    assert response.status_code == 200
    assert "coordinate numeriche valide".encode() in response.data
    with client.application.app_context():
        assert Segnalazione.query.count() == 0


def test_report_rejects_overlong_description(client):
    register(client, "long-description@example.test")
    login(client, "long-description@example.test")
    response = create_report(client, description="x" * 5001)
    assert response.status_code == 200
    assert b"5000 caratteri" in response.data
    with client.application.app_context():
        assert Segnalazione.query.count() == 0


def test_support_toggles_without_duplicate_rows(app):
    client = app.test_client()
    register(client, "supporter@example.test")
    login(client, "supporter@example.test")
    create_report(client)
    with app.app_context():
        report_id = Segnalazione.query.one().id
    token = csrf_token(client, f"/segnalazioni/{report_id}")
    assert client.post(f"/segnalazioni/{report_id}/sostegno", data={"csrf_token": token}).status_code == 302
    with app.app_context():
        assert Sostegno.query.count() == 1
    token = csrf_token(client, f"/segnalazioni/{report_id}")
    assert client.post(f"/segnalazioni/{report_id}/sostegno", data={"csrf_token": token}).status_code == 302
    with app.app_context():
        assert Sostegno.query.count() == 0


def test_upload_rejects_invalid_content(app):
    client = app.test_client()
    register(client, "uploader@example.test")
    login(client, "uploader@example.test")
    create_report(client)
    with app.app_context():
        report_id = Segnalazione.query.one().id
    token = csrf_token(client, f"/segnalazioni/{report_id}")
    response = client.post(
        f"/segnalazioni/{report_id}/allegati",
        data={"csrf_token": token, "file": (BytesIO(b"not really a png"), "fake.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    with app.app_context():
        assert AllegatoMultimediale.query.filter_by(fk_segnalazione=report_id).count() == 1


def test_upload_accepts_a_decodable_image(app):
    client = app.test_client()
    register(client, "image-uploader@example.test")
    login(client, "image-uploader@example.test")
    create_report(client)
    with app.app_context():
        report_id = Segnalazione.query.one().id
    image_data = BytesIO()
    Image.new("RGB", (2, 2), color="green").save(image_data, format="PNG")
    image_data.seek(0)
    token = csrf_token(client, f"/segnalazioni/{report_id}")
    response = client.post(
        f"/segnalazioni/{report_id}/allegati",
        data={"csrf_token": token, "file": (image_data, "foto.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    with app.app_context():
        attachments = AllegatoMultimediale.query.filter_by(fk_segnalazione=report_id).order_by(AllegatoMultimediale.id).all()
        assert len(attachments) == 2
        assert attachments[-1].tipo_file == "Foto"


def test_upload_cleans_partial_file_write(app, monkeypatch):
    client = app.test_client()
    register(client, "partial-upload@example.test")
    login(client, "partial-upload@example.test")
    create_report(client)
    with app.app_context():
        report_id = Segnalazione.query.one().id
    existing_files = set(Path(app.config["UPLOAD_FOLDER"]).iterdir())
    image_data = BytesIO()
    Image.new("RGB", (2, 2), color="green").save(image_data, format="PNG")
    image_data.seek(0)
    token = csrf_token(client, f"/segnalazioni/{report_id}")
    original_write_bytes = Path.write_bytes

    def fail_after_partial_write(path, data):
        original_write_bytes(path, data[:10])
        raise OSError("simulated disk failure")

    monkeypatch.setattr(Path, "write_bytes", fail_after_partial_write)
    with pytest.raises(OSError, match="simulated disk failure"):
        client.post(
            f"/segnalazioni/{report_id}/allegati",
            data={"csrf_token": token, "file": (image_data, "foto.png", "image/png")},
            content_type="multipart/form-data",
        )
    assert set(Path(app.config["UPLOAD_FOLDER"]).iterdir()) == existing_files
    with app.app_context():
        assert AllegatoMultimediale.query.filter_by(fk_segnalazione=report_id).count() == 1


def test_admin_can_manage_roles_but_last_admin_is_preserved(app):
    with app.app_context():
        user = Utente(nome="Ada", cognome="Admin", email="admin@example.test", fk_quartiere=1, tipo_ruolo="Admin")
        user.set_password("password-sicura-123")
        citizen = Utente(nome="Leo", cognome="Cittadino", email="citizen@example.test", fk_quartiere=1)
        citizen.set_password("password-sicura-123")
        db.session.add_all([user, citizen])
        db.session.commit()
        admin_id, citizen_id = user.id, citizen.id
    client = app.test_client()
    login(client, "admin@example.test")
    token = csrf_token(client, "/amministrazione/utenti")
    response = client.post(f"/amministrazione/utenti/{citizen_id}/ruolo", data={"csrf_token": token, "tipo_ruolo": "MembroComitato"})
    assert response.status_code == 302
    token = csrf_token(client, "/amministrazione/utenti")
    response = client.post(f"/amministrazione/utenti/{admin_id}/ruolo", data={"csrf_token": token, "tipo_ruolo": "Cittadino"})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Utente, admin_id).tipo_ruolo == "Admin"
        assert db.session.get(Utente, citizen_id).tipo_ruolo == "MembroComitato"


def test_duplicate_links_reject_cycles(app):
    with app.app_context():
        author = Utente(nome="Ada", cognome="Luna", email="author@example.test", fk_quartiere=1)
        author.set_password("password-sicura-123")
        db.session.add(author)
        db.session.flush()
        reports = [
            Segnalazione(titolo=f"Problema {index}", descrizione_testuale="Descrizione", latitudine=45, longitudine=9, indirizzo="Via Roma", fk_utente_autore=author.id, fk_categoria=1, fk_quartiere=1)
            for index in (1, 2)
        ]
        committee = Utente(nome="Comitato", cognome="Uno", email="committee@example.test", fk_quartiere=1, tipo_ruolo="MembroComitato")
        committee.set_password("password-sicura-123")
        db.session.add_all([*reports, committee])
        db.session.commit()
        first_id, second_id, committee_id = reports[0].id, reports[1].id, committee.id
    client = app.test_client()
    login(client, "committee@example.test")
    token = csrf_token(client, "/comitato/segnalazioni")
    assert client.post(f"/comitato/segnalazioni/{first_id}/duplicato", data={"csrf_token": token, "padre_id": second_id}).status_code == 302
    token = csrf_token(client, "/comitato/segnalazioni")
    client.post(f"/comitato/segnalazioni/{second_id}/duplicato", data={"csrf_token": token, "padre_id": first_id})
    with app.app_context():
        assert db.session.get(Segnalazione, first_id).fk_segnalazione_padre == second_id
        assert db.session.get(Segnalazione, second_id).fk_segnalazione_padre is None


def test_dossier_prevents_duplicate_associations(app):
    with app.app_context():
        author = Utente(nome="Ada", cognome="Luna", email="author2@example.test", fk_quartiere=1)
        author.set_password("password-sicura-123")
        committee = Utente(nome="Comitato", cognome="Uno", email="committee2@example.test", fk_quartiere=1, tipo_ruolo="MembroComitato")
        committee.set_password("password-sicura-123")
        db.session.add_all([author, committee])
        db.session.flush()
        report = Segnalazione(titolo="Buche", descrizione_testuale="Descrizione", latitudine=45, longitudine=9, indirizzo="Via Roma", fk_utente_autore=author.id, fk_categoria=1, fk_quartiere=1)
        dossier = Dossier(titolo="Centro", fk_utente_creatore=committee.id)
        db.session.add_all([report, dossier])
        db.session.commit()
        report_id, dossier_id = report.id, dossier.id
    client = app.test_client()
    login(client, "committee2@example.test")
    token = csrf_token(client, f"/dossier/{dossier_id}")
    response = client.post(f"/dossier/{dossier_id}", data={"csrf_token": token, "segnalazione_id": report_id})
    assert response.status_code == 302
    token = csrf_token(client, f"/dossier/{dossier_id}")
    client.post(f"/dossier/{dossier_id}", data={"csrf_token": token, "segnalazione_id": report_id})
    with app.app_context():
        assert DossierSegnalazione.query.count() == 1


def test_dossier_rejects_overlong_notes(app):
    with app.app_context():
        committee = Utente(nome="Ada", cognome="Comitato", email="notes@example.test", fk_quartiere=1, tipo_ruolo="MembroComitato")
        committee.set_password("password-sicura-123")
        db.session.add(committee)
        db.session.commit()
    client = app.test_client()
    login(client, "notes@example.test")
    token = csrf_token(client, "/dossier")
    response = client.post("/dossier", data={
        "csrf_token": token,
        "titolo": "Dossier valido",
        "note_comitato": "x" * 5001,
    })
    assert response.status_code == 200
    assert b"5000 caratteri" in response.data
    with app.app_context():
        assert Dossier.query.count() == 0


def test_dossier_list_is_paginated(app):
    with app.app_context():
        committee = Utente(nome="Ada", cognome="Comitato", email="dossier-pages@example.test", fk_quartiere=1, tipo_ruolo="MembroComitato")
        committee.set_password("password-sicura-123")
        db.session.add(committee)
        db.session.flush()
        db.session.add_all([
            Dossier(titolo=f"Dossier {index}", fk_utente_creatore=committee.id)
            for index in range(13)
        ])
        db.session.commit()
    client = app.test_client()
    login(client, "dossier-pages@example.test")
    first_page = client.get("/dossier")
    second_page = client.get("/dossier?page=2")
    assert b"Pagina 1 di 2" in first_page.data
    assert b"Pagina 2 di 2" in second_page.data
