from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app import models  # noqa: F401  (registra os models para o Flask-Migrate)
    from app.seguranca import init_csrf
    from app.filtros import init_filtros
    from app.comandos import init_comandos
    from app.routes import registrar_blueprints

    init_csrf(app)
    init_filtros(app)
    init_comandos(app)
    registrar_blueprints(app)

    return app
