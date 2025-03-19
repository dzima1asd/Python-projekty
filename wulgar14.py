import speech_recognition as sr
import time
import subprocess  # Dodajemy import subprocess do wywołania termux-vibrate
import re

# Lista wulgaryzmów
wulgaryzmy = ['kurwa', 'kurwica', 'kurwić', 'kurwi', 'kurwiłem', 'kurwiła', 'kurwą', 'kurwić',
    'jebany', 'jebać', 'jebał', 'jebany', 'pierdolić', 'pierdoli', 'pierdolenie',
    'spierdalać', 'spierdalac', 'zajebisty', 'zajebie', 'zajebał', 'zajebana', 'zajebać',
    'suka', 'zjebany', 'sukinsyn', 'sukinsyny', 'spieprzać', 'spieprzac', 'spieprza',
    'spieprzał', 'spieprzal', 'spieprzała', 'spieprzala', 'spieprzaj', 'spieprzajcie',
    'spieprzają', 'spieprzaja', 'spieprzający', 'spieprzajacy', 'spieprzająca', 'spieprzajaca',
    'spierdolić', 'spierdolic', 'spierdoli', 'spierdoliła', 'spierdoliło', 'spierdolą',
    'spierdola', 'srać', 'srac', 'srający', 'srajacy', 'srając', 'srajac', 'sraj', 'sukinsyn',
    'sukinsyny', 'sukinsynom', 'sukinsynowi', 'sukinsynów', 'sukinsynow', 'śmierdziel', 'udupić',
    'ujebać', 'ujebac', 'ujebał', 'ujebal', 'ujebana', 'ujebany', 'ujebie', 'ujebała', 'ujebala',
    'upierdalać', 'upierdalac', 'upierdala', 'upierdoli', 'upierdolić', 'upierdolic', 'upierdoli',
    'upierdola', 'upierdoleni', 'wjebać', 'wjebac', 'wjebie', 'wjebią', 'wjebia', 'wjebiemy',
    'wjebiecie', 'wkurwiać', 'wkurwiac', 'wkurwi', 'wkurwia', 'wkurwiał', 'wkurwial', 'wkurwiający',
    'wkurwiajacy', 'wkurwiająca', 'wkurwiajaca', 'wkurwić', 'wkurwic', 'wkurwi', 'wkurwiacie',
    'wkurwiają', 'wkurwiali', 'wkurwią', 'wkurwia', 'wkurwimy', 'wkurwicie', 'wkurwiacie',
    'wkurwić', 'wkurwic', 'wkurwia', 'wpierdalać', 'wpierdalac', 'wpierdalający', 'wpierdalajacy',
    'wpierdol', 'wpierdolić', 'wpierdolic', 'wpierdolą', 'wpierdola', 'zapierdala', 'zapierdalać',
    'zapierdalac', 'zapierdalaja', 'zapierdalał', 'zapierdalal', 'zapierdalała', 'zapierdalala',
    'zapierdalali', 'zapierdalający', 'zapierdalajacy', 'zapierdolić', 'zapierdolic', 'zapierdoli',
    'zapierdolił', 'zapierdolil', 'zapierdoliła', 'zapierdolila', 'zapierdolą', 'zapierdola',
    'zapierniczać', 'zapierniczający', 'zasrać', 'zasranym', 'zasrywać', 'zasrywający', 'zesrywać',
    'zesrywający', 'zjebać', 'zjebac', 'zjebał', 'zjebal', 'zjebła', 'zjebala', 'zjebana', 'zjebią',
    'zjebali', 'zjeby', 'cipa', 'cipka', 'cipuś', 'cipsia', 'ciota', 'ciotka', 'ciotowaty', 'chuj',
    'chuje', 'chujowy', 'chujnia', 'chujniach', 'chujowa', 'chujek', 'chujowo', 'chujowo', 'chuj',
    'kurwić', 'kurwiak', 'kutas', 'kutasy', 'kurwiarz', 'kurwica', 'kutas', 'kurwa', 'kurwica',
    'kozojeb', 'wypierdalaj', 'kurwicha', 'dziwka', 'pizda', 'pieprz mnie', 'pieprzyć', 'obciągać', 'obciągnij', 'fiut', 'ruchać','wyruchaj', 'wyruchać,']

# Inicjalizujemy licznik wykrytych wulgaryzmów
liczba_wulgaryzmów = 0
wykryte_wulgaryzmy = []

# Funkcja do wibracji
def wibracja():
    subprocess.run(['termux-vibrate', '-d', '1000'])  # Wykorzystujemy termux-vibrate do wibracji przez 1 sekundę

# Funkcja do rozpoznawania mowy
def rozpoznaj_mowe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Czekam na nagranie...")
        audio = recognizer.listen(source)
        print("Rozpoznaję tekst...")
        try:
            text = recognizer.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznany tekst: {text}")
            return text.lower()  # Zamieniamy na małe litery, aby porównanie było niewrażliwe na wielkość liter
        except sr.UnknownValueError:
            print("Nie udało się rozpoznać mowy.")
            return None
        except sr.RequestError:
            print("Błąd połączenia z API rozpoznawania mowy.")
            return None

# Główna pętla programu
print("Program rozpoczął działanie. Powiedz 'koniec koniec', aby zakończyć.")
while True:
    rozpoznany_tekst = rozpoznaj_mowe()
    
    if rozpoznany_tekst:
        if "koniec koniec" in rozpoznany_tekst:
            print("Polecenie zakończenia programu wykryte. Kończę działanie.")
            break
        
        # Sprawdzamy, czy rozpoznany tekst zawiera wulgaryzm
        for wulgaryzm in wulgaryzmy:
            if wulgaryzm in rozpoznany_tekst:
                print(f"Wykryto wulgaryzm: {wulgaryzm}")
                wibracja()  # Wywołujemy funkcję wibracji
                liczba_wulgaryzmów += 1
                wykryte_wulgaryzmy.append(wulgaryzm)
                break  # Po wykryciu pierwszego wulgaryzmu przechodzimy do kolejnego nagrania
    
    # Pokazujemy wyniki
    print(f"Liczba wykrytych wulgarnych słów: {liczba_wulgaryzmów}")
    print("Lista wykrytych wulgaryzmów:", wykryte_wulgaryzmy)

    time.sleep(1)  # Krótkie opóźnienie przed kolejnym nagraniem
