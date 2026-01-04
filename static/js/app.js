
let socket = null;
let playerId = null;
let currentLobbyId = null;
let lobbyState = 'waiting';
let isDrawing = false;
let lastSendTime = 0;
let currentRoundNum = 0;
let maxRounds = 5;
let timerInterval = null;
let isEraserMode = false;
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
ctx.fillStyle = '#fff';
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.strokeStyle = '#000';
ctx.lineWidth = 8;
ctx.lineCap = 'round';
ctx.lineJoin = 'round';

let lastX = 0;
let lastY = 0;
let hasMoved = false;
let mouseButtonDown = false;

let soundEnabled = true;

const sounds = {
    roundStart: new Howl({
        src: ['https://cdn.freesound.org/previews/341/341695_5858296-lq.mp3'],
        volume: 0.5
    }),
    correctGuess: new Howl({
        src: ['https://cdn.freesound.org/previews/270/270304_5123851-lq.mp3'],
        volume: 0.6
    }),
    roundWin: new Howl({
        src: ['https://cdn.freesound.org/previews/387/387232_1474204-lq.mp3'],
        volume: 0.5
    }),
    gameOver: new Howl({
        src: ['https://cdn.freesound.org/previews/270/270319_5123851-lq.mp3'],
        volume: 0.5
    }),
    timerWarning: new Howl({
        src: ['https://cdn.freesound.org/previews/254/254316_4597545-lq.mp3'],
        volume: 0.3
    }),
    countdown: new Howl({
        src: ['https://cdn.freesound.org/previews/263/263133_2064400-lq.mp3'],
        volume: 0.4
    }),
    error: new Howl({
        src: ['https://cdn.freesound.org/previews/142/142608_1840739-lq.mp3'],
        volume: 0.4
    }),
    click: new Howl({
        src: ['https://cdn.freesound.org/previews/242/242501_4284968-lq.mp3'],
        volume: 0.3
    })
};

const SoundFX = {
    roundStart: () => soundEnabled && sounds.roundStart.play(),
    correctGuess: () => soundEnabled && sounds.correctGuess.play(),
    roundWin: () => soundEnabled && sounds.roundWin.play(),
    gameOver: () => soundEnabled && sounds.gameOver.play(),
    timerWarning: () => soundEnabled && sounds.timerWarning.play(),
    countdown: () => soundEnabled && sounds.countdown.play(),
    error: () => soundEnabled && sounds.error.play(),
    click: () => soundEnabled && sounds.click.play()
};

function toggleSound() {
    soundEnabled = !soundEnabled;
    const btn = document.getElementById('soundToggle');
    if (btn) {
        btn.textContent = soundEnabled ? '🔊' : '🔇';
    }
    if (soundEnabled) SoundFX.click();
}
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && currentLobbyId && lobbyState === 'playing') {
        submitDrawing();
    }
});
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseenter', resumeDrawing);
canvas.addEventListener('mouseleave', pauseDrawing);
canvas.addEventListener('touchstart', handleTouch);
canvas.addEventListener('touchmove', handleTouchMove);
canvas.addEventListener('touchend', stopDrawing);
document.addEventListener('mouseup', () => {
    mouseButtonDown = false;
    isDrawing = false;
});

function startDrawing(e) {
    mouseButtonDown = true;
    isDrawing = true;
    hasMoved = false;
    lastX = e.offsetX;
    lastY = e.offsetY;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
}

function draw(e) {
    if (!isDrawing) return;
    hasMoved = true;

    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);

    lastX = e.offsetX;
    lastY = e.offsetY;
    if (Date.now() - lastSendTime > 150) {
        sendDrawing();
        lastSendTime = Date.now();
    }
}

function pauseDrawing() {
    ctx.beginPath();
}

function resumeDrawing(e) {
    if (mouseButtonDown) {
        isDrawing = true;
        lastX = e.offsetX;
        lastY = e.offsetY;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
    }
}

