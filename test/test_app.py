from io import BytesIO
import re
from decimal import Decimal

from PIL import Image

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


def create_report(client, title="Marciapiede danneggiato"):
    token = csrf_token(client, "/segnalazioni/nuova")
    return client.post("/segnalazioni/nuova", data={
        "csrf_token": token,
        "titolo": title,
        "descrizione_testuale": "Il marciapiede è danneggiato e difficile da percorrere.",
        "latitudine": "45.123456",
        "longitudine": "9.123456",
        "indirizzo": "Via Roma 10",
        "categoria_id": "1",
        "quartiere_id": "1",
    }, follow_redirects=False)


def test_public_pages_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/registrazione").status_code == 200
    assert client.get("/accesso").status_code == 200
    assert client.get("/health").json == {"status": "ok", "database": "connected"}


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

    other = app.test_client()
    register(other, "other@example.test")
    login(other, "other@example.test")
    token = csrf_token(other, "/accesso")
    denied = other.post(f"/segnalazioni/{report_id}/modifica", data={"csrf_token": token})
    assert denied.status_code == 403, denied.data[:500]


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
        assert AllegatoMultimediale.query.count() == 0


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
        assert AllegatoMultimediale.query.one().tipo_file == "Foto"


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
