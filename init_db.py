"""
Script pour recréer la base de données et créer un compte admin
À exécuter une seule fois après avoir modifié models.py
"""

from app import create_app, db
from app.models import User

def init_database():
    """Initialise la base de données avec un compte admin"""
    app = create_app()
    
    with app.app_context():
        print("🗑️  Suppression de l'ancienne base de données...")
        db.drop_all()
        
        print("🔨 Création de la nouvelle base de données...")
        db.create_all()
        
        print("👤 Création du compte administrateur...")
        admin = User(
            username='admin',
            is_admin=True,
            is_guest=False
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Base de données initialisée avec succès !")
        print("\n📋 Compte admin créé :")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n⚠️  IMPORTANT : Changez ce mot de passe après la première connexion !")

if __name__ == '__main__':
    init_database()