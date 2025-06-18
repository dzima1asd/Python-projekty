import os
import re
import shlex
import subprocess
import platform
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import psutil
import requests
import getpass
from collections import deque
from openai import OpenAI
import difflib
import os

if not os.getenv("OPENAI_API_KEY"):
    print("🔐 Nie wykryto klucza OpenAI API.")
    key = input("Podaj swój klucz OpenAI API: ").strip()
    os.environ["OPENAI_API_KEY"] = key
    print("✅ Klucz zapisany w zmiennej środowiskowej.")



def auto_update():
    try:
        url = "https://raw.githubusercontent.com/dzima1asd/Python-projekty/main/gpt_chat.py"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and "def main():" in response.text:
            current_code = Path(__file__).read_text(encoding="utf-8")
            if response.text.strip() != current_code.strip():
                Path(__file__).write_text(response.text, encoding="utf-8")
                print("✅ Terminal zaktualizowany. Uruchom ponownie.")
                exit(0)
        else:
            print("⚠️ Brak aktualizacji lub nieprawidłowa zawartość (HTTP", response.status_code, ")")
    except Exception as e:
        print(f"❌ Autoaktualizacja nie powiodła się: {e}")


# === Config ===
class Config:
    def __init__(self):
        self.LOG_FILE = "command_log.json"
        self.SAFETY_MODE = True
        self.MAX_HISTORY = 50
        self.SYSTEM_INFO = True
        self.ENABLE_FILE_OPS = True
        self.ENABLE_NETWORK_OPS = False
        self.ALLOWED_DIRS = [str(Path.home())]
        self.BLACKLISTED_DIRS = ["/etc", "/bin", "/sbin", "/usr"]
        self.MEMORY_FILE = "session_memory.json"
        self.OPENAI_MODEL = "gpt-4"
        self.COMMAND_PREFIX = "!"

