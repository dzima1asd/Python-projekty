import os
import string
import random
import math

# Funkcja generująca losowy klucz o zadanej długości bitowej
def generate_key(bit_length):
    byte_length = bit_length // 8
    return os.urandom(byte_length)

# Funkcja konwertująca klucz z postaci bitowej na tekstową
def key_to_text(key_bytes):
    chars = string.ascii_lowercase + "1234567890"
    key_text = ''.join(chars[b % len(chars)] for b in key_bytes)
    return key_text

# Funkcja szyfrująca wstępnie
def encrypt_text(text, white_key, black_key, chars):
    encrypted = ""
    for i, char in enumerate(text):
        t_idx = chars.index(char)
        w_idx = chars.index(white_key[i % len(white_key)])
        b_idx = chars.index(black_key[i % len(black_key)])
        encrypted_idx = (t_idx + w_idx + b_idx) % len(chars)
        encrypted += chars[encrypted_idx]
    return encrypted

# Funkcja tworząca tablicę znaków
def generate_table(size, chars):
    return [random.choice(chars) for _ in range(size * size)]

# Funkcja wyznaczająca współrzędne opal/iryd
def get_coordinates(char, key_char, chars, size):
    char_value = chars.index(char) + 1
    key_value = chars.index(key_char) + 1
    result = (char_value * key_value) % size
    return result


def sprawdz_wspolrzedne(x, y, table_size):
    if x < 0 or x >= table_size or y < 0 or y >= table_size:
        print(f"Błąd: Nieprawidłowe współrzędne x={x}, y={y}")
        print(f"Rozmiar tablicy: {table_size}x{table_size}")
        return []



# Funkcja ukrywania sekwencji w tablicy
def embed_sequence(table, sequence, opal, iryd, size):
    x, y = opal, iryd
    for char in sequence:
        table[y * size + x] = char
        x = (x + 1) % size
        if x == 0:
            y = (y + 1) % size

# Funkcja szyfrowania do szyfrogramu
def encrypt_to_scyphrogram(pre_encrypted_text, white_key, black_key, chars):
    table_size = int(math.sqrt(10000))  # Rozmiar tablicy
    tables = []
    sequences = [pre_encrypted_text[i:i + 10] for i in range(0, len(pre_encrypted_text), 10)]

    for i, seq in enumerate(sequences):
        table = generate_table(table_size, chars)
        opal = get_coordinates(black_key[i % len(black_key)], white_key[i % len(white_key)], chars, table_size)
        iryd = get_coordinates(black_key[(i + 1) % len(black_key)], white_key[(i + 1) % len(white_key)], chars, table_size)
        embed_sequence(table, seq, opal, iryd, table_size)
        tables.append(''.join(table))

    return ''.join(tables)

# Funkcja deszyfrująca z szyfrogramu
def decrypt_from_scyphrogram(scyphrogram, white_key, black_key, chars):
    table_size = int(math.sqrt(10000))  # Rozmiar tablicy
    tables = [scyphrogram[i:i + 10000] for i in range(0, len(scyphrogram), 10000)]
    decrypted_sequences = []

    for i, table_data in enumerate(tables):
        table = list(table_data)
        opal = get_coordinates(black_key[i % len(black_key)], white_key[i % len(white_key)], chars, table_size)
        iryd = get_coordinates(black_key[(i + 1) % len(black_key)], white_key[(i + 1) % len(white_key)], chars, table_size)

        # Wyciąganie sekwencji z tablicy
        sequence = []
        x, y = opal, iryd
        for _ in range(10):  # Maksymalnie 10 znaków
            sequence.append(table[y * table_size + x])
            x = (x + 1) % table_size
            if x == 0:
                y = (y + 1) % table_size
        decrypted_sequences.append(''.join(sequence))

    return ''.join(decrypted_sequences)

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

        # Szyfrowanie wstępne
        pre_encrypted = encrypt_text(text, white_key, black_key, chars)

        # Szyfrowanie do szyfrogramu
        scyphrogram = encrypt_to_scyphrogram(pre_encrypted, white_key, black_key, chars)

        # Wyświetlenie wyników
        print("\nWyniki szyfrowania:")
        print(f"Klucz biały: {white_key}")
        print(f"Szyfrogram: {scyphrogram}")

    elif choice == "2":  # Odszyfrowanie
        white_key = input("Wprowadź klucz biały: ").lower()
        white_key = ''.join(filter(lambda x: x in chars, white_key))  # Filtracja znaków

        if not white_key:
            print("Klucz biały nie może być pusty!")
            return

        scyphrogram = input("Wprowadź szyfrogram do odszyfrowania: ").lower()

        if not scyphrogram:
            print("Szyfrogram nie może być pusty!")
            return

        # Deszyfrowanie z szyfrogramu
        pre_decrypted = decrypt_from_scyphrogram(scyphrogram, white_key, black_key, chars)

        # Wyświetlenie wyników
        print("\nWyniki odszyfrowania:")
        print(f"Tekst odszyfrowany: {pre_decrypted}")

# Uruchomienie programu
if __name__ == "__main__":
    main()
