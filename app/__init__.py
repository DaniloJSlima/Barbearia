from flask import Flask
from sqlalchemy import text
from config import Config
from app.extensions import db


def create_app ():
    app = Flask (__name__)
    app.config.from_object(Config)
    @app.route('/')
    def home ():
        return " barbeaia fuancionando"
    @app.route('/servicos')
    def servicos():
        return "lista de servicos em breve"
    @app.route('/teste_baco')
    def teste_baco():
        return "lista de servicos em breve"
    
    
    return app 
