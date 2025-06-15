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
from openai import OpenAI
from history_manager import HistoryManager
from collections import deque
from command_mapper import CommandMapper

def get_prompt(history, user_input, system_prompt="Jesteś AI terminalem, odpowiadasz w stylu basha."):
    max_tokens = 2500
    current_prompt = [{"role": "system", "content": system_prompt}]
    token_sum = len(system_prompt.split())

    for entry in reversed(history.entries):
        tokens = len(entry["content"].split())
        if token_sum + tokens > max_tokens:
            break
        current_prompt.insert(1, entry)
        token_sum += tokens

    current_prompt.append({"role": "user", "content": user_input})
    return current_prompt


class HistoryManager:
    def __init__(self, history_file="history.jsonl", max_entries=50):
        self.history_file = history_file
        self.max_entries = max_entries
        self.entries = deque(maxlen=max_entries)
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        self.entries.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue

    def add_entry(self, role: str, content: str):
        entry = {"role": role, "content": content}
        self.entries.append(entry)
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_recent_history(self):
        return list(self.entries)


    def show_recent(self, n=5):
        """Wyświetla ostatnie n wpisów z historii"""
        for entry in list(self.entries)[-n:]:
            print(f"[{entry.get('timestamp')}] {entry.get('role', 'unknown').upper()}: {entry.get('content')}")


class Config:
    """Klasa konfiguracyjna z domyślnymi ustawieniami"""
    def __init__(self):
        self.LOG_FILE = "command_log.json"
        self.SAFETY_MODE = True
        self.MAX_HISTORY = 50
        self.SYSTEM_INFO = True
        self.ENABLE_FILE_OPS = True
        self.ENABLE_NETWORK_OPS = False
        self.ALLOWED_DIRS = [str(Path.home())]
        self.BLACKLISTED_DIRS = ["/", "/etc", "/bin", "/sbin", "/usr"]
        self.MEMORY_FILE = "session_memory.json"
        self.OPENAI_MODEL = "gpt-4"
        self.COMMAND_PREFIX = "!"

class SystemInspector:
    """Klasa do inspekcji systemu i dostarczania informacji do AI"""
    @staticmethod
    def get_system_info() -> Dict:
        """Zbiera kompleksowe informacje o systemie"""
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            info = {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_cores": os.cpu_count(),
                "memory": {
                    "total": mem.total,
                    "available": mem.available,
                    "percent": mem.percent
                },
                "disk_usage": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "current_user": getpass.getuser(),
                "environment": {
                    k: v for k, v in os.environ.items()
                    if not any(s in k.lower() for s in ["key", "pass", "token"])
                },
                "network": {
                    "hostname": platform.node(),
                    "ip_address": SystemInspector.get_ip_address(),
                },
                "python_version": platform.python_version(),
                "timestamp": datetime.now().isoformat()
            }
            return info
        except Exception as e:
            print(f"Błąd podczas zbierania informacji o systemie: {e}")
            return {}

    @staticmethod
    def get_ip_address() -> str:
        """Pobiera zewnętrzny adres IP"""
        try:
            return requests.get('https://api.ipify.org', timeout=3).text
        except:
            try:
                return requests.get('https://ifconfig.me', timeout=3).text
            except:
                return "127.0.0.1"

