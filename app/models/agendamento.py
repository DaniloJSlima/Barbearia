from datetime import datetime

from app.extensions import db


class Agendamento(db.Model):
    __tablename__ = 'agendamento'

    STATUS_AGENDADO = 'agendado'
    STATUS_CONCLUIDO = 'concluido'
    STATUS_CANCELADO = 'cancelado'
    STATUS_FALTOU = 'faltou'
    STATUS = (STATUS_AGENDADO, STATUS_CONCLUIDO, STATUS_CANCELADO, STATUS_FALTOU)

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    barbeiro_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    inicio = db.Column(db.DateTime, nullable=False, index=True)
    fim = db.Column(db.DateTime, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_AGENDADO)
    observacao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    cliente = db.relationship('Usuario', foreign_keys=[cliente_id], backref='agendamentos_cliente')
    barbeiro = db.relationship('Usuario', foreign_keys=[barbeiro_id], backref='agendamentos_barbeiro')
    servico = db.relationship('Servico', backref='agendamentos')

    __table_args__ = (
        db.CheckConstraint('fim > inicio', name='ck_agendamento_periodo'),
        db.CheckConstraint(
            "status IN ('agendado', 'concluido', 'cancelado', 'faltou')",
            name='ck_agendamento_status',
        ),
    )

    @property
    def pode_cancelar(self):
        return self.status == self.STATUS_AGENDADO and self.inicio > datetime.now()

    def __repr__(self):
        return f'<Agendamento {self.id} {self.inicio:%d/%m %H:%M}>'
