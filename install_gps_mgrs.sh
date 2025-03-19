#!/data/data/com.termux/files/usr/bin/bash

# Aktualizacja pakietów i instalacja zależności
pkg update -y
pkg install -y python python-pip termux-api

# Instalacja wymaganych bibliotek Python
pip install mgrs utm

# Tworzenie katalogu na skrypt
mkdir -p ~/gps_mgrs
cd ~/gps_mgrs

# Tworzenie skryptu GPS
cat > gps_mgrs.py <<EOF
# Tutaj wklej cały kod swojego programu
EOF

# Tworzenie skryptu startowego
cat > gps_mgrs.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
python ~/gps_mgrs/gps_mgrs.py
EOF

# Nadanie uprawnień do uruchamiania
chmod +x gps_mgrs.sh

# Powiadomienie o zakończeniu instalacji
echo "✅ Instalacja zakończona! Uruchom program komendą: ~/gps_mgrs/gps_mgrs.sh"
