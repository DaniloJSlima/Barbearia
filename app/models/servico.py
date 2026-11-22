from app.extensions import db


class Servico(db.Model):
    __tablename__ = 'servico'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao_min = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.CheckConstraint('preco >= 0', name='ck_servico_preco_positivo'),
        db.CheckConstraint('duracao_min > 0', name='ck_servico_duracao_positiva'),
    )

    def __repr__(self):
        return f'<Servico {self.nome}>'
