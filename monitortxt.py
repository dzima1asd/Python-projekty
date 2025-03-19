import os
import subprocess

# Katalog, w którym będą zapisywane pliki z komendami
monitor_dir = "/storage/emulated/0/Download"

# Funkcja monitorująca katalog na nowe pliki
def monitor_directory():
    print("Monitoruję katalog:", monitor_dir)
    if not os.path.exists(monitor_dir):
        print(f"Katalog {monitor_dir} nie istnieje.")
        return
    
    while True:
        files = os.listdir(monitor_dir)
        for file in files:
            file_path = os.path.join(monitor_dir, file)

            # Sprawdzamy, czy plik jest tekstowy
            if os.path.isfile(file_path) and file.endswith(".txt"):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        command = f.read().strip()

                    if command:
                        print(f"Znaleziono plik: {file} z komendą: {command}")
                        user_input = input(f"Czy chcesz wykonać komendę '{command}'? [y/n]: ")
                        if user_input.lower() == "y":
                            execute_command(command)
                            os.remove(file_path)
                            print(f"Komenda '{command}' została wykonana.")
                        else:
                            print("Komenda nie została wykonana.")
                except Exception as e:
                    print(f"Błąd podczas przetwarzania pliku {file}: {e}")

# Funkcja wykonująca komendę
def execute_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas wykonywania komendy: {e}")

# Uruchomienie monitorowania katalogu
monitor_directory()
