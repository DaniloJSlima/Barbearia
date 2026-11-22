from decimal import Decimal

ROTULOS_STATUS = {
    'agendado': 'Agendado',
    'concluido': 'Concluído',
    'cancelado': 'Cancelado',
    'faltou': 'Faltou',
}

DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']


def moeda(valor):
    valor = Decimal(valor or 0)
    texto = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'R$ {texto}'


def data_br(valor, formato='%d/%m/%Y'):
    return valor.strftime(formato) if valor else ''


def dia_semana(valor):
    return DIAS_SEMANA[valor.weekday()]


def init_filtros(app):
    app.jinja_env.filters['moeda'] = moeda
    app.jinja_env.filters['data_br'] = data_br
    app.jinja_env.filters['dia_semana'] = dia_semana
    app.jinja_env.filters['status'] = lambda s: ROTULOS_STATUS.get(s, s)
