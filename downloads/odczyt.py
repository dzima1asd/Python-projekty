import androidhelper
import time

# Inicjalizacja Androida (SL4A)
droid = androidhelper.Android()

# Funkcja do odczytu sygnału światła
def read_light_sensor():
    light = droid.sensorsGetLight().result
    return light

# Funkcja do detekcji sekwencji Morse'a
def detect_morse():
    # Zmienna do przechowywania wyników
    morse_code = []
    last_light = None
    last_time = time.time()

    # Progi detekcji
    threshold_on = 50  # Światło
    threshold_off = 20  # Brak światła

    try:
        while True:
            current_light = read_light_sensor()
            current_time = time.time()

            if current_light > threshold_on and (last_light is None or last_light <= threshold_off):
                # Zaczynamy wykrywać światło (kropka lub kreska)
                last_time = current_time
                morse_code.append(1)  # Światło
            elif current_light <= threshold_off and last_light is not None and last_light > threshold_on:
                # Kończymy wykrywanie światła (końcówka kropki lub kreski)
                duration = current_time - last_time
                if duration < 0.4:
                    morse_code.append('.')
                else:
                    morse_code.append('-')
                
            last_light = current_light
            time.sleep(0.1)  # Czekamy, aby nie męczyć sensora

    except KeyboardInterrupt:
        # Kończymy po naciśnięciu ctrl+c
        print("Detected Morse code:", "".join(morse_code))
        return morse_code

# Słownik alfabetu Morse'a
MORSE_DICT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
    '---..': '8', '----.': '9'
}

# Funkcja do tłumaczenia Morse'a na tekst
def morse_to_text(morse_code):
    words = morse_code.split('   ')  # Przerwa między słowami to 3 spacje
    decoded_message = ''
    for word in words:
        letters = word.split()
        for letter in letters:
            decoded_message += MORSE_DICT.get(letter, '?')  # Zamień kod na literę
        decoded_message += ' '
    return decoded_message.strip()

# Główna funkcja
def main():
    print("Start detekcji Morse'a. Naciśnij Ctrl+C, aby zakończyć.")
    morse_code = detect_morse()
    morse_string = ''.join(morse_code)
    print("Detected Morse code:", morse_string)
    text_message = morse_to_text(morse_string)
    print("Decoded message:", text_message)

if __name__ == "__main__":
    main()
