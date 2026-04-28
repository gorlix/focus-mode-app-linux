#!/usr/bin/env bash

# Ottieni la directory del progetto in modo sicuro
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$PROJECT_DIR" || exit 1

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Trova un virtual environment valido o creane uno
VENV_PATH=""
for d in venv .venv .venv_new; do
    if [ -d "$d" ] && [ -f "$d/bin/activate" ]; then
        VENV_PATH="$d"
        break
    fi
done

if [ -z "$VENV_PATH" ]; then
    echo "📦 Nessun Virtual Environment trovato. Creazione di .venv..."
    python3 -m venv .venv
    VENV_PATH=".venv"
fi

echo "🔄 Attivazione Virtual Environment ($VENV_PATH)..."
source "$VENV_PATH/bin/activate"

# Controllo dipendenze
if ! python -c "import ttkbootstrap" >/dev/null 2>&1; then
    echo "📥 Installazione dipendenze mancanti..."
    pip install -r requirements.txt
fi

echo "🚀 Avvio Focus Mode App..."
# Avvia l'applicazione intercettando eventuali errori
if ! python focus_mode_app/main.py; then
    echo "❌ Errore durante l'avvio dell'applicazione."
    exit 1
fi
