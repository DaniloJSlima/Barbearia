"""Regras de agenda: horários disponíveis e verificação de conflitos."""
from datetime import date, datetime, time, timedelta

from flask import current_app

from app.extensions import db
from app.models import Agendamento


def dia_funciona(dia: date) -> bool:
    return dia.weekday() in current_app.config['DIAS_FUNCIONAMENTO']


def data_permitida(dia: date) -> bool:
    hoje = date.today()
    limite = hoje + timedelta(days=current_app.config['DIAS_ANTECEDENCIA_MAX'])
    return hoje <= dia <= limite and dia_funciona(dia)


def agendamentos_ativos(barbeiro_id, inicio, fim, ignorar_id=None):
    """Agendamentos do barbeiro que se sobrepõem ao intervalo [inicio, fim)."""
    consulta = db.select(Agendamento).where(
        Agendamento.barbeiro_id == barbeiro_id,
        Agendamento.status == Agendamento.STATUS_AGENDADO,
        Agendamento.inicio < fim,
        Agendamento.fim > inicio,
    )
    if ignorar_id:
        consulta = consulta.where(Agendamento.id != ignorar_id)
    return db.session.execute(consulta).scalars().all()


def tem_conflito(barbeiro_id, inicio, fim, ignorar_id=None) -> bool:
    return bool(agendamentos_ativos(barbeiro_id, inicio, fim, ignorar_id))


def horarios_disponiveis(barbeiro_id, servico, dia: date):
    """Lista de datetimes de início livres para o serviço no dia."""
    if not data_permitida(dia):
        return []

    cfg = current_app.config
    abertura = datetime.combine(dia, time(cfg['HORA_ABERTURA']))
    fechamento = datetime.combine(dia, time(cfg['HORA_FECHAMENTO']))
    passo = timedelta(minutes=cfg['INTERVALO_AGENDA_MIN'])
    duracao = timedelta(minutes=servico.duracao_min)
    agora = datetime.now()

    ocupados = agendamentos_ativos(barbeiro_id, abertura, fechamento)

    livres = []
    slot = abertura
    while slot + duracao <= fechamento:
        fim = slot + duracao
        if slot > agora and not any(a.inicio < fim and a.fim > slot for a in ocupados):
            livres.append(slot)
        slot += passo
    return livres


def horario_valido(barbeiro_id, servico, inicio: datetime) -> bool:
    return inicio in horarios_disponiveis(barbeiro_id, servico, inicio.date())
