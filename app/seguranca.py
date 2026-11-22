import secrets
from functools import wraps

from flask import abort, request, session
from flask_login import current_user, login_required


def _gerar_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def init_csrf(app):
    """Proteção CSRF simples: todo formulário POST precisa enviar o token da sessão."""

    @app.before_request
    def verificar_csrf():
        if request.method == 'POST':
            token = session.get('_csrf_token')
            enviado = request.form.get('csrf_token')
            if not token or not enviado or not secrets.compare_digest(token, enviado):
                abort(400, description='Token CSRF inválido. Recarregue a página e tente novamente.')

    app.jinja_env.globals['csrf_token'] = _gerar_csrf_token


def papel_requerido(*papeis):
    """Restringe a rota aos papéis informados (admin sempre tem acesso)."""

    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.papel not in papeis and not current_user.is_admin:
                abort(403)
            return f(*args, **kwargs)

        return wrapper

    return decorator
