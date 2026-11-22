from decimal import Decimal

import click

from app.extensions import db
from app.models import Servico, Usuario


def init_comandos(app):

    @app.cli.command('criar-admin')
    @click.option('--nome', prompt='Nome')
    @click.option('--email', prompt='E-mail')
    @click.option('--senha', prompt='Senha', hide_input=True, confirmation_prompt=True)
    def criar_admin(nome, email, senha):
        """Cria um usuário administrador."""
        email = email.strip().lower()
        if db.session.execute(db.select(Usuario).filter_by(email=email)).scalar():
            raise click.ClickException('Já existe um usuário com esse e-mail.')
        admin = Usuario(nome=nome, email=email, papel=Usuario.PAPEL_ADMIN)
        admin.definir_senha(senha)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Administrador {email} criado.')

    @app.cli.command('seed')
    def seed():
        """Cadastra serviços de exemplo (se ainda não houver nenhum)."""
        if db.session.execute(db.select(Servico)).first():
            click.echo('Já existem serviços cadastrados. Nada feito.')
            return
        exemplos = [
            ('Corte de cabelo', 'Corte na máquina e tesoura', '45.00', 30),
            ('Barba', 'Barba com toalha quente', '35.00', 30),
            ('Corte + Barba', 'Combo completo', '70.00', 60),
            ('Sobrancelha', 'Design na navalha', '15.00', 15),
            ('Pigmentação', 'Pigmentação de barba ou cabelo', '40.00', 30),
        ]
        for nome, descricao, preco, duracao in exemplos:
            db.session.add(Servico(nome=nome, descricao=descricao, preco=Decimal(preco), duracao_min=duracao))
        db.session.commit()
        click.echo(f'{len(exemplos)} serviços cadastrados.')