function stopDrawing(e) {
    if (isDrawing && !hasMoved) {
        ctx.beginPath();
        ctx.arc(lastX, lastY, ctx.lineWidth / 2, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();
        sendDrawing();
    }
    mouseButtonDown = false;
    isDrawing = false;
    ctx.beginPath();
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    startDrawing({
        offsetX: (touch.clientX - rect.left) * scaleX,
        offsetY: (touch.clientY - rect.top) * scaleY
    });
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    draw({
        offsetX: (touch.clientX - rect.left) * scaleX,
        offsetY: (touch.clientY - rect.top) * scaleY
    });
}

function clearCanvas() {
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#000';
    isEraserMode = false;
    updateEraserButton();
}

function toggleEraser() {
    isEraserMode = !isEraserMode;
    if (isEraserMode) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 20;
    } else {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 8;
    }
    updateEraserButton();
}

function updateEraserButton() {
    const btn = document.getElementById('eraserBtn');
    if (btn) {
        btn.textContent = isEraserMode ? 'Pen' : 'Eraser';
        btn.classList.toggle('active', isEraserMode);
    }
}
function connect() {
    socket = io();

    socket.on('connect', () => {
        log('Connected to server', 'success');
        updateStatus(true);
        if (playerId) {
            log('Reconnecting... Please re-authenticate', 'info');
            playerId = null;
            currentLobbyId = null;
            currentRoundNum = 0;
            document.getElementById('wordDisplay').style.display = 'none';
            document.getElementById('roundDisplay').style.display = 'none';
            document.getElementById('playersList').innerHTML = '';
            updateButtons();
        }
    });

    socket.on('disconnect', () => {
        log('Disconnected from server', 'error');
        updateStatus(false);
        updateButtons();
    });

    socket.on('connected', (data) => {
        log('Server: ' + data.message, 'info');
    });

    socket.on('authenticated', (data) => {
        playerId = data.player_id;
        log(`Authenticated as ${data.username} (${data.player_id.slice(0, 8)})`, 'success');
        updateButtons();
    });
    socket.on('lobby_created', (data) => {
        currentLobbyId = data.lobby_id;
        document.getElementById('currentGameId').textContent = data.lobby_id.slice(0, 8) + '...';
        log(`Lobby created: ${data.lobby_id.slice(0, 8)}`, 'success');
        updateButtons();
        updateLobbyState(data.lobby);
    });
    socket.on('game_created', (data) => {
        currentLobbyId = data.lobby_id || data.game_id;
        document.getElementById('currentGameId').textContent = currentLobbyId.slice(0, 8) + '...';
        log(`Lobby created: ${currentLobbyId.slice(0, 8)}`, 'success');
        updateButtons();
        updateLobbyState(data.lobby || data.game);
    });

    socket.on('player_joined', (data) => {
        log(`${data.username} joined the lobby`, 'info');
        updateLobbyState(data.lobby || data.game);
    });

    socket.on('joined_lobby', (data) => {
        currentLobbyId = data.lobby_id;
        document.getElementById('currentGameId').textContent = data.lobby_id.slice(0, 8) + '...';
        log(`Joined lobby: ${data.lobby_id.slice(0, 8)}`, 'success');
        updateButtons();
        updateLobbyState(data.lobby);
    });

    socket.on('player_left', (data) => {
        log(`${data.username} left the lobby`, 'info');
        if (data.lobby) updateLobbyState(data.lobby);
        if (data.game) updateLobbyState(data.game);
    });

    socket.on('left_lobby', (data) => {
        currentLobbyId = null;
        document.getElementById('wordDisplay').style.display = 'none';
        log('Left the lobby', 'info');
        updateButtons();
    });

    socket.on('left_game', (data) => {
        currentLobbyId = null;
        document.getElementById('wordDisplay').style.display = 'none';
        log('Left the lobby', 'info');
        updateButtons();
    });

    socket.on('player_ready_update', (data) => {
        log(`${data.username} is ready!`, 'info');
        updateLobbyState(data.lobby || data.game);
    });

    socket.on('player_ready_for_next', (data) => {
        log(`${data.username} is ready for next game! 🔄`, 'info');
        updateLobbyState(data.lobby);
    });

    socket.on('lobby_settings_updated', (data) => {
        log('Lobby settings updated', 'info');
        updateLobbyState(data.lobby);
    });

    socket.on('game_starting', (data) => {
        log(`Game starting in ${data.countdown} seconds!`, 'success');
        lobbyState = 'starting';
        document.getElementById('gameOverOverlay').style.display = 'none';
        updateButtons();
        showCountdownOverlay(data.countdown);
    });

    socket.on('round_start', (data) => {
        currentRoundNum = data.round_number || (currentRoundNum + 1);
        lobbyState = 'playing';
        log(`Round ${currentRoundNum} started! Word: ${data.word}`, 'success');
        document.getElementById('wordDisplay').textContent = `Draw: ${data.word.toUpperCase()}`;
        document.getElementById('wordDisplay').style.display = 'block';
        document.getElementById('roundDisplay').style.display = 'block';
        document.getElementById('currentRound').textContent = currentRoundNum;
        document.getElementById('gameState').textContent = 'playing';
        clearCanvas();
        startTimer(data.duration);
        updateButtons();
        SoundFX.roundStart();
    });

    socket.on('ai_prediction', (data) => {
        displayPredictions(data.predictions, data.is_correct);
        if (data.is_correct) {
            log('AI guessed correctly!', 'success');
            SoundFX.correctGuess();
        }
    });

    socket.on('round_end', (data) => {
        if (data.winner_id) {
            log(`Round ${currentRoundNum} ended! Winner: ${data.winner_username || data.winner_id.slice(0, 8)}`, 'success');
            showWinnerAnnouncement(data.winner_username || 'Unknown');
            SoundFX.roundWin();
        } else {
            log(`Round ${currentRoundNum} ended - timeout!`, 'info');
        }
        document.getElementById('timer').textContent = '';
        document.getElementById('gameState').textContent = 'round_end';

        if (data.scores) {
            updateScoresFromData(data.scores);
        }
    });

    socket.on('submission_result', (data) => {
        displayPredictions(data.predictions, data.is_correct);
        if (data.is_correct) {
            log('Your drawing was recognized!', 'success');
            SoundFX.correctGuess();
        } else {
            log('AI did not recognize it - try again!', 'info');
        }
    });

    socket.on('game_end', (data) => {
        log(`Game ended! Winner: ${data.winner_username || 'N/A'}`, 'success');
        document.getElementById('wordDisplay').style.display = 'none';
        document.getElementById('roundDisplay').style.display = 'none';
        document.getElementById('timer').textContent = '';
        document.getElementById('gameState').textContent = 'game_over';
        currentRoundNum = 0;
        lobbyState = 'game_over';

        showGameOverScreen(data.winner_username, data.final_scores);
        updateButtons();
        SoundFX.gameOver();

        if (data.lobby) {
            updateLobbyState(data.lobby);
        }
    });

    socket.on('error', (data) => {
        log(`Error: ${data.message} (${data.code})`, 'error');
        SoundFX.error();
    });

    socket.on('available_lobbies', (data) => {
        log(`Available lobbies: ${data.lobbies.length}`, 'info');
        if (data.lobbies.length > 0) {
            document.getElementById('gameIdInput').value = data.lobbies[0].id;
        }
    });

    socket.on('available_games', (data) => {
        log(`Available lobbies: ${data.games.length}`, 'info');
        if (data.games.length > 0) {
            document.getElementById('gameIdInput').value = data.games[0].id;
        }
    });
}
function authenticate() {
    const username = document.getElementById('username').value || 'TestPlayer';
    socket.emit('authenticate', { username });
}

