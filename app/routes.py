"""
Routes principales de l'application Battle of Roles
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, abort
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Game, Turn
from app.forms import LoginForm, RegisterForm
from app.utils import calculate_winner, update_score, check_victory, format_game_result
from datetime import datetime
import random
import string
import traceback
from functools import wraps

bp = Blueprint('main', __name__)


# ============================================
# DÉCORATEUR ADMIN
# ============================================

def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès réservé aux administrateurs', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ROUTES PUBLIQUES
# ============================================

@bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
            return redirect(url_for('main.login'))
        
        session.clear()
        login_user(user, remember=False)
        flash(f'Bienvenue {user.username} !', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('main.lobby'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data
        
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Ce nom d\'utilisateur existe déjà', 'danger')
            return render_template('register.html', form=form)
        
        user = User(username=username, is_guest=False)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)


@bp.route('/guest')
def guest_login():
    """Connexion en tant qu'invité"""
    guest_name = f"Guest_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    
    guest_user = User(username=guest_name, is_guest=True)
    db.session.add(guest_user)
    db.session.commit()
    
    session.clear()
    login_user(guest_user, remember=False)
    flash(f'Bienvenue {guest_name} !', 'info')
    return redirect(url_for('main.lobby'))


@bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    session.clear()
    flash('Vous êtes déconnecté', 'info')
    response = redirect(url_for('main.index'))
    response.set_cookie('session', '', expires=0) 
    return response


# ============================================
# ROUTES DE JEU
# ============================================

@bp.route('/lobby')
@login_required
def lobby():
    """Lobby de recherche de partie"""
    old_waiting = Game.query.filter_by(
        player1_id=current_user.id,
        status='waiting'
    ).all()
    
    for old_game in old_waiting:
        db.session.delete(old_game)
    
    if old_waiting:
        db.session.commit()
    
    ongoing_game = Game.query.filter(
        ((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)),
        Game.status == 'ongoing'
    ).first()
    
    if ongoing_game:
        return redirect(url_for('main.game', game_id=ongoing_game.id))
    
    waiting_game = Game.query.filter(
        Game.status == 'waiting',
        Game.player1_id != current_user.id,
        Game.player2_id.is_(None)
    ).first()
    
    if waiting_game:
        waiting_game.player2_id = current_user.id
        waiting_game.status = 'ongoing'
        db.session.commit()
        flash('Adversaire trouvé ! La partie commence.', 'success')
        return redirect(url_for('main.game', game_id=waiting_game.id))
    
    new_game = Game(
        player1_id=current_user.id,
        player2_id=None,
        status='waiting',
        score1=0,
        score2=0
    )
    db.session.add(new_game)
    db.session.commit()
    
    return render_template('lobby.html', game=new_game)


@bp.route('/game/<int:game_id>')
@login_required
def game(game_id):
    """Page de jeu"""
    game = Game.query.get_or_404(game_id)
    
    valid_players = [game.player1_id]
    if game.player2_id:
        valid_players.append(game.player2_id)
    
    if current_user.id not in valid_players:
        flash('Vous ne faites pas partie de cette partie', 'danger')
        return redirect(url_for('main.lobby'))
    
    player_num = 1 if current_user.id == game.player1_id else 2
    
    return render_template('game.html', game=game, player_num=player_num)


@bp.route('/api/check-game-ready/<int:game_id>')
@login_required
def check_game_ready(game_id):
    """Vérifie si la partie a trouvé un adversaire"""
    try:
        game = Game.query.get(game_id)
        
        if not game:
            return jsonify({'ready': False, 'deleted': True})
        
        if game.status == 'ongoing' and game.player2_id is not None and game.player1_id != game.player2_id:
            return jsonify({'ready': True, 'game_id': game.id})
        
        return jsonify({'ready': False})
        
    except Exception as e:
        print(f"❌ Erreur dans check_game_ready: {e}")
        return jsonify({'ready': False, 'error': str(e)})


