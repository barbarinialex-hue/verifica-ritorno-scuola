from datetime import datetime, timezone

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Quartiere(db.Model):
    __tablename__ = "quartiere"
    __table_args__ = (
        db.UniqueConstraint("nome_quartiere", "cap_zona", name="uq_quartiere_nome_cap"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = db.Column(db.Integer, primary_key=True)
    nome_quartiere = db.Column(db.String(120), nullable=False)
    cap_zona = db.Column(db.String(10), nullable=False, default="00000")
    utenti = db.relationship("Utente", back_populates="quartiere")


class Categoria(db.Model):
    __tablename__ = "categoria"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = db.Column(db.Integer, primary_key=True)
    nome_categoria = db.Column(db.String(100), nullable=False, unique=True)
    descrizione = db.Column(db.Text)
    segnalazioni = db.relationship("Segnalazione", back_populates="categoria")


class Utente(db.Model):
    __tablename__ = "utente"
    __table_args__ = (
        db.CheckConstraint("tipo_ruolo IN ('Cittadino', 'MembroComitato', 'Admin')", name="ck_utente_ruolo"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_ruolo = db.Column(db.String(30), nullable=False, default="Cittadino", server_default="Cittadino")
    data_registrazione = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    fk_quartiere = db.Column(db.Integer, db.ForeignKey("quartiere.id", ondelete="RESTRICT"), nullable=False)

    quartiere = db.relationship("Quartiere", back_populates="utenti")
    segnalazioni = db.relationship("Segnalazione", back_populates="autore", foreign_keys="Segnalazione.fk_utente_autore")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Segnalazione(db.Model):
    __tablename__ = "segnalazione"
    __table_args__ = (
        db.CheckConstraint("latitudine >= -90 AND latitudine <= 90", name="ck_segnalazione_latitudine"),
        db.CheckConstraint("longitudine >= -180 AND longitudine <= 180", name="ck_segnalazione_longitudine"),
        db.CheckConstraint("stato_attuale IN ('Inviata', 'Approvata', 'Presa in Carico', 'Inclusa nel Dossier', 'Risolta')", name="ck_segnalazione_stato"),
        db.Index("ix_segnalazione_filtri", "fk_quartiere", "fk_categoria", "stato_attuale", "data_creazione"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(180), nullable=False)
    descrizione_testuale = db.Column(db.Text, nullable=False)
    latitudine = db.Column(db.Numeric(9, 6), nullable=False)
    longitudine = db.Column(db.Numeric(9, 6), nullable=False)
    indirizzo = db.Column(db.String(255), nullable=False)
    data_creazione = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    stato_attuale = db.Column(db.String(40), nullable=False, default="Inviata", server_default="Inviata")
    fk_utente_autore = db.Column(db.Integer, db.ForeignKey("utente.id", ondelete="RESTRICT"), nullable=False)
    fk_categoria = db.Column(db.Integer, db.ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=False)
    fk_quartiere = db.Column(db.Integer, db.ForeignKey("quartiere.id", ondelete="RESTRICT"), nullable=False)
    fk_segnalazione_padre = db.Column(db.Integer, db.ForeignKey("segnalazione.id", ondelete="SET NULL"))

    autore = db.relationship("Utente", back_populates="segnalazioni", foreign_keys=[fk_utente_autore])
    categoria = db.relationship("Categoria", back_populates="segnalazioni")
    quartiere = db.relationship("Quartiere")
    padre = db.relationship("Segnalazione", remote_side=[id], foreign_keys=[fk_segnalazione_padre])
    allegati = db.relationship("AllegatoMultimediale", back_populates="segnalazione", cascade="all, delete-orphan", passive_deletes=True)
    sostegni = db.relationship("Sostegno", back_populates="segnalazione", cascade="all, delete-orphan", passive_deletes=True)


class AllegatoMultimediale(db.Model):
    __tablename__ = "allegato_multimediale"
    __table_args__ = (
        db.CheckConstraint("tipo_file IN ('Foto', 'Video')", name="ck_allegato_tipo"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = db.Column(db.Integer, primary_key=True)
    url_file = db.Column(db.Text, nullable=False)
    tipo_file = db.Column(db.String(10), nullable=False)
    data_upload = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    fk_segnalazione = db.Column(db.Integer, db.ForeignKey("segnalazione.id", ondelete="CASCADE"), nullable=False, index=True)
    segnalazione = db.relationship("Segnalazione", back_populates="allegati")


class Sostegno(db.Model):
    __tablename__ = "sostegno"
    __table_args__ = (
        db.UniqueConstraint("fk_utente", "fk_segnalazione", name="uq_sostegno_utente_segnalazione"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = db.Column(db.Integer, primary_key=True)
    data_voto = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    fk_utente = db.Column(db.Integer, db.ForeignKey("utente.id", ondelete="CASCADE"), nullable=False)
    fk_segnalazione = db.Column(db.Integer, db.ForeignKey("segnalazione.id", ondelete="CASCADE"), nullable=False)
    segnalazione = db.relationship("Segnalazione", back_populates="sostegni")


class Dossier(db.Model):
    __tablename__ = "dossier"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(180), nullable=False)
    data_creazione = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    note_comitato = db.Column(db.Text)
    fk_utente_creatore = db.Column(db.Integer, db.ForeignKey("utente.id", ondelete="RESTRICT"), nullable=False)
    elementi = db.relationship("DossierSegnalazione", back_populates="dossier", cascade="all, delete-orphan", passive_deletes=True)


class DossierSegnalazione(db.Model):
    __tablename__ = "dossier_segnalazione"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    fk_dossier = db.Column(db.Integer, db.ForeignKey("dossier.id", ondelete="CASCADE"), primary_key=True)
    fk_segnalazione = db.Column(db.Integer, db.ForeignKey("segnalazione.id", ondelete="CASCADE"), primary_key=True)
    data_inserimento = db.Column(db.DateTime, nullable=False, default=utc_now, server_default=func.current_timestamp())
    dossier = db.relationship("Dossier", back_populates="elementi")
    segnalazione = db.relationship("Segnalazione")