class CommandValidator:
    """Klasa do walidacji i bezpieczeństwa komend"""
    def __init__(self, config: Config):
        self.config = config
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

        self.dangerous_patterns = [
            (r'rm\s+-rf\s+\/', "Rekursywne usuwanie roota"),
            (r'(shutdown|reboot|poweroff|halt)', "Wyłączanie systemu"),
            (r'systemctl\s+(stop|disable)\s+', "Zatrzymywanie usług"),
            (r'(ifconfig|ip)\s+\w+\s+down', "Wyłączanie interfejsów"),
            (r'iptables\s+-F', "Czyszczenie firewall"),
            (r'm[v]\s+\/(etc|usr|bin|lib|sbin|var|boot)', "Przenoszenie systemowych katalogów"),
            (r'dd\s+if=\S+\s+of=\S+', "Operacje dd"),
            (r'mkfs\s+', "Formatowanie"),
            (r'chmod\s+[0]\s+\/etc\/(passwd|shadow|sudoers)', "Niebezpieczne uprawnienia"),
            (r'echo\s+\S+\s+>\s+\/(etc|usr|bin|lib|sbin|var|boot)', "Nadpisywanie systemowych plików"),
            (r':(){:|:&\};?', "Fork bomb"),
            (r'nc\s+-l', "Otwieranie portów"),
            (r'ssh\s+-[fNR]', "Niebezpieczne opcje SSH"),
        ]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Kompleksowa walidacja komendy pod kątem bezpieczeństwa"""
        if not self.config.SAFETY_MODE:
            return True, None

        command_lower = command.lower()

        if any(dir in command_lower for dir in self.config.BLACKLISTED_DIRS):
            return False, "Operacja na zabronionym katalogu"

        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, f"Niebezpieczna operacja: {description}"

        for pattern, description in self.warning_patterns:
            if re.search(pattern, command_lower):
                return True, f"Wymaga potwierdzenia: {description}"

        return True, None

class CommandExecutor:
    """Rozszerzona klasa do wykonywania komend z dodatkowymi funkcjami"""
    def __init__(self, config: Config, inspector: SystemInspector):
        self.config = config
        self.inspector = inspector

    def execute(self, command: str) -> Tuple[bool, str]:
        """Bezpieczne wykonanie komendy z pełnym logowaniem"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            self.log_command("WYKONANO", command, result.stdout)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            self.log_command("BŁĄD", command, e.stderr)
            return False, e.stderr
        except subprocess.TimeoutExpired:
            self.log_command("TIMEOUT", command, "Przekroczono czas wykonania")
            return False, "Przekroczono czas wykonania komendy"
        except Exception as e:
            self.log_command("BŁĄD", command, str(e))
            return False, str(e)

    def execute_with_pipe(self, command: str) -> Tuple[bool, str]:
        """Wykonanie komendy z potokowaniem"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=60)
            if process.returncode == 0:
                self.log_command("WYKONANO", command, stdout)
                return True, stdout
            else:
                self.log_command("BŁĄD", command, stderr)
                return False, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            self.log_command("TIMEOUT", command, "Przekroczono czas wykonania")
            return False, "Przekroczono czas wykonania komendy"
        except Exception as e:
            self.log_command("BŁĄD", command, str(e))
            return False, str(e)

    def log_command(self, status: str, command: str, output: str = ""):
        """Loguje wykonanie komendy z jej statusem i ewentualnym wynikiem"""
        print(f"[{status}] {command}")
        if output:
            print(output)

class FileOperations:
    """Bezpieczne operacje na plikach z kontrolą dostępu"""
    def __init__(self, config: Config):
        self.config = config

    def is_allowed_path(self, path: str) -> bool:
        """Sprawdza czy ścieżka jest dozwolona"""
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(allowed) for allowed in self.config.ALLOWED_DIRS) and \
                   not any(abs_path.startswith(blocked) for blocked in self.config.BLACKLISTED_DIRS)
        except Exception:
            return False

    def read_file(self, file_path: str) -> Optional[str]:
        """Bezpieczne czytanie pliku z walidacją ścieżki"""
        if not self.config.ENABLE_FILE_OPS or not self.is_allowed_path(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def write_file(self, file_path: str, content: str) -> bool:
        """Bezpieczne zapisywanie pliku"""
        if not self.config.ENABLE_FILE_OPS or not self.is_allowed_path(file_path):
            return False
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def append_to_file(self, file_path: str, content: str) -> bool:
        """Dopisuje zawartość do pliku"""
        if not self.config.ENABLE_FILE_OPS or not self.is_allowed_path(file_path):
            return False
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def delete_file(self, file_path: str) -> bool:
        """Bezpieczne usuwanie pliku"""
        if not self.config.ENABLE_FILE_OPS or not self.is_allowed_path(file_path):
            return False
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False

class CommandHistory:
    """Zarządzanie historią komend z limitem i zapisem do pliku"""
    def __init__(self, config: Config):
        self.config = config
        self.file_path = self.config.LOG_FILE
        self.history: List[Dict] = []
        self.load()

    def load(self):
        """Ładuje historię z pliku"""
        if os.path.isfile(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def save(self):
        """Zapisuje historię do pliku"""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.history[-self.config.MAX_HISTORY:], f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu historii: {e}")

    def add(self, command: str, result: str, status: str):
        """Dodaje nową komendę do historii"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "status": status,
            "result": result.strip()[:500]
        })
        self.save()

    def get_recent(self, count: int = 10) -> List[Dict]:
        """Zwraca ostatnie komendy"""
        return self.history[-count:]

