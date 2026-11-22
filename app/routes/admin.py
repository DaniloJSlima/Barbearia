from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Agendamento, Servico, Usuario
from app.seguranca import papel_requerido

bp = Blueprint('admin', __name__)


@bp.before_request
@papel_requerido(Usuario.PAPEL_ADMIN)
def somente_admin():
    pass


# ---------- Dashboard ----------

@bp.route('/')
def dashboard():
    hoje = date.today()
    inicio_dia = datetime.combine(hoje, datetime.min.time())
    inicio_mes = inicio_dia.replace(day=1)
    fim_dia = inicio_dia + timedelta(days=1)
    proximo_mes = (inicio_mes + timedelta(days=32)).replace(day=1)

    def soma_preco(*filtros):
        return db.session.execute(
            db.select(db.func.coalesce(db.func.sum(Agendamento.preco), 0)).where(*filtros)
        ).scalar()

    def contar(*filtros):
        return db.session.execute(db.select(db.func.count(Agendamento.id)).where(*filtros)).scalar()

    concluido = Agendamento.status == Agendamento.STATUS_CONCLUIDO
    no_mes = (Agendamento.inicio >= inicio_mes, Agendamento.inicio < proximo_mes)
    no_dia = (Agendamento.inicio >= inicio_dia, Agendamento.inicio < fim_dia)

    resumo = {
        'hoje_total': contar(*no_dia, Agendamento.status != Agendamento.STATUS_CANCELADO),
        'hoje_pendentes': contar(*no_dia, Agendamento.status == Agendamento.STATUS_AGENDADO),
        'faturamento_hoje': soma_preco(*no_dia, concluido),
        'faturamento_mes': soma_preco(*no_mes, concluido),
        'atendimentos_mes': contar(*no_mes, concluido),
        'faltas_mes': contar(*no_mes, Agendamento.status == Agendamento.STATUS_FALTOU),
        'clientes': db.session.execute(
            db.select(db.func.count(Usuario.id)).filter_by(papel=Usuario.PAPEL_CLIENTE)
        ).scalar(),
    }

    por_barbeiro = db.session.execute(
        db.select(Usuario.nome, db.func.count(Agendamento.id), db.func.coalesce(db.func.sum(Agendamento.preco), 0))
        .join(Agendamento, Agendamento.barbeiro_id == Usuario.id)
        .where(*no_mes, concluido)
        .group_by(Usuario.nome)
        .order_by(db.func.sum(Agendamento.preco).desc())
    ).all()

    por_servico = db.session.execute(
        db.select(Servico.nome, db.func.count(Agendamento.id))
        .join(Agendamento, Agendamento.servico_id == Servico.id)
        .where(*no_mes, Agendamento.status != Agendamento.STATUS_CANCELADO)
        .group_by(Servico.nome)
        .order_by(db.func.count(Agendamento.id).desc())
        .limit(5)
    ).all()

    proximos = db.session.execute(
        db.select(Agendamento)
        .where(Agendamento.inicio >= datetime.now(), Agendamento.status == Agendamento.STATUS_AGENDADO)
        .order_by(Agendamento.inicio)
        .limit(10)
    ).scalars().all()

    return render_template('admin/dashboard.html', resumo=resumo, por_barbeiro=por_barbeiro,
                           por_servico=por_servico, proximos=proximos, hoje=hoje)


# ---------- Serviços ----------

@bp.route('/servicos')
def servicos():
    servicos = db.session.execute(
        db.select(Servico).order_by(Servico.ativo.desc(), Servico.nome)
    ).scalars().all()
    return render_template('admin/servicos.html', servicos=servicos)


def _preencher_servico(servico):
    """Valida o formulário e preenche o serviço. Retorna lista de erros."""
    erros = []
    nome = request.form.get('nome', '').strip()
    try:
        preco = Decimal(request.form.get('preco', '').replace(',', '.'))
        if preco < 0:
            raise InvalidOperation
    except InvalidOperation:
        preco = None
        erros.append('Preço inválido.')
    duracao = request.form.get('duracao_min', type=int)

    if not nome:
        erros.append('Informe o nome do serviço.')
    if not duracao or duracao <= 0:
        erros.append('Duração deve ser um número de minutos maior que zero.')

    if not erros:
        servico.nome = nome
        servico.descricao = request.form.get('descricao', '').strip() or None
        servico.preco = preco
        servico.duracao_min = duracao
        servico.ativo = bool(request.form.get('ativo'))
    return erros


