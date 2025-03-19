#!/data/data/com.termux/files/usr/bin/bash

Instalator automatyczny dla programu GPS-MGRS

echo "=== Instalacja zależności ===" pkg update -y && pkg upgrade -y pkg install -y python termux-api dialog

echo "=== Tworzenie i aktywacja wirtualnego środowiska ===" pkg install -y python-virtualenv VENV_DIR="$HOME/myenv" python -m venv "$VENV_DIR" source "$VENV_DIR/bin/activate"

echo "=== Instalacja bibliotek Python w myenv ===" pip install --upgrade pip pip install mgrs utm

Tworzenie katalogu i kopiowanie plików

INSTALL_DIR="$HOME/gps_mgrs" mkdir -p "$INSTALL_DIR" cp gps_program.py "$INSTALL_DIR/gps_program.py"

echo "=== Tworzenie skryptu startowego ===" START_SCRIPT="$HOME/.shortcuts/gps_mgrs.sh" mkdir -p "$HOME/.shortcuts" echo "#!/data/data/com.termux/files/usr/bin/bash" > "$START_SCRIPT" echo "source $VENV_DIR/bin/activate" >> "$START_SCRIPT" echo "python $INSTALL_DIR/gps_program.py" >> "$START_SCRIPT" chmod +x "$START_SCRIPT"

Dodanie opcji diagnostyki

echo "=== Tworzenie skryptu diagnostycznego ===" DIAG_SCRIPT="$HOME/.shortcuts/gps_mgrs_diag.sh" echo "#!/data/data/com.termux/files/usr/bin/bash" > "$DIAG_SCRIPT" echo "source $VENV_DIR/bin/activate" >> "$DIAG_SCRIPT" echo "python $INSTALL_DIR/gps_program.py --diagnostics" >> "$DIAG_SCRIPT" chmod +x "$DIAG_SCRIPT"

Powiadomienie użytkownika

echo "Instalacja zakończona! Aby uruchomić:" echo "  - Program: shortcuts gps_mgrs.sh" echo "  - Diagnostyka: shortcuts gps_mgrs_diag.sh"

