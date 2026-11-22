from datetime import date, datetime, timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.agenda import data_permitida, horario_valido, horarios_disponiveis
from app.extensions import db
from app.models import Agendamento, Servico, Usuario
from app.seguranca import papel_requerido

bp = Blueprint('agendamentos', __name__)


def _parse_data(texto, padrao=None):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return padrao


def _barbeiros_ativos():
    return db.session.execute(
        db.select(Usuario).filter_by(papel=Usuario.PAPEL_BARBEIRO, ativo=True).order_by(Usuario.nome)
    ).scalars().all()


def _servicos_ativos():
    return db.session.execute(
        db.select(Servico).filter_by(ativo=True).order_by(Servico.nome)
    ).scalars().all()


@bp.route('/agendar', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        servico = db.session.get(Servico, request.form.get('servico_id', type=int))
        barbeiro_id = request.form.get('barbeiro_id', type=int)
        try:
            inicio = datetime.fromisoformat(request.form.get('horario', ''))
        except ValueError:
            inicio = None

        # trava a linha do barbeiro para evitar dois agendamentos simultâneos no mesmo horário
        barbeiro = db.session.execute(
            db.select(Usuario).where(Usuario.id == barbeiro_id).with_for_update()
        ).scalar()

        if (not servico or not servico.ativo or not barbeiro or not barbeiro.is_barbeiro
                or not barbeiro.ativo or not inicio or barbeiro.id == current_user.id):
            db.session.rollback()
            flash('Dados do agendamento inválidos.', 'erro')
            return redirect(url_for('agendamentos.novo'))

        if not horario_valido(barbeiro.id, servico, inicio):
            db.session.rollback()
            flash('Esse horário acabou de ficar indisponível. Escolha outro.', 'erro')
            return redirect(url_for('agendamentos.novo', servico_id=servico.id,
                                    barbeiro_id=barbeiro.id, data=inicio.date().isoformat()))

        agendamento = Agendamento(
            cliente_id=current_user.id,
            barbeiro_id=barbeiro.id,
            servico_id=servico.id,
            inicio=inicio,
            fim=inicio + timedelta(minutes=servico.duracao_min),
            preco=servico.preco,
            observacao=request.form.get('observacao', '').strip()[:255] or None,
        )
        db.session.add(agendamento)
        db.session.commit()
        flash(f'Agendado! {servico.nome} com {barbeiro.nome} em {inicio:%d/%m às %H:%M}.', 'sucesso')
        return redirect(url_for('agendamentos.meus'))

    servicos = _servicos_ativos()
    barbeiros = _barbeiros_ativos()
    servico = db.session.get(Servico, request.args.get('servico_id', type=int) or 0)
    barbeiro = db.session.get(Usuario, request.args.get('barbeiro_id', type=int) or 0)
    dia = _parse_data(request.args.get('data'), date.today())

    horarios = None
    if servico and barbeiro and barbeiro.is_barbeiro:
        if not data_permitida(dia):
            flash('A barbearia não atende nessa data. Escolha outro dia.', 'aviso')
            horarios = []
        else:
            horarios = horarios_disponiveis(barbeiro.id, servico, dia)

    return render_template(
        'agendamentos/novo.html',
        servicos=servicos,
        barbeiros=barbeiros,
        servico=servico,
        barbeiro=barbeiro,
        dia=dia,
        horarios=horarios,
        data_min=date.today(),
        data_max=date.today() + timedelta(days=current_app.config['DIAS_ANTECEDENCIA_MAX']),
    )


@bp.route('/meus-agendamentos')
@login_required
def meus():
    agora = datetime.now()
    base = db.select(Agendamento).filter_by(cliente_id=current_user.id)
    proximos = db.session.execute(
        base.where(Agendamento.inicio >= agora, Agendamento.status == Agendamento.STATUS_AGENDADO)
        .order_by(Agendamento.inicio)
    ).scalars().all()
    historico = db.session.execute(
        base.where(db.or_(Agendamento.inicio < agora, Agendamento.status != Agendamento.STATUS_AGENDADO))
        .order_by(Agendamento.inicio.desc()).limit(50)
    ).scalars().all()
    return render_template('agendamentos/meus.html', proximos=proximos, historico=historico)


@bp.route('/agendamentos/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    agendamento = db.get_or_404(Agendamento, id)
    eh_dono = agendamento.cliente_id == current_user.id
    eh_equipe = current_user.is_admin or agendamento.barbeiro_id == current_user.id
    if not (eh_dono or eh_equipe):
        abort(403)
    if not agendamento.pode_cancelar:
        flash('Esse agendamento não pode mais ser cancelado.', 'erro')
    else:
        agendamento.status = Agendamento.STATUS_CANCELADO
        db.session.commit()
        flash('Agendamento cancelado.', 'sucesso')
    return redirect(request.referrer or url_for('main.painel'))


@bp.route('/agenda')
@papel_requerido(Usuario.PAPEL_BARBEIRO)
def agenda():
    dia = _parse_data(request.args.get('data'), date.today())
    barbeiros = _barbeiros_ativos() if current_user.is_admin else []

    if current_user.is_admin:
        barbeiro_id = request.args.get('barbeiro_id', type=int)
    else:
        barbeiro_id = current_user.id

    consulta = db.select(Agendamento).where(
        Agendamento.inicio >= datetime.combine(dia, datetime.min.time()),
        Agendamento.inicio < datetime.combine(dia + timedelta(days=1), datetime.min.time()),
    ).order_by(Agendamento.inicio)
    if barbeiro_id:
        consulta = consulta.filter_by(barbeiro_id=barbeiro_id)
    agendamentos = db.session.execute(consulta).scalars().all()

    validos = [a for a in agendamentos if a.status != Agendamento.STATUS_CANCELADO]
    previsto = sum(a.preco for a in validos)
    concluido = sum(a.preco for a in validos if a.status == Agendamento.STATUS_CONCLUIDO)

    return render_template(
        'agendamentos/agenda.html',
        dia=dia,
        agendamentos=agendamentos,
        barbeiros=barbeiros,
        barbeiro_id=barbeiro_id,
        previsto=previsto,
        concluido=concluido,
        timedelta=timedelta,
    )


@bp.route('/agendamentos/<int:id>/status', methods=['POST'])
@papel_requerido(Usuario.PAPEL_BARBEIRO)
def alterar_status(id):
    agendamento = db.get_or_404(Agendamento, id)
    if not current_user.is_admin and agendamento.barbeiro_id != current_user.id:
        abort(403)

    novo_status = request.form.get('status')
    if novo_status not in (Agendamento.STATUS_CONCLUIDO, Agendamento.STATUS_FALTOU, Agendamento.STATUS_CANCELADO):
        abort(400)
    if agendamento.status != Agendamento.STATUS_AGENDADO:
        flash('Esse agendamento já foi finalizado.', 'erro')
    else:
        agendamento.status = novo_status
        db.session.commit()
        flash('Status atualizado.', 'sucesso')
    return redirect(request.referrer or url_for('agendamentos.agenda'))
