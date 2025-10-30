# 📚 Modalità Studio

![Python](https://img.shields.ioshields.io/badge/license-/badge/platform-Linux-lightapplicazione desktop per bloccare app e webapp distraenti durante le sessioni di studio o lavoro. Sviluppata con Python e design Material 3.

![Screenshot](assets ✨ Caratteristiche

- 🎯 **Blocco app native** - Termina automaticamente processi di applicazioni specifiche
- 🌐 **Blocco webapp** - Blocca webapp browser (Chrome, Firefox, ecc.) tramite URL o ID
- 🎨 **Design Material 3** - Interfaccia moderna e pulita con Material Design
- 🔄 **Toggle on/off** - Attiva/disattiva il blocco senza chiudere l'app
- 💾 **Persistenza dati** - Salva automaticamente la lista di app/webapp bloccate
- 🖱️ **System tray** - Icona nella barra di sistema con menu rapido
- ⚡ **Leggero** - Consuma risorse minime in background
- 🐧 **Linux native** - Ottimizzato per KDE Plasma e altre DE Linux

***

## 📋 Prerequisiti

- **Python 3.9+**
- **Linux** (testato su Arch Linux con KDE Plasma)
- **pip** o **pip3**

***

## 🚀 Installazione

### 1. Clona il repository

```bash
git clone https://github.com/tuousername/Mode_Study.git
cd Mode_Study
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

Oppure manualmente:

```bash
pip install ttkbootstrap psutil pystray pillow
```

### 3. Avvia l'applicazione

```bash
python main.py
```

O rendi il file eseguibile:

```bash
chmod +x main.py
./main.py
```

***

## 📖 Guida Utilizzo

### Prima configurazione

1. **Avvia l'applicazione**
   ```bash
   python main.py
   ```

2. **Aggiungi app/webapp da bloccare**
   - Seleziona il tipo: **📱 App Nativa** o **🌐 Webapp**
   - Inserisci il nome (es: `firefox`, `telegram`) o URL (es: `web.whatsapp.com`)
   - Clicca **➕ Aggiungi**

3. **Attiva la modalità blocco**
   - Clicca sul grande bottone verde **"▶️ ATTIVA MODALITÀ STUDIO"**
   - Il bottone diventerà rosso: **"⏸️ DISATTIVA MODALITÀ STUDIO"**

4. **Verifica il blocco**
   - Prova ad aprire un'app bloccata
   - Dovrebbe chiudersi automaticamente entro 2 secondi

### Esempi di utilizzo

#### Bloccare app native

Per bloccare Firefox:
- Tipo: **📱 App Nativa**
- Nome: `firefox`

Per bloccare Telegram:
- Tipo: **📱 App Nativa**
- Nome: `telegram`

#### Bloccare webapp

Per bloccare WhatsApp Web:
- Tipo: **🌐 Webapp**
- URL: `web.whatsapp.com`

Per bloccare webapp Instagram:
- Tipo: **🌐 Webapp**
- URL: `instagram.com`

### System Tray

L'app crea un'icona nella system tray con queste opzioni:

- **▶️ Avvia Blocco** / **⏸️ Ferma Blocco** - Toggle rapido
- **👁️ Mostra GUI** - Apre la finestra principale
- **🚪 Esci** - Chiude l'applicazione

### Comandi da tastiera

- Quando la finestra è aperta, premere **X** la nasconde (non la chiude)
- Per chiudere definitivamente, usa **🚪 Esci** dalla GUI o dal tray menu

***

## ⚙️ Configurazione Avanzata

### File di configurazione

Modifica `config.py` per personalizzare:

```python
# Intervallo di controllo processi (secondi)
BLOCKING_INTERVAL = 2

# Stato iniziale del blocco all'avvio
BLOCKING_ACTIVE_ON_STARTUP = False  # True per attivare di default

# Dimensioni finestra
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 620

# Tema GUI (opzioni: flatly, cosmo, darkly, cyborg, ecc.)
GUI_THEME = "flatly"
```

### File dati

La lista delle app/webapp bloccate è salvata in:

```
data/blocked_apps.json
```

Formato:

```json
[
    {
        "name": "firefox",
        "type": "app"
    },
    {
        "name": "web.whatsapp.com",
        "type": "webapp"
    }
]
```

***

## 🏗️ Struttura Progetto

```
Mode_Study/
├── main.py                      # Entry point
├── config.py                    # Configurazioni globali
├── requirements.txt             # Dipendenze Python
├── README.md                    # Questo file
│
├── data/
│   └── blocked_apps.json        # Dati salvati
│
├── core/
│   ├── __init__.py
│   ├── blocker.py               # Logica blocco processi
│   └── storage.py               # Gestione dati JSON
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py           # Finestra principale
│   └── material_theme.py        # Stili Material 3
│
├── utils/
│   ├── __init__.py
│   └── tray_icon.py             # System tray icon
│
└── assets/
    └── screenshot.png           # Screenshot app
```

***

## 🐛 Troubleshooting

### L'app non killa i processi

**Problema:** Hai attivato la modalità blocco?

**Soluzione:**
1. Clicca il bottone **"▶️ ATTIVA MODALITÀ STUDIO"**
2. Verifica che diventi rosso con scritto **"⏸️ DISATTIVA"**

Oppure attiva di default modificando `config.py`:
```python
BLOCKING_ACTIVE_ON_STARTUP = True
```

### Nome app non funziona

**Problema:** Il nome inserito non corrisponde al processo.

**Soluzione:** Verifica il nome esatto del processo:

```bash
ps aux | grep nome_app
```

Usa il nome della colonna `COMMAND` (es: per Firefox usa `firefox`, non `Firefox`).

### Webapp non viene bloccata

**Problema:** La stringa URL non è presente nella command line.

**Soluzione:** Verifica la command line del processo:

```bash
ps aux | grep chrome
```

Usa una parte dell'URL che compare (es: `whatsapp.com` invece di `https://web.whatsapp.com/`).

### Errore "ModuleNotFoundError"

**Problema:** Dipendenze non installate.

**Soluzione:**

```bash
pip install -r requirements.txt
```

### System tray non appare (Wayland)

**Problema:** Alcune DE su Wayland hanno limitazioni.

**Soluzione:** Usa l'app dalla finestra principale o passa a X11.

***

## 🔧 Sviluppo

### Setup ambiente sviluppo

```bash
# Clona repo
git clone https://github.com/tuousername/Mode_Study.git
cd Mode_Study

# Crea virtual environment (opzionale)
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt
```

### Test

```bash
# Test manuale
python main.py

# Verifica stato blocco
python -c "from core.blocker import is_blocking_active; print(is_blocking_active())"
```

### Contribuire

1. Fork il progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

***

## 📝 TODO / Roadmap

- [ ] **Scheduler** - Attiva/disattiva automaticamente in orari specifici
- [ ] **Statistiche** - Traccia tempo studio e app bloccate
- [ ] **Whitelist** - Lista di app sempre consentite
- [ ] **Notifiche** - Alert quando un'app viene bloccata
- [ ] **Modalità Focus** - Blocco temporaneo con timer (es: Pomodoro)
- [ ] **Profili** - Diversi set di app per scenari diversi (studio, lavoro, relax)
- [ ] **Autostart** - Avvio automatico con il sistema
- [ ] **Password protection** - Richiede password per disattivare il blocco
- [ ] **CLI** - Interfaccia command line per controllo remoto
- [ ] **Cross-platform** - Supporto Windows e macOS

***

## 🤝 Crediti

- **Autore:** Gorlix
- **Design:** Material 3 by Google
- **Framework GUI:** [ttkbootstrap](https://ttkbootstrap.readthedocs.io/)
- **Gestione processi:** [psutil](https://github.com/giampaolo/psutil)
- **System tray:** [pystray](https://github.com/moses
