let currentGameId = null;
let currentPlayerNum = null;
let isGuest = false;
let pollingInterval = null;
let lastGameState = null;

window.addEventListener('DOMContentLoaded', function() {
    const gameDataEl = document.getElementById('game-data');
    
    if (gameDataEl) {
        const gameId = parseInt(gameDataEl.getAttribute('data-game-id'), 10);
        const playerNum = parseInt(gameDataEl.getAttribute('data-player-num'), 10);
        const isGuestStr = gameDataEl.getAttribute('data-is-guest');
        const isGuestVal = isGuestStr === 'true';
        
        console.log('🎮 Configuration chargée depuis data attributes:', { gameId, playerNum, isGuestVal });
        initGame(gameId, playerNum, isGuestVal);
    } else {
        console.error('❌ Élément game-data introuvable !');
    }
});


function initGame(gameId, playerNum, guestStatus) {
    currentGameId = gameId;
    currentPlayerNum = playerNum;
    isGuest = guestStatus;
    
    console.log('🎮 Initialisation du jeu:', { gameId, playerNum, guestStatus });
    
    attachCardListeners();
    
    startPolling();

    updateGameState();
}

function attachCardListeners() {
    const cardButtons = document.querySelectorAll('.card-button');
    
    console.log('🃏 Nombre de boutons trouvés:', cardButtons.length);
    
    cardButtons.forEach(function(button, index) {
        const card = button.getAttribute('data-card');
        console.log('➡️ Bouton', index, ':', card);
        
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            if (this.disabled) {
                console.log('⚠️ Bouton désactivé, clic ignoré');
                return;
            }
            
            const cardName = this.getAttribute('data-card');
            console.log('🎯 CARTE CLIQUÉE:', cardName);
            playCard(cardName);
        });
    });
    
    console.log('✅ Listeners attachés avec succès');
}

async function playCard(card) {
    console.log('🚀 Tentative de jouer la carte:', card);
    
    const useJoker = document.getElementById('use-joker').checked;
    
    disableAllButtons();
    
    try {
        const url = '/api/game/' + currentGameId + '/play';
        console.log('📡 Envoi vers:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                card: card,
                use_joker: useJoker
            })
        });
        
        const data = await response.json();
        console.log('📥 Réponse serveur:', data);
        
        if (!response.ok) {
            console.error('❌ Erreur serveur:', data.error);
            alert(data.error || 'Erreur lors du jeu de la carte');
            enableCardButtons();
            return;
        }
        
        document.getElementById('use-joker').checked = false;
        
        showTurnMessage('Carte jouée ! En attente de l\'adversaire...');
        
        setTimeout(function() {
            updateGameState();
        }, 100);
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        alert('Erreur de connexion au serveur');
        enableCardButtons();
    }
}

