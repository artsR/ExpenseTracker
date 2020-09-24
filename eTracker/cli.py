import click
from eTracker import db


def register(app):
    @app.cli.command('create_db')
    def create_db():
        """Creates database."""
        db.create_all()
