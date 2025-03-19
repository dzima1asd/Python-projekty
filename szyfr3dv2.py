import os
import string

# Funkcja generująca losowy klucz o zadanej długości bitowej
def generate_key(bit_length):
    byte_length = bit_length // 8
    return os.urandom(byte_length)

# Funkcja konwertująca klucz z postaci bitowej na tekstową
def key_to_text(key_bytes):
    chars = string.ascii_lowercase + "1234567890"
    key_text = ''.join(chars[b % len(chars)] for b in key_bytes)
    return key_text

# Funkcja szyfrująca
def encrypt_text(text, white_key, black_key, chars):
    encrypted = ""
    for i, char in enumerate(text):
        t_idx = chars.index(char)
        w_idx = chars.index(white_key[i % len(white_key)])
        b_idx = chars.index(black_key[i % len(black_key)])
        encrypted_idx = (t_idx + w_idx + b_idx) % len(chars)
        encrypted += chars[encrypted_idx]
    return encrypted

# Funkcja deszyfrująca
def decrypt_text(encrypted, white_key, black_key, chars):
    decrypted = ""
    for i, char in enumerate(encrypted):
        e_idx = chars.index(char)
        w_idx = chars.index(white_key[i % len(white_key)])
        b_idx = chars.index(black_key[i % len(black_key)])
        decrypted_idx = (e_idx - w_idx - b_idx) % len(chars)
        decrypted += chars[decrypted_idx]
    return decrypted

# Główna funkcja programu
def main():
    chars = string.ascii_lowercase + "1234567890"
    
    # Wybór trybu działania
    print("Wybierz tryb działania:")
    print("1. Szyfrowanie")
    print("2. Odszyfrowanie")
    choice = input("Wprowadź 1 lub 2: ").strip()

    if choice not in {"1", "2"}:
        print("Nieprawidłowy wybór. Zakończenie programu.")
        return

    # Pobranie klucza czarnego
    black_key = input("Wprowadź klucz czarny: ").lower()
    black_key = ''.join(filter(lambda x: x in chars, black_key))  # Filtracja znaków

    if not black_key:
        print("Klucz czarny nie może być pusty!")
        return

    if choice == "1":  # Szyfrowanie
        text = input("Wprowadź tekst do zaszyfrowania: ").lower()
        text = ''.join(filter(lambda x: x in chars, text))  # Filtracja znaków

        if not text:
            print("Tekst do zaszyfrowania nie może być pusty!")
            return

        # Generowanie klucza białego
        white_key_bits = generate_key(128)  # 128-bitowy klucz
        white_key = key_to_text(white_key_bits)

        # Szyfrowanie
        encrypted = encrypt_text(text, white_key, black_key, chars)
        
        # Wyświetlenie wyników
        print("\nWyniki szyfrowania:")
        print(f"Klucz biały: {white_key}")
        print(f"Tekst zaszyfrowany: {encrypted}")

    elif choice == "2":  # Odszyfrowanie
        white_key = input("Wprowadź klucz biały: ").lower()
        white_key = ''.join(filter(lambda x: x in chars, white_key))  # Filtracja znaków

        if not white_key:
            print("Klucz biały nie może być pusty!")
            return

        encrypted = input("Wprowadź tekst do odszyfrowania: ").lower()
        encrypted = ''.join(filter(lambda x: x in chars, encrypted))  # Filtracja znaków

        if not encrypted:
            print("Tekst do odszyfrowania nie może być pusty!")
            return

        # Odszyfrowanie
        decrypted = decrypt_text(encrypted, white_key, black_key, chars)
        
        # Wyświetlenie wyników
        print("\nWyniki odszyfrowania:")
        print(f"Tekst odszyfrowany: {decrypted}")

# Uruchomienie programu
if __name__ == "__main__":
    main()