async function updateGameState() {
    try {
        const response = await fetch('/api/game/' + currentGameId + '/state');
        const gameState = await response.json();
        
        if (!response.ok) {
            console.error('Erreur lors de la récupération de l\'état');
            return;
        }
        
        console.log('📊 État du jeu:', gameState);
        console.log('   ⏳ waiting_for:', gameState.waiting_for);
        console.log('   🎮 currentPlayerNum:', currentPlayerNum);
        
        const previousState = lastGameState;
        lastGameState = gameState;
        
        updateScoreboard(gameState);
        updatePlayArea(gameState, previousState);
        updatePlayerHand(gameState);
        
        if (gameState.status === 'finished') {
            stopPolling();
            showEndGameModal(gameState);
        }
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function updateScoreboard(gameState) {
    const score1El = document.querySelector('#player1-score .score');
    const score2El = document.querySelector('#player2-score .score');
    
    if (score1El) score1El.textContent = gameState.score1;
    if (score2El) score2El.textContent = gameState.score2;
    
    // Statut du Bouffon
    const jokerP1 = document.querySelector('#joker-p1 .joker-available');
    const jokerP2 = document.querySelector('#joker-p2 .joker-available');
    
    if (jokerP1) {
        jokerP1.textContent = gameState.joker_used_p1 ? 'Utilisé' : 'Disponible';
        jokerP1.style.color = gameState.joker_used_p1 ? '#ef4444' : '#10b981';
    }
    
    if (jokerP2) {
        jokerP2.textContent = gameState.joker_used_p2 ? 'Utilisé' : 'Disponible';
        jokerP2.style.color = gameState.joker_used_p2 ? '#ef4444' : '#10b981';
    }
}

function updatePlayArea(gameState, previousState) {
    const lastTurn = gameState.last_turn;
    
    if (!lastTurn) {
        showTurnMessage('Jouez votre première carte !');
        updateCardSlot('card-p1', null, 0);
        updateCardSlot('card-p2', null, 0);
        return;
    }
    
    const p1Id = gameState.player1_id || 0;
    const p2Id = gameState.player2_id || 0;
    
    if (lastTurn.player1_card && lastTurn.player2_card) {
        updateCardSlot('card-p1', lastTurn.player1_card, lastTurn.winner_id === p1Id ? 1 : 0);
        updateCardSlot('card-p2', lastTurn.player2_card, lastTurn.winner_id === p2Id ? 1 : 0);
        
        if (!previousState || !previousState.last_turn ||
            previousState.last_turn.turn_number !== lastTurn.turn_number) {
            showTurnResult(lastTurn, gameState);
        }
        
        if (gameState.waiting_for === 'both') {
            showTurnMessage('Nouveau tour ! Jouez votre carte');
        } else if (gameState.waiting_for === currentPlayerNum) {
            showTurnMessage('À votre tour !');
        } else {
            showTurnMessage('En attente de l\'adversaire...');
        }
    } 
    else {
        if (currentPlayerNum === 1) {
            updateCardSlot('card-p1', lastTurn.player1_card, 0);
            updateCardSlot('card-p2', null, 0);
        } else {
            updateCardSlot('card-p1', null, 0);
            updateCardSlot('card-p2', lastTurn.player2_card, 0);
        }
        
        if (gameState.waiting_for === currentPlayerNum) {
            showTurnMessage('À votre tour !');
        } else {
            showTurnMessage('En attente de l\'adversaire...');
        }
    }
}

function updateCardSlot(slotId, cardName, isWinner) {
    const slot = document.getElementById(slotId);
    if (!slot) return;
    
    if (!cardName) {
        slot.innerHTML = '<div class="card card-back"><div class="card-content">?</div></div>';
        return;
    }
    
    const cardClass = 'card-' + cardName.toLowerCase();
    const winnerClass = isWinner > 0 ? 'card-winner' : '';
    const emoji = getCardEmoji(cardName);
    
    slot.innerHTML = '<div class="card ' + cardClass + ' ' + winnerClass + ' card-flip"><div class="card-image">' + emoji + '</div><div class="card-name">' + cardName + '</div></div>';
}


function getCardEmoji(cardName) {
    const emojis = {
        'Mage': '🔮',
        'Chevalier': '⚔️',
        'Loup': '🐺'
    };
    return emojis[cardName] || '❓';
}


function showTurnResult(lastTurn, gameState) {
    const resultDiv = document.getElementById('turn-result');
    if (!resultDiv) return;
    
    let message = '';
    let color = '';
    
    const p1Id = gameState.player1_id || 0;
    const p2Id = gameState.player2_id || 0;
    
    if (lastTurn.winner_id === null) {
        message = '⚖️ Égalité !';
        color = '#94a3b8';
    } else {
        const winnerName = lastTurn.winner_id === p1Id ? gameState.player1 : gameState.player2;
        message = '🏆 ' + winnerName + ' remporte le tour !';
        
        const youWon = (lastTurn.winner_id === p1Id && currentPlayerNum === 1) ||
                       (lastTurn.winner_id === p2Id && currentPlayerNum === 2);
        color = youWon ? '#10b981' : '#ef4444';
    }
    
    if (lastTurn.joker_used) {
        message += ' 🃏 (Ordre inversé)';
    }
    
    resultDiv.textContent = message;
    resultDiv.style.color = color;
    resultDiv.style.animation = 'slideIn 0.5s ease-out';
}

function updatePlayerHand(gameState) {
    const waiting = gameState.waiting_for;
    
    console.log('⏳ En attente de:', waiting, '| Joueur actuel:', currentPlayerNum);
    console.log('   🎮 Peut jouer:', (waiting === currentPlayerNum || waiting === 'both'));
    
    if (waiting === currentPlayerNum || waiting === 'both') {
        console.log('   ✅ Activation des boutons');
        enableCardButtons();
    } else {
        console.log('   🚫 Désactivation des boutons');
        disableAllButtons();
    }
    
    const jokerCheckbox = document.getElementById('use-joker');
    if (!jokerCheckbox) return;
    
    const jokerUsed = currentPlayerNum === 1 ? gameState.joker_used_p1 : gameState.joker_used_p2;
    
    if (jokerUsed) {
        jokerCheckbox.disabled = true;
        jokerCheckbox.parentElement.style.opacity = '0.5';
    } else {
        jokerCheckbox.disabled = false;
        jokerCheckbox.parentElement.style.opacity = '1';
    }
}


function enableCardButtons() {
    const buttons = document.querySelectorAll('.card-button');
    buttons.forEach(function(btn) {
        btn.disabled = false;
        btn.style.cursor = 'pointer';
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    });
    console.log('✅ Boutons activés (' + buttons.length + ' boutons)');
}

function disableAllButtons() {
    const buttons = document.querySelectorAll('.card-button');
    buttons.forEach(function(btn) {
        btn.disabled = true;
        btn.style.cursor = 'not-allowed';
        btn.style.opacity = '0.6';
        btn.style.pointerEvents = 'none';
    });
    console.log('🚫 Boutons désactivés (' + buttons.length + ' boutons)');
}

function showTurnMessage(message) {
    const statusDiv = document.getElementById('game-status');
    if (statusDiv) {
        statusDiv.textContent = message;
    }
}


function showEndGameModal(gameState) {
    const modal = document.getElementById('end-game-modal');
    const winnerText = document.getElementById('winner-text');
    const finalScore1 = document.getElementById('final-score1');
    const finalScore2 = document.getElementById('final-score2');
    
    if (!modal || !winnerText || !finalScore1 || !finalScore2) return;
    
    const youWon = (gameState.score1 >= 3 && currentPlayerNum === 1) || 
                   (gameState.score2 >= 3 && currentPlayerNum === 2);
    
    winnerText.textContent = youWon ? '🎉 Victoire ! 🎉' : '😢 Défaite';
    winnerText.style.color = youWon ? '#10b981' : '#ef4444';
    
    finalScore1.textContent = gameState.score1;
    finalScore2.textContent = gameState.score2;
    
    modal.style.display = 'flex';
}

function showConversionForm() {
    const form = document.getElementById('conversion-form');
    if (form) {
        form.style.display = 'block';
    }
}

async function convertAccount() {
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    
    if (!username || !password) {
        alert('Veuillez remplir tous les champs');
        return;
    }
    
    try {
        const response = await fetch('/convert-guest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username, password: password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Compte créé avec succès !');
            window.location.href = '/';
        } else {
            alert(data.error || 'Erreur lors de la création du compte');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur de connexion');
    }
}

function startPolling() {
    pollingInterval = setInterval(function() {
        updateGameState();
    }, 2000);
    console.log('🔄 Polling démarré');
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('⏹️ Polling arrêté');
    }
}

window.addEventListener('beforeunload', function() {
    stopPolling();
});
