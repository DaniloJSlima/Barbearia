from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Servico, Usuario

bp = Blueprint('main', __name__)


@bp.route('/')
def home():
    servicos = db.session.execute(
        db.select(Servico).filter_by(ativo=True).order_by(Servico.nome)
    ).scalars().all()
    barbeiros = db.session.execute(
        db.select(Usuario).filter_by(papel=Usuario.PAPEL_BARBEIRO, ativo=True).order_by(Usuario.nome)
    ).scalars().all()
    return render_template('index.html', servicos=servicos, barbeiros=barbeiros)


@bp.route('/servicos')
def servicos():
    servicos = db.session.execute(
        db.select(Servico).filter_by(ativo=True).order_by(Servico.nome)
    ).scalars().all()
    return render_template('servicos.html', servicos=servicos)


@bp.route('/painel')
@login_required
def painel():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    if current_user.is_barbeiro:
        return redirect(url_for('agendamentos.agenda'))
    return redirect(url_for('agendamentos.meus'))
