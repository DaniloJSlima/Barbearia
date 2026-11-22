from flask import render_template


def registrar_blueprints(app):
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.agendamentos import bp as agendamentos_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(agendamentos_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def erro(e):
        return render_template('erro.html', erro=e), e.code