class SessionMemory:
    """Zarządzanie pamięcią sesji między interakcjami"""
    def __init__(self, config: Config):
        self.config = config
        self.memory_file = self.config.MEMORY_FILE
        self.data: Dict[str, str] = {}
        self.load()

    def load(self):
        """Ładuje dane z pliku"""
        if os.path.isfile(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        """Zapisuje dane do pliku"""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu pamięci sesji: {e}")

    def set(self, key: str, value: str):
        """Ustawia wartość kontekstową"""
        self.data[key] = value
        self.save()

    def get(self, key: str) -> Optional[str]:
        """Pobiera wartość kontekstową"""
        return self.data.get(key)

    def clear(self):
        """Czyści całą pamięć"""
        self.data = {}
        self.save()

class AITerminal:
    """Główna klasa terminala AI z zarządzaniem sesją"""
    def __init__(self, config: Config, executor: CommandExecutor, file_ops: FileOperations):
        self.config = config
        self.executor = executor
        self.file_ops = file_ops
        self.history = self._load_history()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_info = SystemInspector().get_system_info()

    def add_to_history(self, command: str, output: str):
        """Dodaje wpis do historii i zapisuje do pliku"""
        self.history.append({
            "command": command,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
        self.history = self.history[-self.config.MAX_HISTORY:]
        self._save_history()

    def get_context_prompt(self) -> str:
        """Generuje rozbudowany prompt kontekstowy dla AI"""
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
        """Wysyła zapytanie do AI i przetwarza odpowiedź"""
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
        """Tłumaczy naturalne polecenia na komendy systemowe"""
        text = text.lower()
        if "zawartość katalogu" in text or "co jest w katalogu" in text or "pokaż katalog" in text:
            return "ls"
        if text.startswith("cd "):
            return text
        if text.startswith("pokaż plik ") or text.startswith("przeczytaj plik "):
            plik = text.split("plik ", 1)[1].strip()
            return f"cat {plik}"
        if text.startswith("stwórz plik ") or text.startswith("utwórz plik "):
            m = re.match(r'(stwórz|utwórz) plik (\S+)( i zapisz w nim (.+))?', text)
            if m:
                nazwa = m.group(2)
                tresc = m.group(4)
                if tresc:
                    return f'echo "{tresc}" > {nazwa}'
                else:
                    return f'touch {nazwa}'
        return None

    def _save_history(self):
        """Zapisuje historię do pliku JSON"""
        try:
            with open(self.config.MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd podczas zapisywania historii: {e}")

    def _load_history(self) -> List[Dict]:
        """Wczytuje historię z pliku JSON"""
        try:
            if os.path.exists(self.config.MEMORY_FILE):
                with open(self.config.MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Formatuje bajty do czytelnej postaci"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

history = HistoryManager("history.jsonl", max_entries=50)

def main():
    """Główna funkcja uruchamiająca terminal AI"""
    config = Config()
    inspector = SystemInspector()
    validator = CommandValidator(config)
    executor = CommandExecutor(config, inspector)
    file_ops = FileOperations(config)
    history = HistoryManager()
    terminal = AITerminal(config, executor, file_ops)

    terminal = AITerminal(config, executor, file_ops)

    print("🌐 GPT TERMINAL v2.0")
    print("Wpisz '!komenda' aby wykonać polecenie systemowe")
    print("Wpisz 'read <plik>' aby odczytać plik")
    print("Wpisz 'write <plik> <treść>' aby zapisać do pliku")
    print("Wpisz dowolny tekst aby pogadać z AI")
    print("Wpisz 'exit' aby zakończyć\n")


def main():
    """Główna funkcja uruchamiająca terminal AI"""
    # Inicjalizacja wszystkich potrzebnych komponentów
    config = Config()
    inspector = SystemInspector()
    validator = CommandValidator(config)
    executor = CommandExecutor(config, inspector)
    file_ops = FileOperations(config)
    history = HistoryManager()

    # Inicjalizacja terminala
    terminal = AITerminal(config, executor, file_ops)

    print("🌐 GPT TERMINAL v2.0")
    print("Wpisz '!komenda' aby wykonać polecenie systemowe")
    print("Wpisz 'read <plik>' aby odczytać plik")
    print("Wpisz 'write <plik> <treść>' aby zapisać do pliku")
    print("Wpisz dowolny tekst aby pogadać z AI")
    print("Wpisz 'exit' aby zakończyć\n")

    while True:
        try:
            user_input = input("hal@ai-term:~$ ").strip()

            # Zapis inputu użytkownika
            history.add_entry("user", user_input)

            # Obsługa komendy exit
            if user_input.lower() == 'exit':
                break

            # Interpretacja poleceń naturalnych
            natural_cmd = terminal.translate_natural_command(user_input)
            if natural_cmd:
                print(f"Wykonuję: {natural_cmd}")
                history.add_entry("assistant", f"Tłumaczę na: {natural_cmd}")
                user_input = natural_cmd

            # Obsługa komend systemowych
            if user_input.startswith(config.COMMAND_PREFIX):
                cmd = user_input[1:]
                is_valid, reason = validator.validate_command(cmd)

                if not is_valid:
                    print(f"🛑 {reason}")
                    history.add_entry("system", f"Zablokowano komendę: {reason}")
                    continue

                success, output = executor.execute(cmd)
                if success:
                    print(output)
                    history.add_entry("system", f"Wykonano: {cmd}")
                else:
                    print(f"❌ {output}")
                    history.add_entry("system", f"Błąd wykonania: {cmd}")
                continue

            # Obsługa operacji na plikach
            if user_input.startswith('read '):
                file_path = user_input[5:].strip()
                content = file_ops.read_file(file_path)
                if content is not None:
                    print(content)
                    history.add_entry("system", f"Odczytano plik: {file_path}")
                else:
                    print("🛑 Nie można odczytać pliku lub brak uprawnień")
                    history.add_entry("system", f"Błąd odczytu pliku: {file_path}")
                continue

            if user_input.startswith('write '):
                parts = user_input[6:].split(maxsplit=1)
                if len(parts) == 2:
                    file_path, content = parts
                    if file_ops.write_file(file_path, content):
                        print("✔ Zapisano plik")
                        history.add_entry("system", f"Zapisano plik: {file_path}")
                    else:
                        print("🛑 Nie można zapisać pliku lub brak uprawnień")
                        history.add_entry("system", f"Błąd zapisu pliku: {file_path}")
                else:
                    print("🛑 Nieprawidłowy format: write <plik> <treść>")
                continue

            # Interakcja z AI
            ai_response = terminal.query_ai(user_input)
            print(ai_response)
            history.add_entry("assistant", ai_response)

        except KeyboardInterrupt:
            print("\nWpisz 'exit' aby zakończyć")
            continue
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd: {e}")
            history.add_entry("system", f"Błąd systemowy: {str(e)}")
            continue

if __name__ == "__main__":
    main()
