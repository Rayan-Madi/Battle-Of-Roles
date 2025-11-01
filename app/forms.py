"""
Formulaires Flask-WTF pour login et register
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur', 
                          validators=[DataRequired(message='Nom d\'utilisateur requis'), 
                                     Length(min=3, max=80, message='3 à 80 caractères')])
    password = PasswordField('Mot de passe', 
                            validators=[DataRequired(message='Mot de passe requis')])
    submit = SubmitField('Se connecter')


class RegisterForm(FlaskForm):
    """Formulaire d'inscription"""
    username = StringField('Nom d\'utilisateur', 
                          validators=[DataRequired(message='Nom d\'utilisateur requis'), 
                                     Length(min=3, max=80, message='3 à 80 caractères')])
    password = PasswordField('Mot de passe', 
                            validators=[DataRequired(message='Mot de passe requis'), 
                                       Length(min=6, message='Minimum 6 caractères')])
    password2 = PasswordField('Confirmer le mot de passe', 
                             validators=[DataRequired(message='Confirmation requise'), 
                                        EqualTo('password', message='Les mots de passe doivent correspondre')])
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        """Vérifie que le username n'existe pas déjà"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur existe déjà.')