@bp.route('/servicos/novo', methods=['GET', 'POST'])
@bp.route('/servicos/<int:id>/editar', methods=['GET', 'POST'])
def servico_form(id=None):
    servico = db.get_or_404(Servico, id) if id else Servico(ativo=True)
    if request.method == 'POST':
        erros = _preencher_servico(servico)
        if erros:
            for e in erros:
                flash(e, 'erro')
        else:
            if not id:
                db.session.add(servico)
            db.session.commit()
            flash('Serviço salvo.', 'sucesso')
            return redirect(url_for('admin.servicos'))
    return render_template('admin/servico_form.html', servico=servico)


@bp.route('/servicos/<int:id>/alternar', methods=['POST'])
def servico_alternar(id):
    servico = db.get_or_404(Servico, id)
    servico.ativo = not servico.ativo
    db.session.commit()
    flash(f'Serviço {"ativado" if servico.ativo else "desativado"}.', 'sucesso')
    return redirect(url_for('admin.servicos'))


# ---------- Usuários / Equipe ----------

@bp.route('/usuarios')
def usuarios():
    papel = request.args.get('papel')
    busca = request.args.get('q', '').strip()
    consulta = db.select(Usuario).order_by(Usuario.nome)
    if papel in Usuario.PAPEIS:
        consulta = consulta.filter_by(papel=papel)
    if busca:
        termo = f'%{busca}%'
        consulta = consulta.where(db.or_(Usuario.nome.ilike(termo), Usuario.email.ilike(termo)))
    usuarios = db.session.execute(consulta).scalars().all()
    return render_template('admin/usuarios.html', usuarios=usuarios, papel=papel, busca=busca)


@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
def usuario_form(id=None):
    usuario = db.get_or_404(Usuario, id) if id else Usuario(papel=Usuario.PAPEL_BARBEIRO, ativo=True)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        papel = request.form.get('papel')
        senha = request.form.get('senha', '')
        ativo = bool(request.form.get('ativo'))

        erros = []
        if not nome:
            erros.append('Informe o nome.')
        if '@' not in email:
            erros.append('E-mail inválido.')
        if papel not in Usuario.PAPEIS:
            erros.append('Papel inválido.')
        if (not id or senha) and len(senha) < 6:
            erros.append('A senha precisa ter pelo menos 6 caracteres.')
        existente = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar()
        if existente and existente.id != usuario.id:
            erros.append('Já existe um usuário com esse e-mail.')
        if usuario.id == current_user.id and (papel != Usuario.PAPEL_ADMIN or not ativo):
            erros.append('Você não pode remover seu próprio acesso de administrador.')

        if erros:
            for e in erros:
                flash(e, 'erro')
        else:
            usuario.nome = nome
            usuario.email = email
            usuario.telefone = request.form.get('telefone', '').strip() or None
            usuario.papel = papel
            usuario.ativo = ativo
            if senha:
                usuario.definir_senha(senha)
            if not id:
                db.session.add(usuario)
            db.session.commit()
            flash('Usuário salvo.', 'sucesso')
            return redirect(url_for('admin.usuarios'))

    return render_template('admin/usuario_form.html', usuario=usuario, papeis=Usuario.PAPEIS)


# ---------- Agendamentos ----------

@bp.route('/agendamentos')
def agendamentos():
    inicio = request.args.get('de') or date.today().isoformat()
    fim = request.args.get('ate') or (date.today() + timedelta(days=7)).isoformat()
    status = request.args.get('status')
    barbeiro_id = request.args.get('barbeiro_id', type=int)

    try:
        dt_inicio = datetime.combine(date.fromisoformat(inicio), datetime.min.time())
        dt_fim = datetime.combine(date.fromisoformat(fim) + timedelta(days=1), datetime.min.time())
    except ValueError:
        abort(400)

    consulta = (
        db.select(Agendamento)
        .where(Agendamento.inicio >= dt_inicio, Agendamento.inicio < dt_fim)
        .order_by(Agendamento.inicio)
    )
    if status in Agendamento.STATUS:
        consulta = consulta.filter_by(status=status)
    if barbeiro_id:
        consulta = consulta.filter_by(barbeiro_id=barbeiro_id)

    lista = db.session.execute(consulta).scalars().all()
    barbeiros = db.session.execute(
        db.select(Usuario).filter_by(papel=Usuario.PAPEL_BARBEIRO).order_by(Usuario.nome)
    ).scalars().all()
    return render_template('admin/agendamentos.html', agendamentos=lista, barbeiros=barbeiros,
                           de=inicio, ate=fim, status=status, barbeiro_id=barbeiro_id,
                           todos_status=Agendamento.STATUS)
