from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    PAPEL_CLIENTE = 'cliente'
    PAPEL_BARBEIRO = 'barbeiro'
    PAPEL_ADMIN = 'admin'
    PAPEIS = (PAPEL_CLIENTE, PAPEL_BARBEIRO, PAPEL_ADMIN)

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(20))
    senha_hash = db.Column(db.String(256), nullable=False)
    papel = db.Column(db.String(20), nullable=False, default=PAPEL_CLIENTE)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.CheckConstraint("papel IN ('cliente', 'barbeiro', 'admin')", name='ck_usuario_papel'),
    )

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self):
        return self.ativo

    @property
    def is_admin(self):
        return self.papel == self.PAPEL_ADMIN

    @property
    def is_barbeiro(self):
        return self.papel == self.PAPEL_BARBEIRO

    @property
    def is_cliente(self):
        return self.papel == self.PAPEL_CLIENTE

    def __repr__(self):
        return f'<Usuario {self.email}>'


@login_manager.user_loader
def carregar_usuario(usuario_id):
    return db.session.get(Usuario, int(usuario_id))
