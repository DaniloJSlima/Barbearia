from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Usuario

bp = Blueprint('auth', __name__)

SENHA_MIN = 6


def _destino_seguro(destino):
    # evita redirecionamento para outro site via ?next=
    return destino if destino and not urlparse(destino).netloc and destino.startswith('/') else None


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.painel'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        usuario = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar()

        if not usuario or not usuario.verificar_senha(senha):
            flash('E-mail ou senha incorretos.', 'erro')
        elif not usuario.ativo:
            flash('Sua conta está desativada. Fale com a barbearia.', 'erro')
        else:
            login_user(usuario, remember=bool(request.form.get('lembrar')))
            return redirect(_destino_seguro(request.args.get('next')) or url_for('main.painel'))

    return render_template('auth/login.html')


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.painel'))

    dados = request.form
    if request.method == 'POST':
        nome = dados.get('nome', '').strip()
        email = dados.get('email', '').strip().lower()
        telefone = dados.get('telefone', '').strip()
        senha = dados.get('senha', '')

        erros = []
        if not nome:
            erros.append('Informe seu nome.')
        if '@' not in email:
            erros.append('Informe um e-mail válido.')
        if len(senha) < SENHA_MIN:
            erros.append(f'A senha precisa ter pelo menos {SENHA_MIN} caracteres.')
        if senha != dados.get('confirmar_senha'):
            erros.append('As senhas não conferem.')
        if email and db.session.execute(db.select(Usuario).filter_by(email=email)).scalar():
            erros.append('Já existe uma conta com esse e-mail.')

        if erros:
            for e in erros:
                flash(e, 'erro')
        else:
            usuario = Usuario(nome=nome, email=email, telefone=telefone or None)
            usuario.definir_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash('Conta criada com sucesso! Agora é só agendar.', 'sucesso')
            return redirect(url_for('agendamentos.novo'))

    return render_template('auth/registro.html', dados=dados)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'sucesso')
    return redirect(url_for('main.home'))


@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')

        if not nome:
            flash('Informe seu nome.', 'erro')
            return redirect(url_for('auth.perfil'))

        if nova_senha:
            if not current_user.verificar_senha(senha_atual):
                flash('Senha atual incorreta.', 'erro')
                return redirect(url_for('auth.perfil'))
            if len(nova_senha) < SENHA_MIN:
                flash(f'A nova senha precisa ter pelo menos {SENHA_MIN} caracteres.', 'erro')
                return redirect(url_for('auth.perfil'))
            current_user.definir_senha(nova_senha)

        current_user.nome = nome
        current_user.telefone = telefone or None
        db.session.commit()
        flash('Perfil atualizado.', 'sucesso')
        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html')
