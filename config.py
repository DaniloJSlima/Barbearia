import os
from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.getenv("DATABASE_URL", "")
    # SQLAlchemy 2.1 usa o driver "psycopg" (v3) por padrão; o projeto usa psycopg2
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _database_url()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-troque-esta-chave")

    HORA_ABERTURA = int(os.getenv("HORA_ABERTURA", 9))
    HORA_FECHAMENTO = int(os.getenv("HORA_FECHAMENTO", 19))
    INTERVALO_AGENDA_MIN = int(os.getenv("INTERVALO_AGENDA_MIN", 30))
    DIAS_FUNCIONAMENTO = [int(d) for d in os.getenv("DIAS_FUNCIONAMENTO", "0,1,2,3,4,5").split(",")]
    DIAS_ANTECEDENCIA_MAX = int(os.getenv("DIAS_ANTECEDENCIA_MAX", 30))