# === System Inspector ===
class SystemInspector:
    @staticmethod
    def get_system_info() -> Dict:
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_cores": os.cpu_count(),
                "memory": {"total": mem.total, "available": mem.available, "percent": mem.percent},
                "disk_usage": {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent},
                "current_user": getpass.getuser(),
                "hostname": platform.node(),
                "ip_address": SystemInspector.get_ip_address(),
                "environment": {k: v for k, v in os.environ.items() if not any(s in k.lower() for s in ["key", "pass", "token"])},
                "python_version": platform.python_version(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_ip_address() -> str:
        try:
            return requests.get('https://api.ipify.org', timeout=3).text
        except:
            try:
                return requests.get('https://ifconfig.me', timeout=3).text
            except:
                return "127.0.0.1"

# === Session Memory ===
class SessionMemory:
    def __init__(self, config: Config):
        self.config = config
        self.memory_file = self.config.MEMORY_FILE
        self.data: Dict[str, str] = {}
        self.load()

    def load(self):
        if os.path.isfile(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu pamięci sesji: {e}")

    def set(self, key: str, value: str):
        self.data[key] = value
        self.save()

    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)

    def clear(self):
        self.data = {}
        self.save()

class CommandValidator:
    """Klasa do walidacji i bezpieczeństwa komend"""

    def __init__(self, config: Config):
        self.config = config
        self.dangerous_patterns = [
            (r'rm\s+-rf\s+/', "Rekursywne usuwanie roota"),
            (r'(shutdown|reboot|poweroff|halt)', "Wyłączanie systemu"),
            (r'systemctl\s+(stop|disable)\s+', "Zatrzymywanie usług"),
            (r'(ifconfig|ip)\s+\w+\s+down', "Wyłączanie interfejsów"),
            (r'iptables\s+-F', "Czyszczenie firewall"),
            (r'mkfs\s+', "Formatowanie"),
            (r'chmod\s+[0]\s+/etc/(passwd|shadow|sudoers)', "Niebezpieczne uprawnienia"),
            (r'echo\s+.+\s+>\s+/etc/', "Nadpisywanie systemowych plików"),
            (r':(){:|:&};', "Fork bomb"),
            (r'nc\s+-l', "Otwieranie portów"),
            (r'ssh\s+-[fNR]', "Niebezpieczne opcje SSH"),
        ]
        self.warning_patterns = [
            (r'rm\s', "Usuwanie plików"),
            (r'apt\s+(install|remove|purge)', "Zarządzanie pakietami"),
            (r'(yum|dnf|pacman)\s+(install|remove|-S|-R)', "Zarządzanie pakietami"),
            (r'(chmod|chown)\s+', "Zmiana uprawnień/właściciela"),
            (r'(mv|cp)\s+\S+\s+\S+', "Operacje na plikach"),
            (r'dd\s+', "Operacje na dysku"),
            (r'git\s+(push|reset|checkout)', "Operacje Git"),
            (r'curl\s+\S+', "Pobieranie plików"),
            (r'wget\s+\S+', "Pobieranie plików"),
        ]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Kompleksowa walidacja komendy pod kątem bezpieczeństwa"""
        if not self.config.SAFETY_MODE:
            return True, None

        command_lower = command.lower()

        # Sprawdzenie, czy argumenty komendy wskazują na zabroniony katalog
        for blocked in self.config.BLACKLISTED_DIRS:
            matches = re.findall(r'[\s\'"](/[^\'"\s]+)', command_lower)
            for path in matches:
                if path.startswith(blocked):
                    return False, f"Zabroniona ścieżka: {blocked}"

        # Wzorce niebezpieczne
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, f"Niebezpieczna operacja: {description}"

        # Wzorce ostrzegawcze
        for pattern, description in self.warning_patterns:
            if re.search(pattern, command_lower):
                return True, f"Wymaga potwierdzenia: {description}"

        return True, None

# === File Operations ===
class FileOperations:
    def __init__(self, config: Config):
        self.config = config

    def _is_safe(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(allowed) for allowed in self.config.ALLOWED_DIRS) and \
               not any(abs_path.startswith(blocked) for blocked in self.config.BLACKLISTED_DIRS)


    def read_file(self, path: str) -> Optional[str]:
        if not self._is_safe(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None

    def write_file(self, path: str, content: str) -> bool:
        if not self._is_safe(path):
            return False
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except:
            return False

    def append_to_file(self, path: str, content: str) -> bool:
        if not self._is_safe(path):
            return False
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            return True
        except:
            return False

    def delete_file(self, path: str) -> bool:
        if not self._is_safe(path):
            return False
        try:
            os.remove(path)
            return True
        except:
            return False

# === Command Executor ===

class CommandExecutor:
    def __init__(self, config: Config, inspector: SystemInspector):
        self.config = config
        self.inspector = inspector

    def execute(self, command: str) -> Tuple[bool, str]:
        """Wykonuje komendę systemową z logowaniem i obsługą wyjątków"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            status = "WYKONANO" if result.returncode == 0 else "BŁĄD"
            output = result.stdout if result.returncode == 0 else result.stderr
            self.log_command(status, command, output)
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            self.log_command("TIMEOUT", command, "Przekroczono czas wykonania")
            return False, "Przekroczono czas wykonania komendy"
        except Exception as e:
            self.log_command("BŁĄD", command, str(e))
            return False, str(e)

    def log_command(self, status: str, command: str, output: str = ""):
        print(f"[{status}] {command}")
        if output:
            print(output)

# === AITerminal ===
class AITerminal:
    def __init__(self, config: Config, executor, file_ops):
        self.config = config
        self.executor = executor
        self.file_ops = file_ops
        self.history: List[Dict] = self._load_history()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_info = SystemInspector.get_system_info()

    def add_to_history(self, command: str, output: str):
        self.history.append({
            "command": command,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
        self.history = self.history[-self.config.MAX_HISTORY:]
        self._save_history()

    def _save_history(self):
        try:
            with open(self.config.MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd podczas zapisywania historii: {e}")

    def _load_history(self) -> List[Dict]:
        try:
            if os.path.exists(self.config.MEMORY_FILE):
                with open(self.config.MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def get_context_prompt(self) -> str:
        context = [
            "Jesteś inteligentnym asystentem terminalowym. Masz następujące informacje o systemie:",
            f"System: {self.system_info.get('system', 'N/A')} {self.system_info.get('release', 'N/A')}",
            f"Procesor: {self.system_info.get('processor', 'N/A')} ({self.system_info.get('cpu_cores', 'N/A')} cores)",
            f"Pamięć: {self._format_bytes(self.system_info.get('memory', {}).get('total', 0))}",
            f"Użytkownik: {self.system_info.get('current_user', 'N/A')}",
            f"Katalog domowy: {os.path.expanduser('~')}",
            "\nOstatnie komendy:"
        ]
        for item in self.history[-5:]:
            context.append(f"- {item['command']} (output: {item['output'][:50]}...)")
        context.append("\nFormat odpowiedzi:")
        context.append("WYKONAJ: <komenda> - dla komend do wykonania")
        context.append("PLIK: <operacja> <ścieżka> - dla operacji na plikach")
        context.append("PYTANIE: <pytanie> - dla zapytań o system")
        return "\n".join(context)

    def query_ai(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.get_context_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Błąd zapytania do OpenAI: {str(e)}"

    def translate_natural_command(self, text: str) -> Optional[str]:
        text = text.lower()
        if "zawartość katalogu" in text or "co jest w katalogu" in text or "pokaż katalog" in text:
            return "ls"
        if text.startswith("cd "):
            return text
        if text.startswith("pokaż plik ") or text.startswith("przeczytaj plik "):
            plik = text.split("plik ", 1)[1].strip()
            return f"cat {plik}"
        if text.startswith("stwórz plik ") or text.startswith("utwórz plik "):
            m = re.match(r'(stwórz|utwórz) plik (\\S+)( i zapisz w nim (.+))?', text)
            if m:
                nazwa = m.group(2)
                tresc = m.group(4)
                if tresc:
                    return f'echo \"{tresc}\" > {nazwa}'
                else:
                    return f'touch {nazwa}'
        return None

    @staticmethod
    def _format_bytes(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

# --- AI Response Handler: WYKONAJ ---
def parse_and_execute_ai_response(response: str, config, validator, executor, terminal):
    lines = response.strip().splitlines()
    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("wykonaj:"):
            command = stripped[8:].strip()
            print(f"➡️ AI sugeruje wykonanie: {command}")
            confirm = input("Czy wykonać? [Y/n]: ").strip().lower()
            if confirm not in ["", "y", "yes", "tak"]:
                print("❌ Anulowano wykonanie.")
                return

            valid, msg = validator.validate_command(command)
            if not valid:
                print(f"🔚 Blokada bezpieczeństwa: {msg}")
                return
            if msg:
                print(f"⚠️ Ostrzeżenie: {msg}")

            success, output = executor.execute(command)
            print(output)
            terminal.add_to_history(command, output)
            return

#--- AI Response Handler: File Operations ---

def handle_file_operations(response: str, file_ops, terminal):
    lines = response.strip().splitlines()
    for line in lines:
        stripped = line.strip()

        # PLIK: przeczytaj <plik>
        if "plik" in stripped.lower() and "przeczytaj" in stripped.lower():
            match = re.search(r'przeczytaj\s+plik\s+(\S+)', stripped, re.IGNORECASE)
            if match:
                path = match.group(1)
                content = file_ops.read_file(path)
                if content:
                    print(content)
                    terminal.add_to_history(f"read {path}", content[:200])
                else:
                    print("❌ Nie udało się odczytać pliku")
                return

        # PLIK: zapisz <plik> zawiera <treść>
        if "plik" in stripped.lower() and "zapisz" in stripped.lower():
            match = re.search(r'zapisz\s+plik\s+(\S+)\s+zawiera\s+(.+)', stripped, re.IGNORECASE)
            if match:
                path, content = match.group(1), match.group(2)
                if file_ops.write_file(path, content):
                    print("✅ Zapisano plik")
                    terminal.add_to_history(f"write {path}", content)
                else:
                    print("❌ Błąd zapisu pliku")
                return

# PLIK: przeczytaj <plik>
    if "plik" in stripped.lower() and "przeczytaj" in stripped.lower():
        match = re.search(r'przeczytaj\s+plik\s+(\S+)', stripped, re.IGNORECASE)
        if match:
            path = match.group(1)
            content = file_ops.read_file(path)
            if content:
                print(content)
                terminal.add_to_history(f"read {path}", content[:200])
            else:
                print("\u274c Nie uda\u0142o si\u0119 odczyta\u0107 pliku")
            return

    # PLIK: zapisz <plik> zawiera <tre\u015b\u0107>
    if "plik" in stripped.lower() and "zapisz" in stripped.lower():
        match = re.search(r'zapisz\s+plik\s+(\S+)\s+zawiera\s+(.+)', stripped, re.IGNORECASE)
        if match:
            path, content = match.group(1), match.group(2)
            if file_ops.write_file(path, content):
                print("\u2705 Zapisano plik")
                terminal.add_to_history(f"write {path}", content)
            else:
                print("\u274c B\u0142\u0105d zapisu pliku")
            return

# --- AI Response Handler: Wykonaj Komendę ---
def parse_and_execute_ai_response(response: str, config, validator, executor, terminal):
    lines = response.strip().splitlines()
    for line in lines:
        stripped = line.strip()

        # Sprawdź, czy AI sugeruje wykonanie komendy
        if stripped.lower().startswith("wykonaj:"):
            command = stripped[8:].strip()
            print(f"➡️ AI sugeruje wykonanie: {command}")
            confirm = input("Czy wykonać? [Y/n]: ").strip().lower()
            if confirm not in ["", "y", "yes", "tak"]:
                print("❌ Anulowano wykonanie.")
                return

            valid, msg = validator.validate_command(command)
            if not valid:
                print(f"🛑 Blokada bezpieczeństwa: {msg}")
                return
            if msg:
                print(f"⚠️ Ostrzeżenie: {msg}")
            success, output = executor.execute(command)
            print(output)
            terminal.add_to_history(command, output)
            return

# Sprawdź, czy AI sugeruje wykonanie komendy
    if stripped.lower().startswith("wykonaj:"):
        command = stripped[8:].strip()
        print(f"➡️ AI sugeruje wykonanie: {command}")
        confirm = input("Czy wykona\u0107? [Y/n]: ").strip().lower()
        if confirm not in ["", "y", "yes", "tak"]:
            print("\u274c Anulowano wykonanie.")
            return

        valid, msg = validator.validate_command(command)
        if not valid:
            print(f"🔚 Blokada bezpiecze\u0144stwa: {msg}")
            return
        if msg:
            print(f"⚠️ Ostrze\u017cenie: {msg}")
        success, output = executor.execute(command)
        print(output)
        terminal.add_to_history(command, output)
        return

def załaduj_komendy_urządzeń(plik: str = "device_commands.json") -> dict:
    """Wczytuje plik z komendami dla urządzeń, np. przekaźników, LED itp."""
    try:
        with open(plik, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Nie udało się załadować komend urządzeń: {e}")
        return {}

def interpretuj_polecenie_urządzenia(tekst: str, komendy: dict) -> Optional[str]:
    """Analizuje polecenie tekstowe i próbuje dopasować do komend urządzeń"""
    tekst = tekst.lower()
    for urządzenie, akcje in komendy.items():
        if urządzenie in tekst:
            if "włącz" in tekst:
                return akcje.get("włącz")
            if "wyłącz" in tekst or "zgaś" in tekst:
                return akcje.get("wyłącz")
    return None

def załaduj_komendy_urządzeń(plik="device_commands.json"):
    try:
        with open(plik, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Błąd ładowania komend urządzeń: {e}")
        return {}

def interpretuj_polecenie_urządzenia(tekst: str, komendy: dict):
    tekst = tekst.lower()
    nazwy_urzadzen = list(komendy.keys())

    # Bezpośrednie dopasowanie
    for urządzenie in nazwy_urzadzen:
        if urządzenie in tekst or any(słowo in tekst for słowo in urządzenie.split()):
            if "włącz" in tekst:
                return komendy[urządzenie].get("włącz")
            elif any(słowo in tekst for słowo in ["wyłącz", "zgaś", "zgasz", "wyłączyć"]):
                return komendy[urządzenie].get("wyłącz")

    # Fuzzy matching
    pasujace = difflib.get_close_matches(tekst, nazwy_urzadzen, n=1, cutoff=0.4)
    if pasujace:
        urządzenie = pasujace[0]
        if "włącz" in tekst:
            return komendy[urządzenie].get("włącz")
        elif any(słowo in tekst for słowo in ["wyłącz", "zgaś", "zgasz", "wyłączyć"]):
            return komendy[urządzenie].get("wyłącz")

    return None

# === Main Loop ===

def main():
    config = Config()
    inspector = SystemInspector()
    validator = CommandValidator(config)
    executor = CommandExecutor(config, inspector)
    file_ops = FileOperations(config)
    terminal = AITerminal(config, executor, file_ops)

    print("🌐 GPT TERMINAL FUSION – wpisz 'exit' aby zakończyć")
    print("📁 read <plik> – odczyt pliku")
    print("✏️ write <plik> <treść> – zapis do pliku")
    print("📡 !komenda – wykonanie polecenia systemowego ")

    while True:
        try:

            user_input = input("hal@ai-term:~$ ").strip()

         # Obsługa komendy help
        if user_input.lower() == "help":
            print("📖 Dostępne polecenia:")
            print("  exit                      – zakończenie działania")
            print("  read <plik>              – odczyt pliku")
            print("  write <plik> <treść>     – zapis do pliku")
            print("  !<komenda>               – wykonanie komendy systemowej")
            print("  dowolne polecenie        – przekaż AI")
            continue

        # Obsługa komendy exit
        if user_input.lower() == "exit":
            print("👋 Do zobaczenia, Jaśnie Panie!")
        break


            # Sprawdź, czy pasuje do polecenia urządzenia
            komendy_urządzeń = załaduj_komendy_urządzeń()
            komenda_z_urz = interpretuj_polecenie_urządzenia(user_input, komendy_urządzeń)
            if komenda_z_urz:
                print(f"➡️ Zinterpretowano jako: {komenda_z_urz}")
                confirm = input("Czy wykonać? [Y/n]: ").strip().lower()
                if confirm in ["", "y", "yes", "tak"]:
                    is_valid, reason = validator.validate_command(komenda_z_urz)
                    if not is_valid:
                        print(f"🛑 {reason}")
                        continue
                    if reason:
                        print(f"⚠️ Ostrzeżenie: {reason}")
                    success, output = executor.execute(komenda_z_urz)
                    print(output)
                    terminal.add_to_history(user_input, output)
                else:
                    print("❌ Anulowano wykonanie.")
                continue  # nie wysyłamy do AI, bo już zrobione

            # Obsługa komend prefiksowanych "!"
            if user_input.startswith(config.COMMAND_PREFIX):
                command = user_input[1:]
                valid, msg = validator.validate_command(command)
                if not valid:
                    print(f"🛑 Blokada bezpieczeństwa: {msg}")
                    continue
                if msg:
                    print(f"⚠️ Ostrzeżenie: {msg}")
                print(f"➡️ Uruchamiam: {command}")
                success, output = executor.execute(command)
                print(output)
                terminal.add_to_history(command, output)
                continue

            # Obsługa czytania plików
            if user_input.startswith("read "):
                path = user_input[5:].strip()
                content = file_ops.read_file(path)
                if content:
                    print(content)
                    terminal.add_to_history(f"read {path}", content[:200])
                else:
                    print("❌ Nie udało się odczytać pliku")
                continue

            # Obsługa zapisu do plików
            if user_input.startswith("write "):
                parts = shlex.split(user_input)
                if len(parts) >= 3:
                    path, content = parts[1], " ".join(parts[2:])
                    if file_ops.write_file(path, content):
                        print("✅ Zapisano")
                        terminal.add_to_history(f"write {path}", content)
                    else:
                        print("❌ Błąd zapisu")
                else:
                    print("❌ Błąd składni: write <plik> <treść>")
                continue

            # Interakcja z AI
            ai_response = terminal.query_ai(user_input)
            print(ai_response)
            terminal.add_to_history(user_input, ai_response)

            # Sprawdź, czy AI wygenerował komendę do wykonania lub operację na pliku
            parse_and_execute_ai_response(ai_response, config, validator, executor, terminal)
            handle_file_operations(ai_response, file_ops, terminal)

        except KeyboardInterrupt:
            print("\n⏹️ Przerwano – wpisz 'exit' aby zakończyć.")
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd: {e}")


if __name__ == "__main__":
    main()