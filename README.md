# 🃏 Battle of Roles

Un jeu de cartes stratégique multijoueur développé avec Flask et MySQL. Deux joueurs s'affrontent dans des duels tactiques où Mage, Chevalier et Loup se battent pour la victoire. Attention au Bouffon qui inverse toutes les règles !

## 🎮 Règles du jeu

### Ordre normal
- 🐺 **Loup** bat 🔮 **Mage**
- 🔮 **Mage** bat ⚔️ **Chevalier**
- ⚔️ **Chevalier** bat 🐺 **Loup**

### Avec le Bouffon (🃏)
Quand le Bouffon est joué, l'ordre est **inversé** :
- 🐺 **Loup** perd contre 🔮 **Mage**
- 🔮 **Mage** perd contre ⚔️ **Chevalier**
- ⚔️ **Chevalier** perd contre 🐺 **Loup**

### Règles supplémentaires
- ❌ Un joueur ne peut pas jouer deux fois la même carte d'affilée
- 🃏 Le Bouffon ne peut être utilisé qu'**une seule fois** par partie
- 🏆 Le premier joueur à **3 points** gagne la partie

## 🚀 Installation

### Prérequis
- Python 3.8+
- MySQL 5.7+
- pip

### Étapes d'installation

1. **Cloner le projet**
```bash
git clone 
cd flask_card_game
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer MySQL**
Créez une base de données MySQL :
```sql
CREATE DATABASE battle_of_roles;
```

5. **Configurer les variables d'environnement**
Créez un fichier `.env` à la racine du projet :
```env
SECRET_KEY=votre-cle-secrete-ultra-securisee
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=votre_mot_de_passe
MYSQL_DB=battle_of_roles
```

6. **Lancer l'application**
```bash
python run.py
```

L'application sera accessible sur `http://localhost:5000`

## 📁 Structure du projet

```
flask_card_game/
│
├── app/
│   ├── __init__.py           # Init Flask, SQLAlchemy, LoginManager
│   ├── routes.py             # Routes principales
│   ├── models.py             # Tables MySQL (User, Game, Turn)
│   ├── forms.py              # Flask-WTF Forms
│   ├── utils.py              # Logique du jeu
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── lobby.html
│   │   ├── game.html
│   │   ├── leaderboard.html
│   │   └── history.html
│   └── static/
│       ├── css/
│       │   └── style.css     # Animations et styles
│       └── js/
│           └── game.js       # Logique client
│
├── config.py                 # Configuration
├── run.py                    # Point d'entrée
├── requirements.txt
└── README.md
```

## 🎯 Fonctionnalités

### Système de joueurs
- ✅ **Connexion** : Compte utilisateur avec mot de passe
- ✅ **Inscription** : Création de nouveau compte
- ✅ **Mode invité** : Jouer sans compte (pseudo temporaire `Guest_XXXX`)
- ✅ **Conversion** : Les invités peuvent créer un compte après la partie

### Gameplay
- ✅ Matchmaking automatique (recherche d'adversaire)
- ✅ Tour par tour en temps réel
- ✅ Validation des coups (pas de carte identique consécutive)
- ✅ Système de Bouffon (inversion des règles)
- ✅ Score en temps réel
- ✅ Détection automatique de la victoire

### Interface
- ✅ Animations CSS3 (flip de cartes, glow, effets visuels)
- ✅ Mise à jour en temps réel via polling AJAX
- ✅ Interface responsive
- ✅ Effets visuels selon la carte (couleurs, émojis)

### Statistiques
- ✅ Classement global des joueurs
- ✅ Historique des parties
- ✅ Statistiques personnelles (victoires, parties jouées, ratio)

## 🔧 Technologies utilisées

### Backend
- **Flask** : Framework web Python
- **SQLAlchemy** : ORM pour MySQL
- **Flask-Login** : Gestion des sessions utilisateurs
- **Flask-WTF** : Gestion des formulaires
- **PyMySQL** : Connecteur MySQL

### Frontend
- **HTML5** / **CSS3**
- **JavaScript** (Vanilla)
- **Fetch API** pour les requêtes AJAX

### Base de données
- **MySQL** : Stockage persistant

## 🎨 Animations et effets visuels

- 🔄 **Flip 3D** des cartes lors de la révélation
- ✨ **Glow** animé sur la carte gagnante
- 🌈 **Effet arc-en-ciel** quand le Bouffon est joué
- 💫 **Transitions fluides** entre les tours
- 📊 **Mise à jour dynamique** des scores

## 🗃️ Base de données

### Table `users`
```sql
- id (INT, PRIMARY KEY)
- username (VARCHAR, UNIQUE)
- password_hash (VARCHAR)
- is_guest (BOOLEAN)
- wins (INT)
- games_played (INT)
- created_at (DATETIME)
```

### Table `games`
```sql
- id (INT, PRIMARY KEY)
- player1_id (FK users.id)
- player2_id (FK users.id)
- score1 (INT)
- score2 (INT)
- status (VARCHAR) # 'waiting', 'ongoing', 'finished'
- joker_used_p1 (BOOLEAN)
- joker_used_p2 (BOOLEAN)
- created_at (DATETIME)
- finished_at (DATETIME)
```

### Table `turns`
```sql
- id (INT, PRIMARY KEY)
- game_id (FK games.id)
- turn_number (INT)
- player1_card (VARCHAR)
- player2_card (VARCHAR)
- joker_used_by (FK users.id)
- winner_id (FK users.id)
- created_at (DATETIME)
```

## 🎯 API Endpoints

### Pages
- `GET /` - Page d'accueil
- `GET /login` - Connexion
- `GET /register` - Inscription
- `GET /guest` - Connexion invité
- `GET /lobby` - Recherche de partie
- `GET /game/<id>` - Plateau de jeu
- `GET /leaderboard` - Classement
- `GET /history` - Historique

### API REST
- `GET /api/game/<id>/state` - État de la partie (JSON)
- `POST /api/game/<id>/play` - Jouer une carte
- `GET /api/check-game-ready/<id>` - Vérifier si adversaire trouvé
- `POST /convert-guest` - Convertir compte invité

## 🐛 Dépannage

### La base de données ne se crée pas
```bash
# Vérifiez votre connexion MySQL
mysql -u root -p

# Créez manuellement la base
CREATE DATABASE battle_of_roles;
```

### Erreur de connexion MySQL
Vérifiez vos variables d'environnement dans `config.py` ou `.env`

### Les parties ne se lancent pas
Ouvrez deux navigateurs différents ou deux fenêtres en navigation privée pour simuler deux joueurs

## 🚀 Déploiement

Pour déployer en production :

1. Changez `app.run(debug=True)` en `app.run(debug=False)`
2. Utilisez un vrai serveur WSGI (Gunicorn, uWSGI)
3. Configurez un reverse proxy (Nginx, Apache)
4. Utilisez une vraie SECRET_KEY aléatoire
5. Activez HTTPS

Exemple avec Gunicorn :
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 📝 Licence

Projet éducatif - Libre d'utilisation

## 👥 Auteur

Made By ME (Rayan.Madi)

---

**Bon jeu ! 🎮⚔️🔮🐺🃏**