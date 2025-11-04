"""
Logique du jeu Battle of Roles
Règles, validation, calcul des gagnants
"""


CARDS = ['Mage', 'Chevalier', 'Loup']


RULES_NORMAL = {
    'Loup': 'Mage',      # Loup bat Mage
    'Mage': 'Chevalier', # Mage bat Chevalier
    'Chevalier': 'Loup'  # Chevalier bat Loup
}

RULES_INVERTED = {
    'Loup': 'Chevalier',  
    'Mage': 'Loup',       
    'Chevalier': 'Mage'   
}


def validate_move(previous_card, current_card):
    """
    Vérifie qu'un joueur ne joue pas deux fois la même carte d'affilée
    
    Args:
        previous_card (str): Carte jouée au tour précédent
        current_card (str): Carte que le joueur veut jouer
    
    Returns:
        bool: True si le coup est valide, False sinon
    """
    if previous_card is None:
        return True  
    
    if current_card not in CARDS:
        return False  
    
    return previous_card != current_card


def calculate_winner(card1, card2, joker_active=False):
    """
    Calcule le gagnant d'un tour selon les règles
    
    Args:
        card1 (str): Carte du joueur 1
        card2 (str): Carte du joueur 2
        joker_active (bool): True si le Bouffon a été joué ce tour
    
    Returns:
        int: 1 si joueur 1 gagne, 2 si joueur 2 gagne, 0 si égalité
    """
    if card1 == card2:
        return 0  # Égalité / Match Nul
    
    rules = RULES_INVERTED if joker_active else RULES_NORMAL
    
    if rules.get(card1) == card2:
        return 1
    elif rules.get(card2) == card1:
        return 2
    
    return 0  # Ne devrait SURTOUT VRAIMENT pas arriver 


def get_last_card_for_player(game, player_num):
    """
    Récupère la dernière carte jouée par un joueur dans un tour COMPLÉTÉ
    
    Args:
        game: Objet Game
        player_num (int): 1 ou 2
    
    Returns:
        str or None: Dernière carte jouée ou None
    """
    from app.models import Turn
    
    completed_turns = Turn.query.filter(
        Turn.game_id == game.id,
        Turn.player1_card.isnot(None),
        Turn.player2_card.isnot(None)
    ).order_by(Turn.id.desc()).all()
    
    if not completed_turns:
        return None  
    
    
    last_completed = completed_turns[0]
    
    if player_num == 1:
        return last_completed.player1_card
    else:
        return last_completed.player2_card

def update_score(game, winner_player_num):
    """
    Met à jour le score d'une partie
    
    Args:
        game: Objet Game
        winner_player_num (int): 1 ou 2
    """
    if winner_player_num == 1:
        game.score1 += 1
    elif winner_player_num == 2:
        game.score2 += 1


def check_victory(game):
    """
    Vérifie si un joueur a gagné la partie (3 points)
    
    Args:
        game: Objet Game
    
    Returns:
        int or None: ID du joueur gagnant ou None
    """
    if game.score1 >= 3:
        return game.player1_id
    elif game.score2 >= 3:
        return game.player2_id
    
    return None


def get_card_emoji(card_name):
    """
    Retourne un emoji représentant la carte
    
    Args:
        card_name (str): Nom de la carte
    
    Returns:
        str: Emoji correspondant
    """
    emojis = {
        'Mage': '🔮',
        'Chevalier': '⚔️',
        'Loup': '🐺',
        'Bouffon': '🃏'
    }
    return emojis.get(card_name, '❓')


def format_game_result(game):
    """
    Formate le résultat d'une partie pour l'affichage
    
    Args:
        game: Objet Game
    
    Returns:
        dict: Informations formatées sur la partie
    """
    winner = None
    if game.score1 >= 3:
        winner = game.player1
    elif game.score2 >= 3:
        winner = game.player2
    
    return {
        'game_id': game.id,
        'player1': game.player1.username,
        'player2': game.player2.username,
        'score1': game.score1,
        'score2': game.score2,
        'winner': winner.username if winner else None,
        'status': game.status
    }