function createGame() {
    socket.emit('create_lobby', {});
}

function joinGame() {
    const lobbyId = document.getElementById('gameIdInput').value;
    if (lobbyId) {
        socket.emit('join_lobby', { lobby_id: lobbyId });
        log('Joining lobby...', 'info');
    }
}

function setReady() {
    socket.emit('player_ready', {});
}

function handleReadyClick() {
    if (lobbyState === 'game_over') {
        socket.emit('play_again', {});
        log('Ready for next game...', 'info');
    } else {
        socket.emit('player_ready', {});
    }
}

function leaveGame() {
    socket.emit('leave_lobby', {});
}

function setMaxRounds() {
    const input = document.getElementById('roundsInput');
    const value = input.value ? parseInt(input.value) : null;
    socket.emit('set_max_rounds', { max_rounds: value });
    log(`Rounds set to ${value || 'default'}`, 'info');
}

function setDefaultRounds() {
    const input = document.getElementById('roundsInput');
    const playerCount = document.querySelectorAll('#playersList .player').length || 2;
    const defaultRounds = 5 + (playerCount - 1) * 3;
    input.value = defaultRounds;
    socket.emit('set_max_rounds', { max_rounds: defaultRounds });
    log(`Rounds set to default (${defaultRounds})`, 'info');
}

