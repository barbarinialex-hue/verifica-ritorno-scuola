import re

import click

from app.extensions import db
from app.models import Categoria, Quartiere, Utente


def register_commands(app):
    @app.cli.command("seed-data")
    def seed_data():
        """Inserisce categorie iniziali e un quartiere da configurare."""
        with app.app_context():
            if not Quartiere.query.filter_by(nome_quartiere="Da configurare", cap_zona="00000").first():
                db.session.add(Quartiere(nome_quartiere="Da configurare", cap_zona="00000"))
            for name, description in [
                ("Strade e marciapiedi", "Buche, dissesti e problemi di accessibilità."),
                ("Illuminazione", "Guasti o carenze dell'illuminazione pubblica."),
                ("Verde pubblico", "Alberi, parchi e aree verdi."),
                ("Rifiuti e pulizia", "Raccolta rifiuti e pulizia degli spazi pubblici."),
                ("Altro", "Altre criticità del territorio."),
            ]:
                if not Categoria.query.filter_by(nome_categoria=name).first():
                    db.session.add(Categoria(nome_categoria=name, descrizione=description))
            db.session.commit()
            click.echo("Dati iniziali inseriti. Sostituisci il quartiere segnaposto con quelli reali.")

    @app.cli.command("add-quartiere")
    @click.option("--nome", required=True, help="Nome del quartiere.")
    @click.option("--cap", required=True, help="CAP o codice della zona.")
    def add_neighborhood(nome, cap):
        """Aggiunge un quartiere senza modificare gli account esistenti."""
        name = nome.strip()
        postal_code = cap.strip()
        if not name or len(name) > 120 or not postal_code or len(postal_code) > 10:
            raise click.ClickException("Nome o CAP non validi.")
        if Quartiere.query.filter_by(nome_quartiere=name, cap_zona=postal_code).first():
            raise click.ClickException("Questo quartiere è già presente.")
        db.session.add(Quartiere(nome_quartiere=name, cap_zona=postal_code))
        db.session.commit()
        click.echo(f"Quartiere aggiunto: {name} ({postal_code}).")

    @app.cli.command("add-categoria")
    @click.option("--nome", required=True, help="Nome univoco della categoria.")
    @click.option("--descrizione", default="", help="Descrizione facoltativa.")
    def add_category(nome, descrizione):
        """Aggiunge una categoria di segnalazione."""
        name = nome.strip()
        if not name or len(name) > 100 or len(descrizione) > 5000:
            raise click.ClickException("Nome o descrizione non validi.")
        if Categoria.query.filter_by(nome_categoria=name).first():
            raise click.ClickException("Questa categoria è già presente.")
        db.session.add(Categoria(nome_categoria=name, descrizione=descrizione.strip() or None))
        db.session.commit()
        click.echo(f"Categoria aggiunta: {name}.")

    @app.cli.command("create-admin")
    def create_admin():
        """Crea un amministratore iniziale senza esporre la password nei comandi."""
        with app.app_context():
            if not Quartiere.query.first():
                raise click.ClickException("Esegui prima 'flask seed-data' per creare un quartiere.")
            email = click.prompt("Email amministratore").strip().lower()
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
                raise click.ClickException("Indirizzo email non valido.")
            if Utente.query.filter_by(email=email).first():
                raise click.ClickException("Esiste già un account con questa email.")
            password = click.prompt("Password (almeno 12 caratteri)", hide_input=True, confirmation_prompt=True)
            if len(password) < 12:
                raise click.ClickException("La password deve contenere almeno 12 caratteri.")
            user = Utente(nome="Amministratore", cognome="Sistema", email=email, tipo_ruolo="Admin", fk_quartiere=Quartiere.query.first().id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo("Amministratore creato.")
