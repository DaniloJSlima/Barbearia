# Barbearia

Sistema de agendamentos para barbearia em Flask + PostgreSQL.

## Perfis

- **Cliente** — cria conta, agenda (serviço → barbeiro → dia → horário livre), vê e cancela seus horários.
- **Barbeiro** — vê a agenda do dia e marca atendimentos como concluído / faltou / cancelado.
- **Admin** — painel com faturamento, gestão de serviços, usuários (cadastra barbeiros) e todos os agendamentos.

## Como rodar

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # ajuste DATABASE_URL e SECRET_KEY
flask db upgrade            # cria as tabelas
flask seed                  # serviços de exemplo (opcional)
flask criar-admin           # cria o primeiro administrador
flask run --port 5001       # ou: python run.py
```

Acesse http://127.0.0.1:5001. Depois de logar como admin, cadastre os barbeiros em **Admin → Usuários**.

Horário de funcionamento, intervalo entre horários e dias de atendimento são configuráveis no `.env` (veja `.env.example`).

## Estrutura

```
app/
  models/        Usuario, Servico, Agendamento
  routes/        main, auth, agendamentos, admin (blueprints)
  templates/     páginas Jinja
  static/css/    estilos
  agenda.py      cálculo de horários livres e conflitos
  seguranca.py   CSRF e controle de acesso por papel
  comandos.py    flask criar-admin / flask seed
migrations/      migrations do banco (Flask-Migrate)
```

Ao alterar um model: `flask db migrate -m "descrição"` e depois `flask db upgrade`.