function copyGameId() {
    if (currentLobbyId) {
        navigator.clipboard.writeText(currentLobbyId).then(() => {
            log('Lobby ID copied to clipboard!', 'success');
        }).catch(() => {
            const textArea = document.createElement('textarea');
            textArea.value = currentLobbyId;
            document.body.appendChild(textArea);
            textArea.select();
            document.body.removeChild(textArea);
            log('Lobby ID copied to clipboard!', 'success');
        });
    }
}

function sendDrawing() {
    if (!socket || !currentLobbyId) return;
    const canvasData = canvas.toDataURL('image/png');
    socket.emit('draw_update', { canvas_data: canvasData });
}

function submitDrawing() {
    if (!socket || !currentLobbyId) return;
    const canvasData = canvas.toDataURL('image/png');
    socket.emit('submit_drawing', { canvas_data: canvasData });
    log('Submitting drawing...', 'info');
}

function getAvailableGames() {
    socket.emit('get_available_lobbies', {});
}

function showCountdownOverlay(seconds) {
    const overlay = document.getElementById('countdownOverlay');
    const numberEl = document.getElementById('countdownNumber');
    
    overlay.style.display = 'flex';
    let remaining = seconds;
    
    function updateNumber() {
        numberEl.textContent = remaining;
        numberEl.style.animation = 'none';
        numberEl.style.animation = 'countdownPop 1s ease-out';
        
        SoundFX.countdown();
        
        remaining--;
        
        if (remaining >= 0) {
            setTimeout(updateNumber, 1000);
        } else {
            overlay.style.display = 'none';
        }
    }
    
    updateNumber();
}

function showWinnerAnnouncement(winnerName) {
    document.getElementById('winnerName').textContent = winnerName;
    document.getElementById('winnerOverlay').style.display = 'flex';
    setTimeout(() => {
        document.getElementById('winnerOverlay').style.display = 'none';
    }, 3000);
}

function updateScoresFromData(scores) {
    const list = document.getElementById('playersList');
    let html = '';
    for (const [pid, data] of Object.entries(scores)) {
        html += `
            <div class="player">
                <span>${data.username} <span class="score">${data.score} pts</span></span>
            </div>
        `;
    }
    list.innerHTML = html;
}

function showGameOverScreen(winnerName, finalScores) {
    document.getElementById('gameWinnerName').textContent = `${winnerName || 'No Winner'}`;

    let scoresHtml = '<h3 style="margin-bottom: 10px;">Final Scores:</h3>';
    if (finalScores) {
        const sorted = Object.entries(finalScores).sort((a, b) => b[1].score - a[1].score);
        scoresHtml += sorted.map(([pid, data], i) => `
            <div style="padding: 8px; background: rgba(255,255,255,0.1); border-radius: 6px; margin: 5px 0;">
                ${i === 0 ? '👑' : ''} ${data.username}: <strong>${data.score} pts</strong>
            </div>
        `).join('');
    }
    document.getElementById('finalScores').innerHTML = scoresHtml;
    document.getElementById('gameOverOverlay').style.display = 'flex';
}

function closeGameOver() {
    document.getElementById('gameOverOverlay').style.display = 'none';
}

function playAgain() {
    socket.emit('play_again', {});
    log('Ready for next game...', 'info');
}

function resetForNewGame() {
    currentLobbyId = null;
    currentRoundNum = 0;
    lobbyState = 'waiting';
    document.getElementById('playersList').innerHTML = '';
    document.getElementById('predictions').innerHTML = '';
    document.getElementById('wordDisplay').style.display = 'none';
    document.getElementById('roundDisplay').style.display = 'none';
    clearCanvas();
    updateButtons();
}

function updateStatus(connected) {
    const el = document.getElementById('connectionStatus');
    el.className = 'status ' + (connected ? 'connected' : 'disconnected');
    el.textContent = connected ? 'Connected' : 'Disconnected';
}

