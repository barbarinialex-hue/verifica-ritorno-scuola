import re

import pytest

from app import create_app
from app.extensions import db
from app.models import Categoria, Quartiere


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-long-enough-for-csrf-and-session-signing",
        "JWT_SECRET_KEY": "test-jwt-secret-key-long-enough-for-hmac-signing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "WTF_CSRF_ENABLED": True,
    })
    with app.app_context():
        db.create_all()
        db.session.add_all([
            Quartiere(nome_quartiere="Centro", cap_zona="00000"),
            Categoria(nome_categoria="Altro", descrizione="Altre criticità"),
        ])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match, f"CSRF field not found on {path}"
    return match.group(1).decode()
