from flask import Flask

def create_app ():
    app = Flask (__name__)
    @app.route('/')

    def home ():
        return " barbeaia fuancionando"
    
    def servicos(/servicos):
        return "lista de servicos em breve"
    
    return app 


