
let socket = null;
let playerId = null;
let currentLobbyId = null;
let lobbyState = 'waiting';
let isDrawing = false;
let lastSendTime = 0;
let currentRoundNum = 0;
let timerInterval = null;
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
ctx.fillStyle = '#fff';
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.strokeStyle = '#000';
ctx.lineWidth = 4;
ctx.lineCap = 'round';
ctx.lineJoin = 'round';

let lastX = 0;
let lastY = 0;
let mouseButtonDown = false;
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
    lastX = e.offsetX;
    lastY = e.offsetY;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
}

function draw(e) {
    if (!isDrawing) return;

    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();

    lastX = e.offsetX;
    lastY = e.offsetY;
    if (Date.now() - lastSendTime > 150) {
        sendDrawing();
        lastSendTime = Date.now();
    }
}

function pauseDrawing() { ctx.beginPath(); }

function resumeDrawing(e) {
    if (mouseButtonDown) {
        isDrawing = true;
        lastX = e.offsetX;
        lastY = e.offsetY;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
    }
}

function stopDrawing() {
    isDrawing = false;
    mouseButtonDown = false;
    ctx.beginPath();
    sendDrawing();
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    startDrawing({
        offsetX: (touch.clientX - rect.left) * (canvas.width / rect.width),
        offsetY: (touch.clientY - rect.top) * (canvas.height / rect.height)
    });
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    draw({
        offsetX: (touch.clientX - rect.left) * (canvas.width / rect.width),
        offsetY: (touch.clientY - rect.top) * (canvas.height / rect.height)
    });
}

function clearCanvas() {
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function connect() {
    socket = io();

    socket.on('connect', () => {
        updateStatus(true);
        if (playerId) {
            console.log('Reconnecting...');
            resetForNewGame();
        }
    });

    socket.on('disconnect', () => updateStatus(false));

    socket.on('authenticated', (data) => {
        playerId = data.player_id;
        updateButtons();
    });
    const handleLobbyUpdate = (data) => {
        if (data.lobby_id) {
            currentLobbyId = data.lobby_id;
            document.getElementById('currentGameId').textContent = data.lobby_id.slice(0, 8);
        }
        updateLobbyState(data.lobby || data.game);
        updateButtons();
    };

    socket.on('lobby_created', handleLobbyUpdate);
    socket.on('joined_lobby', handleLobbyUpdate);

    socket.on('player_joined', (data) => {
        updateLobbyState(data.lobby);
    });

    socket.on('player_left', (data) => {
        if (data.lobby) updateLobbyState(data.lobby);
    });

    socket.on('left_lobby', () => {
        resetForNewGame();
    });

    socket.on('player_ready_update', (data) => {
        updateLobbyState(data.lobby);
    });

    socket.on('game_starting', (data) => {
        lobbyState = 'starting';
        document.getElementById('gameOverOverlay').style.display = 'none';
        updateButtons();
    });

    socket.on('round_start', (data) => {
        currentRoundNum = data.round_number;
        lobbyState = 'playing';

        const wordDisplay = document.getElementById('wordDisplay');
        wordDisplay.textContent = `Draw: ${data.word}`;
        wordDisplay.style.display = 'block';

        document.getElementById('roundDisplay').style.display = 'block';
        document.getElementById('currentRound').textContent = currentRoundNum;
        document.getElementById('gameState').textContent = 'playing';

        clearCanvas();
        startTimer(data.duration);
        updateButtons();
    });

    socket.on('round_end', (data) => {
        if (timerInterval) clearInterval(timerInterval);
        document.getElementById('timer').textContent = '';

        if (data.winner_username) {
            showWinnerAnnouncement(data.winner_username);
        }

        document.getElementById('gameState').textContent = 'interval';
        if (data.scores) updateScores(data.scores); 
    });

    socket.on('game_end', (data) => {
        if (timerInterval) clearInterval(timerInterval);
        document.getElementById('wordDisplay').style.display = 'none';

        lobbyState = 'game_over';
        showGameOverScreen(data.winner_username, data.final_scores);
        updateButtons();

        if (data.lobby) updateLobbyState(data.lobby);
    });

    socket.on('error', (data) => alert(`Error: ${data.message}`));
}

function authenticate() {
    const username = document.getElementById('username').value || 'Guest';
    socket.emit('authenticate', { username });
}

function createGame() {
    socket.emit('create_lobby', {});
}

function joinGame() {
    const lobbyId = document.getElementById('gameIdInput').value;
    if (lobbyId) socket.emit('join_lobby', { lobby_id: lobbyId });
}

function handleReadyClick() {
    if (lobbyState === 'game_over') {
        socket.emit('play_again', {});
    } else {
        socket.emit('player_ready', {});
    }
}

function leaveGame() {
    socket.emit('leave_lobby', {});
}

function copyGameId() {
    if (currentLobbyId) {
        navigator.clipboard.writeText(currentLobbyId);
        alert('Copied ID');
    }
}

function sendDrawing() {
    if (!socket || !currentLobbyId) return;
    socket.emit('draw_update', { canvas_data: canvas.toDataURL() });
}

function submitDrawing() {
    if (!socket || !currentLobbyId) return;
    socket.emit('submit_drawing', { canvas_data: canvas.toDataURL() });
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
        readyBtn.style.display = 'block';
    } else if (lobbyState === 'playing' || lobbyState === 'starting') {
        readyBtn.style.display = 'none';
    } else {
        readyBtn.textContent = 'Ready!';
        readyBtn.style.display = 'block';
    }
}

function updateLobbyState(lobby) {
    if (!lobby) return;

    lobbyState = lobby.state;
    document.getElementById('gameState').textContent = lobbyState;

    const list = document.getElementById('playersList');
    list.innerHTML = lobby.players.map(p => `
        <div class="player">
            <span>${p.username} (${p.score || 0} pts)</span>
            <span>${p.is_ready ? '✓' : '...'}</span>
        </div>
    `).join('');
}

function updateScores(scores) {
 
}

function showWinnerAnnouncement(name) {
    document.getElementById('winnerName').textContent = name;
    const el = document.getElementById('winnerOverlay');
    el.style.display = 'flex';
    setTimeout(() => { el.style.display = 'none'; }, 2000);
}

function showGameOverScreen(winner, scores) {
    document.getElementById('gameWinnerName').textContent = winner || 'None';

    let html = '';
    if (scores) {
        html = Object.values(scores)
            .sort((a, b) => b.score - a.score)
            .map(p => `<div>${p.username}: ${p.score}</div>`)
            .join('');
    }
    document.getElementById('finalScores').innerHTML = html;
    document.getElementById('gameOverOverlay').style.display = 'flex';
}

function closeGameOver() {
    document.getElementById('gameOverOverlay').style.display = 'none';
}

function startTimer(duration) {
    let remaining = duration;
    const timerEl = document.getElementById('timer');
    timerEl.textContent = remaining;

    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        remaining--;
        timerEl.textContent = remaining;
        if (remaining <= 0) clearInterval(timerInterval);
    }, 1000);
}

function resetForNewGame() {
    currentLobbyId = null;
    lobbyState = 'waiting';
    document.getElementById('playersList').innerHTML = '';
    document.getElementById('wordDisplay').style.display = 'none';
    document.getElementById('roundDisplay').style.display = 'none';
    clearCanvas();
    updateButtons();
}
connect();