function updateButtons() {
    const authenticated = !!playerId;
    const inLobby = !!currentLobbyId;

    document.getElementById('authBtn').disabled = authenticated;
    document.getElementById('createBtn').disabled = !authenticated || inLobby;
    document.getElementById('joinBtn').disabled = !authenticated || inLobby;
    document.getElementById('lobbyControls').style.display = inLobby ? 'none' : 'block';
    document.getElementById('gameControls').style.display = inLobby ? 'block' : 'none';
    const readyBtn = document.getElementById('readyBtn');
    if (lobbyState === 'game_over') {
        readyBtn.textContent = 'Play Again';
        readyBtn.style.background = 'linear-gradient(90deg, #ffd700, #ff6b00)';
        readyBtn.style.display = 'block';
    } else if (lobbyState === 'in_game' || lobbyState === 'playing') {
        readyBtn.style.display = 'none';
    } else {
        readyBtn.textContent = '✓ Ready!';
        readyBtn.style.background = '';
        readyBtn.style.display = 'block';
    }
}

function updateLobbyState(lobby) {
    if (!lobby) return;

    const state = lobby.state;
    lobbyState = state;
    document.getElementById('gameState').textContent = state;

    if (lobby.current_game) {
        const game = lobby.current_game;
        maxRounds = game.max_rounds || 5;
        document.getElementById('maxRounds').textContent = maxRounds;
        document.getElementById('currentRound').textContent = game.rounds_played || 0;
    } else {
        document.getElementById('currentRound').textContent = '0';
        document.getElementById('maxRounds').textContent = '5';
    }

    const roundsInput = document.getElementById('roundsInput');
    const defaultRounds = lobby.default_rounds || (5 + (lobby.player_count - 2) * 3);
    if (roundsInput) {
        roundsInput.value = lobby.max_rounds || defaultRounds;
    }

    const effectiveRounds = lobby.max_rounds || defaultRounds;
    document.getElementById('maxRounds').textContent = effectiveRounds;
    maxRounds = effectiveRounds;

    const list = document.getElementById('playersList');
    const isGameOver = state === 'game_over';

    list.innerHTML = lobby.players.map(p => {
        let statusHtml;
        if (isGameOver) {
            if (p.ready_for_next) {
                statusHtml = '<span class="ready"> Ready</span>';
            } else {
                statusHtml = '<span class="not-ready">Waiting...</span>';
            }
        } else {
            statusHtml = `<span class="${p.is_ready ? 'ready' : 'not-ready'}">${p.is_ready ? '✓ Ready' : 'Waiting'}</span>`;
        }

        const gamesWonHtml = p.games_won > 0 ? `<span style="color: gold; margin-left: 5px;">🏆${p.games_won}</span>` : '';

        return `
            <div class="player">
                <span>${p.username}${gamesWonHtml} <span class="score">${p.score || 0} pts</span></span>
                ${statusHtml}
            </div>
        `;
    }).join('');

    updateButtons();
}

function updateGameState(game) {
    updateLobbyState(game);
}

function displayPredictions(predictions, isCorrect) {
    const container = document.getElementById('predictions');
    container.innerHTML = predictions.map((p, i) => `
        <div class="prediction ${i === 0 && isCorrect ? 'match' : ''}">
            <span>${p.label}</span>
            <span>${(p.confidence * 100).toFixed(1)}%</span>
        </div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: ${p.confidence * 100}%"></div>
        </div>
    `).join('');
}

function log(message, type = '') {
    const logEl = document.getElementById('log');
    const time = new Date().toLocaleTimeString();
    logEl.innerHTML = `<div class="log-entry ${type}">[${time}] ${message}</div>` + logEl.innerHTML;
}

function startTimer(duration) {
    let remaining = duration;
    const timerEl = document.getElementById('timer');

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        timerEl.textContent = `⏱️ ${remaining}s`;
        if (remaining <= 10 && remaining > 0) {
            SoundFX.timerWarning();
            timerEl.style.color = remaining <= 5 ? '#ff6b6b' : '#ffd43b';
        }
        remaining--;
        if (remaining < 0) {
            clearInterval(timerInterval);
            timerEl.textContent = "Time's up!";
            timerEl.style.color = '#ffd43b';
        }
    }, 1000);
}

connect();
