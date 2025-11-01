"""
Initialisation de l'application Flask
Configuration de SQLAlchemy, LoginManager et routes
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialisation des extensions avec l'app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    # Import des modèles (nécessaire avant create_all)
    from app import models
    
    # Import des routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        db.create_all()
    
    return app

# Fonction pour charger l'utilisateur depuis la session
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))