@bp.route('/api/game/<int:game_id>/state')
@login_required
def game_state(game_id):
    """Retourne l'état actuel de la partie (API)"""
    try:
        game = Game.query.get(game_id)
        
        if not game:
            return jsonify({'error': 'Partie non trouvée'}), 404
        
        valid_players = [game.player1_id]
        if game.player2_id:
            valid_players.append(game.player2_id)
        
        if current_user.id not in valid_players:
            return jsonify({'error': 'Non autorisé'}), 403
        
        player_num = 1 if current_user.id == game.player1_id else 2
        
        db.session.expire_all()
        
        last_turn = Turn.query.filter_by(game_id=game_id).order_by(Turn.id.desc()).first()
        
        waiting_for = None
        if game.status == 'ongoing':
            if not last_turn:
                waiting_for = 'both'
            elif last_turn.player1_card and last_turn.player2_card:
                waiting_for = 'both'
            elif last_turn.player1_card and not last_turn.player2_card:
                waiting_for = 2
            elif last_turn.player2_card and not last_turn.player1_card:
                waiting_for = 1
            else:
                waiting_for = 'both'
        
        print(f"🎮 Game #{game_id} - waiting_for: {waiting_for}, player: {player_num}")
        if last_turn:
            print(f"   Turn #{last_turn.turn_number} (ID:{last_turn.id}): P1={last_turn.player1_card}, P2={last_turn.player2_card}")
        
        player2_username = game.player2.username if game.player2_id else "En attente..."
        
        last_turn_data = None
        if last_turn:
            last_turn_data = {
                'turn_number': last_turn.turn_number,
                'player1_card': last_turn.player1_card,
                'player2_card': last_turn.player2_card,
                'winner_id': last_turn.winner_id,
                'joker_used': last_turn.joker_used_by is not None
            }
        
        return jsonify({
            'status': game.status,
            'score1': game.score1,
            'score2': game.score2,
            'joker_used_p1': game.joker_used_p1,
            'joker_used_p2': game.joker_used_p2,
            'player1': game.player1.username,
            'player2': player2_username,
            'player1_id': game.player1_id,
            'player2_id': game.player2_id,
            'waiting_for': waiting_for,
            'last_turn': last_turn_data,
            'your_player_num': player_num
        })
    except Exception as e:
        print(f"❌ Erreur dans game_state: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/game/<int:game_id>/play', methods=['POST'])
@login_required
def play_turn(game_id):
    """Jouer une carte (API)"""
    try:
        game = Game.query.get(game_id)
        if not game:
            return jsonify({'error': 'Partie non trouvée'}), 404
        
        if current_user.id not in [game.player1_id, game.player2_id]:
            return jsonify({'error': 'Non autorisé'}), 403
        if game.status != 'ongoing':
            return jsonify({'error': 'La partie n\'est pas en cours'}), 400
        
        data = request.get_json()
        card = data.get('card')
        use_joker = data.get('use_joker', False)
        
        if card not in ['Mage', 'Chevalier', 'Loup']:
            return jsonify({'error': 'Carte non valide'}), 400
        
        player_num = 1 if current_user.id == game.player1_id else 2
        
        print(f"\n➡️ P{player_num} ({current_user.username}) joue {card} (Joker: {use_joker})")
        
        db.session.expire(game)
        db.session.refresh(game)
        
        current_turn = Turn.query.filter_by(game_id=game.id).order_by(Turn.id.desc()).first()
        
        print(f"   📊 Dernier tour trouvé: {current_turn}")
        if current_turn:
            print(f"      Turn #{current_turn.turn_number}: P1={current_turn.player1_card}, P2={current_turn.player2_card}")
        
        create_new_turn = False
        
        if not current_turn:
            create_new_turn = True
            print(f"   🆕 Aucun tour existant -> création")
        elif current_turn.player1_card and current_turn.player2_card:
            create_new_turn = True
            print(f"   🆕 Tour {current_turn.turn_number} complet -> nouveau tour")
        else:
            if player_num == 1 and current_turn.player1_card:
                print(f"   ❌ P1 a déjà joué {current_turn.player1_card} dans ce tour")
                return jsonify({'error': 'Vous avez déjà joué dans ce tour'}), 400
            
            if player_num == 2 and current_turn.player2_card:
                print(f"   ❌ P2 a déjà joué {current_turn.player2_card} dans ce tour")
                return jsonify({'error': 'Vous avez déjà joué dans ce tour'}), 400
            
            print(f"   ♻️ Utilisation du tour {current_turn.turn_number} en cours")
        
        if create_new_turn:
            turn_number = (current_turn.turn_number if current_turn else 0) + 1
            current_turn = Turn(game_id=game.id, turn_number=turn_number)
            db.session.add(current_turn)
            db.session.flush()
            print(f"   ✅ Nouveau tour {turn_number} créé (ID: {current_turn.id})")
        
        print(f"   ✅ Carte {card} acceptée")
        
        if use_joker:
            if (player_num == 1 and game.joker_used_p1) or (player_num == 2 and game.joker_used_p2):
                print("   ❌ Joker déjà utilisé")
                return jsonify({'error': 'Vous avez déjà utilisé votre Bouffon'}), 400
        
        if player_num == 1:
            current_turn.player1_card = card
            print(f"   ✅ P1 joue {card} dans tour #{current_turn.turn_number}")
        else:
            current_turn.player2_card = card
            print(f"   ✅ P2 joue {card} dans tour #{current_turn.turn_number}")
        
        if use_joker:
            current_turn.joker_used_by = current_user.id
            if player_num == 1:
                game.joker_used_p1 = True
            else:
                game.joker_used_p2 = True
            print("   🃏 Bouffon utilisé")
        
        db.session.commit()
        print("   💾 Carte sauvegardée")
        
        if current_turn.player1_card and current_turn.player2_card:
            print(f"   ⚔️ Calcul: {current_turn.player1_card} vs {current_turn.player2_card}")
            joker_active = current_turn.joker_used_by is not None
            winner = calculate_winner(current_turn.player1_card, current_turn.player2_card, joker_active)
            
            if winner == 0:
                print(f"   ⚖️ Égalité ! Score inchangé: {game.score1}-{game.score2}")
                current_turn.winner_id = None
            elif winner == 1:
                current_turn.winner_id = game.player1_id
                update_score(game, 1)
                print(f"   🏆 Vainqueur: P1. Score: {game.score1}-{game.score2}")
            elif winner == 2:
                current_turn.winner_id = game.player2_id
                update_score(game, 2)
                print(f"   🏆 Vainqueur: P2. Score: {game.score1}-{game.score2}")
            
            final_winner_id = check_victory(game)
            if final_winner_id:
                game.status = 'finished'
                game.finished_at = datetime.utcnow()
                print(f"   🎉 Fin de partie ! Vainqueur: {final_winner_id}")
                
                winner_user = User.query.get(final_winner_id)
                if winner_user: 
                    winner_user.wins += 1
                
                p1_user = User.query.get(game.player1_id)
                p2_user = User.query.get(game.player2_id)
                if p1_user: 
                    p1_user.games_played += 1
                if p2_user: 
                    p2_user.games_played += 1
            
            db.session.commit()
            print("   💾 Résultat sauvegardé\n")
        else:
            print(f"   ⏳ En attente de l'autre joueur\n")
        
        return jsonify({'success': True, 'message': 'Carte jouée'})
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Erreur serveur: ' + str(e)}), 500


@bp.route('/leaderboard')
def leaderboard():
    """Classement global"""
    users = User.query.filter_by(is_guest=False).order_by(User.wins.desc(), User.games_played).limit(50).all()
    return render_template('leaderboard.html', users=users)


@bp.route('/history')
@login_required
def history():
    """Historique des parties du joueur"""
    games = Game.query.filter(
        ((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)) &
        (Game.status == 'finished')
    ).order_by(Game.finished_at.desc()).all()
    
    return render_template('history.html', games=games)


@bp.route('/convert-guest', methods=['POST'])
@login_required
def convert_guest():
    """Convertit un compte invité en compte permanent"""
    if not current_user.is_guest:
        return jsonify({'error': 'Vous n\'êtes pas un invité'}), 400
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
    
    current_user.username = username
    current_user.set_password(password)
    current_user.is_guest = False
    
    db.session.commit()
    
    flash('Votre compte a été créé avec succès !', 'success')
    return jsonify({'success': True, 'message': 'Compte créé'})


# ============================================
# ROUTES ADMIN
# ============================================

@bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Tableau de bord administrateur"""
    total_users = User.query.count()
    real_users = User.query.filter_by(is_guest=False).count()
    total_games = Game.query.filter_by(status='finished').count()
    active_games = Game.query.filter_by(status='ongoing').count()
    guests = User.query.filter_by(is_guest=True).count()
    admins = User.query.filter_by(is_admin=True).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_games = Game.query.filter_by(status='finished').order_by(Game.finished_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         real_users=real_users,
                         total_games=total_games,
                         active_games=active_games,
                         guests=guests,
                         admins=admins,
                         recent_users=recent_users,
                         recent_games=recent_games)


@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Liste de tous les utilisateurs"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/admin/games')
@login_required
@admin_required
def admin_games():
    """Liste de toutes les parties"""
    games = Game.query.order_by(Game.created_at.desc()).limit(100).all()
    return render_template('admin/games.html', games=games)


@bp.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Activer/désactiver le statut admin d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier vos propres droits admin', 'warning')
        return redirect(url_for('main.admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "activé" if user.is_admin else "désactivé"
    flash(f'Statut admin {status} pour {user.username}', 'success')
    return redirect(url_for('main.admin_users'))


@bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte', 'danger')
        return redirect(url_for('main.admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur {username} supprimé', 'success')
    return redirect(url_for('main.admin_users'))


@bp.route('/admin/game/<int:game_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_game(game_id):
    """Supprimer une partie"""
    game = Game.query.get_or_404(game_id)
    
    db.session.delete(game)
    db.session.commit()
    
    flash(f'Partie #{game_id} supprimée', 'success')
    return redirect(url_for('main.admin_games'))