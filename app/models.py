"""
Modèles de base de données SQLAlchemy
User, Game, Turn
"""
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """Modèle utilisateur (connecté ou invité)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Null pour invités
    is_guest = db.Column(db.Boolean, default=False)
    wins = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    games_as_player1 = db.relationship('Game', foreign_keys='Game.player1_id', backref='player1', lazy='dynamic')
    games_as_player2 = db.relationship('Game', foreign_keys='Game.player2_id', backref='player2', lazy='dynamic')
    
    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # ✅ nullable=True
    score1 = db.Column(db.Integer, default=0)
    score2 = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='waiting')  # 'waiting', 'ongoing', 'finished'
    joker_used_p1 = db.Column(db.Boolean, default=False)  # Bouffon joueur 1
    joker_used_p2 = db.Column(db.Boolean, default=False)  # Bouffon joueur 2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    turns = db.relationship('Turn', backref='game', lazy='dynamic', order_by='Turn.id')
    
    def __repr__(self):
        return f'<Game {self.id}: {self.player1.username} vs {self.player2.username}>'


class Turn(db.Model):
    """Modèle de tour de jeu"""
    __tablename__ = 'turns'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    turn_number = db.Column(db.Integer, nullable=False)  # Numéro du tour
    player1_card = db.Column(db.String(20), nullable=True)  # Carte jouée par joueur 1
    player2_card = db.Column(db.String(20), nullable=True)  # Carte jouée par joueur 2
    joker_used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Qui a utilisé le Bouffon
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Gagnant du tour
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations explicites pour éviter l'ambiguïté
    joker_user = db.relationship('User', foreign_keys=[joker_used_by])
    winner = db.relationship('User', foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<Turn {self.id} of Game {self.game_id}>'