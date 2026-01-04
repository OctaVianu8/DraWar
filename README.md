# DraWar - AI Drawing Battle

> DraWar is a multiplayer drawing game where players compete to have their drawings recognized by an AI. Players join lobbies, receive a random word to draw, and race to create a drawing that the AI model can correctly identify. The game uses real-time WebSocket communication, features multiple rounds per game, and includes a custom-trained neural network for image recognition. The first player whose drawing is correctly guessed by the AI wins the round.

**GitHub:** https://github.com/OctaVianu8/DraWar

---

## Limbaje și Tehnologii

### Limbaje
- **Python** - Backend server, AI model training, image processing
- **JavaScript** - Frontend logic, WebSocket client, canvas drawing
- **HTML/CSS** - User interface, responsive design

### Framework-uri și Librării
- **Flask** - Web server
- **Flask-SocketIO** - WebSocket communication
- **Eventlet** - Async I/O pentru conexiuni simultane
- **PyTorch** - CNN model training și inference
- **FastAPI** - AI inference server
- **Pillow/NumPy** - Image preprocessing
- **Socket.IO** (client) - Real-time communication
- **Howler.js** - Sound effects

### Servicii Cloud
- **Render** - Backend hosting
- **Hugging Face Spaces** - AI model hosting

---

## Despre Proiect

**DraWar** este o aplicație web multiplayer în care jucătorii concurează pentru a desena obiecte cât mai rapid. Un model AI antrenat pe datasetul Google QuickDraw analizează desenele în timp real - primul jucător al cărui desen este recunoscut corect câștigă runda.

### Caracteristici

- Multiplayer real-time - până la 10 jucători simultan
- AI CNN - recunoaștere a 45+ categorii de obiecte
- Timer 30 secunde per rundă
- Funcționează pe desktop și mobil
- Efecte sonore
- Deploy separat pentru scalabilitate (Render + Hugging Face)

---

## Instalare și Rulare

### Cerințe

- Linux / macOS
- Bash
- ngrok (pentru acces extern)

### Instalare

```bash
./install-req.sh
```

### Rulare

```bash
./start-app.sh
```

Deschide browserul la **http://localhost:5003**

### Expunere cu ngrok

```bash
ngrok http 5003
```

---

## Arhitectură

```
Browser (HTML/CSS/JS + Socket.IO)
        |
        | WebSocket
        v
Backend (Flask + SocketIO) - Render.com
        |
        | HTTP POST /predict
        v
AI Service (FastAPI + PyTorch CNN) - Hugging Face Spaces
```

---

## Cum se joacă

1. Introdu un username
2. Creează un joc nou sau intră cu un Game ID
3. Apasă Ready
4. Desenează cuvântul afișat în 30 secunde
5. Primul recunoscut de AI câștigă runda
6. Repetă până se termină rundele

---

## Tehnologii

| Component | Tehnologie |
|-----------|------------|
| Frontend | HTML, CSS, JavaScript, Canvas API, Socket.IO |
| Backend | Python, Flask, Flask-SocketIO, Eventlet |
| AI | PyTorch, FastAPI, CNN (QuickDraw dataset) |
| Deploy | Render (Backend), Hugging Face Spaces (AI) |

---

## Structura Proiectului

```
DraWar/
├── app.py                 # Entry point
├── backend/
│   ├── server.py          # Flask + SocketIO
│   ├── config.py          # Config
│   ├── models/            # Game, Player, Round, Lobby
│   ├── services/          # GameManager, AI, etc.
│   └── handlers/          # WebSocket handlers
├── ai_server/
│   ├── app.py             # FastAPI server
│   ├── model/             # Trained model
│   └── training/          # Training scripts
├── static/
│   ├── css/styles.css
│   └── js/app.js
├── templates/
│   └── index.html
└── requirements.txt
```

---

## Echipa

### Stănescu Matei-Octavian

**Contribuții:**
- Implementarea claselor de bază (Game, Player, Round, Lobby)
- Configurarea serverului Flask și a comunicării WebSocket
- Antrenarea modelului CNN pentru recunoașterea desenelor
- Integrarea serviciului AI cu backend-ul principal
- Sistem de efecte sonore și feedback vizual

**Dificultăți întâmpinate:**
- Odată ce am introdus WebSocket-uri am început să avem race conditions și jocul fie se bloca, fie era într-o stare la mine și altă stare la coechipieri. **Rezolvare:** Crearea unei unici surse de adevăr în server cu verificări la fiecare pas.
- Am încercat să folosesc State Machine Design Pattern, dar m-am lovit de bug-uri precum Player în Lobby dar nu în Game. **Rezolvare:** Multe print-uri cu starea curentă pentru debugging.
- Inițial am vrut să integrăm Gemini API pentru recunoașterea desenelor, dar am realizat că nu e fezabil - aveam nevoie de output aproape instant. **Rezolvare:** Am folosit un model local CNN antrenat pe datasetul Google QuickDraw.
- La integrarea AI-ului cu backend-ul, am avut probleme cu formatul datelor: canvas-ul trimitea imagini PNG base64 de 400x400 color, dar modelul CNN aștepta array-uri NumPy de 28x28 grayscale normalizate. **Rezolvare:** Pipeline de preprocesare în `image_processor.py`.

---

### Crețoiu Teodora-Elena

**Contribuții:**
- Dezvoltarea interfeței utilizator (HTML/CSS)
- Implementarea canvas-ului interactiv pentru desenare
- Logica client-side în JavaScript (comunicare WebSocket, events)
- Testarea și debugging-ul aplicației

**Dificultăți întâmpinate:**
- Numeroase modificări CSS pentru experiență bună pe desktop și mobil - mult trial and error pentru layout stabil.
- Canvas responsive dificil din cauza diferențelor dintre coordonatele mouse și touch. Pe mobil apărea scroll în timpul desenului.
- Variabilele globale (lobbyState, isDrawing) îngreunau debugging-ul. Resetarea stării la finalul jocului necesita atenție.
- Sincronizarea scorurilor, listei de jucători și timerelor în timp real - evenimentele rapide duceau la inconsistențe vizuale.
- Race conditions când mai mulți jucători trimiteau desene simultan.
- Gestionarea tranzițiilor și timerelor - trebuiau anulate corect pentru a evita declanșarea multiplă.

---

### Nițu Eriko-Laurențiu

**Contribuții:**
- Preprocesarea datelor din datasetul QuickDraw
- Implementarea AI inference server cu FastAPI
- Optimizarea modelului și deploy pe Hugging Face Spaces
- Integrarea componentelor și deploy pe Render

**Dificultăți întâmpinate:**
- Inițial am încercat să rulăm modelul AI direct în Flask, dar încărcarea PyTorch bloca serverul la startup și încetinea WebSocket. **Rezolvare:** Am separat AI-ul într-un microserviciu cu FastAPI, comunicând prin HTTP POST cu array JSON de 784 valori float.
- Serverul AI adoarme când nu e folosit, prima cerere dădea eroare. **Rezolvare:** Am crescut timeout-ul la 15 secunde.
- PyTorch e imens și îngreuna serverul. **Rezolvare:** Versiunea CPU-only, mult mai mică.
- Planurile gratuite nu au destul RAM pentru joc + AI în același loc. **Rezolvare:** Am separat proiectul - Backend pe Render, AI pe Hugging Face.
- Ecranele Winner/Countdown se suprapuneau greșit pe iPhone. **Rezolvare:** z-index maxim.

---

## Context

Proiect pentru **Informatică Aplicată 4**  
Facultatea de Automatică și Calculatoare  
Universitatea Politehnica București - 2025