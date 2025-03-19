import os

# Funkcja do tworzenia tablicy kodowania
def create_coding_table():
    table = []
    characters = [chr(i) for i in range(97, 123)] + [str(i) for i in range(1, 10)] + ['0']
    size = len(characters)
    for i in range(size):
        row = characters[i:] + characters[:i]
        table.append(row)
    return table

# Funkcja do konwersji polskich znaków
def convert_polish_chars(text):
    replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
    for pl_char, repl_char in replacements.items():
        text = text.replace(pl_char, repl_char)
    return text

# Funkcja do zaszyfrowania wiadomości
def encrypt_message(message, key, table):
    message = convert_polish_chars(message.lower())
    key = convert_polish_chars(key.lower())
    encrypted = ""
    key_len = len(key)
    characters = [chr(i) for i in range(97, 123)] + [str(i) for i in range(1, 10)] + ['0']

    for i, char in enumerate(message):
        if char not in characters:
            encrypted += char
            continue
        row = characters.index(char)
        col = characters.index(key[i % key_len])
        encrypted += table[row][col]
    return encrypted

# Funkcja do odszyfrowania wiadomości
def decrypt_message(message, key, table):
    message = convert_polish_chars(message.lower())
    key = convert_polish_chars(key.lower())
    decrypted = ""
    key_len = len(key)
    characters = [chr(i) for i in range(97, 123)] + [str(i) for i in range(1, 10)] + ['0']

    for i, char in enumerate(message):
        if char not in characters:
            decrypted += char
            continue
        col = characters.index(key[i % key_len])
        row = [table[r][col] for r in range(len(table))].index(char)
        decrypted += characters[row]
    return decrypted

# Główna funkcja programu
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    table = create_coding_table()
    print("Wybierz opcję:")
    print("z - Zaszyfruj wiadomość")
    print("o - Odszyfruj wiadomość")
    choice = input("Twój wybór: ").strip().lower()

    if choice not in ['z', 'o']:
        print("Nieprawidłowy wybór!")
        return

    key = input("Wprowadź klucz szyfrujący (minimum 5 znaków): ").strip()
    if len(key) < 5:
        print("Klucz musi mieć co najmniej 5 znaków!")
        return

    message = input("Wprowadź wiadomość: ").strip()

    if choice == 'z':
        result = encrypt_message(message, key, table)
        print("\033[91mZaszyfrowana wiadomość:\033[0m", result)
    else:
        result = decrypt_message(message, key, table)
        print("\033[92mOdszyfrowana wiadomość:\033[0m", result)

if __name__ == "__main__":
    main()
