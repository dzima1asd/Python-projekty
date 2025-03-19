import subprocess
import speech_recognition as sr
import time
from collections import deque

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
    'kozojeb', 'k**wa', 'kurwicha']

# Funkcja uruchamiająca wibracje w Termux
def uruchom_wibracje(czas):
    try:
        subprocess.run(["termux-vibrate", "-d", str(czas)])
    except Exception as e:
        print(f"Błąd podczas uruchamiania wibracji: {e}")

# Funkcja do analizy wykrytych słów
def analiza_wulgaryzmow(tekst, czasowe_wulgaryzmy, liczba_wulgaryzmow):
    wykryte = []
    for slowo in tekst.lower().split():
        if slowo in wulgaryzmy:
            wykryte.append(slowo)
            czasowe_wulgaryzmy.append((slowo, time.time()))
            liczba_wulgaryzmow.append(slowo)
            print(f"Wykryto wulgaryzm: {slowo}")

    # Usuwanie przeterminowanych wulgaryzmów
    while czasowe_wulgaryzmy and time.time() - czasowe_wulgaryzmy[0][1] > 180:
        czasowe_wulgaryzmy.popleft()

    # Wibracje w zależności od liczby wykrytych słów w czasie
    liczba_wulgaryzmow_czasowych = len(czasowe_wulgaryzmy)
    if liczba_wulgaryzmow_czasowych == 1:
        uruchom_wibracje(500)  # Wibracja x1
    elif liczba_wulgaryzmow_czasowych == 2:
        uruchom_wibracje(1000)  # Wibracja x2
    elif liczba_wulgaryzmow_czasowych == 3:
        uruchom_wibracje(1500)  # Wibracja x3
    elif liczba_wulgaryzmow_czasowych >= 5:
        uruchom_wibracje(3500)  # Wibracja x7

    return wykryte

# Główna pętla programu
def glowna_petla():
    rozpoznawanie = sr.Recognizer()
    czasowe_wulgaryzmy = deque()
    liczba_wulgaryzmow = []
    print("Program rozpoczął działanie. Powiedz 'koniec koniec', aby zakończyć.")

    try:
        while True:
            print("Czekam na nagranie...")
            with sr.Microphone() as source:
                audio = rozpoznawanie.listen(source)

            print("Rozpoznaję tekst...")
            try:
                tekst = rozpoznawanie.recognize_google(audio, language="pl-PL")
                print(f"Rozpoznany tekst: {tekst}")

                if "koniec koniec" in tekst.lower():
                    print("Polecenie zakończenia programu wykryte. Kończę działanie.")
                    break

                analiza_wulgaryzmow(tekst, czasowe_wulgaryzmy, liczba_wulgaryzmow)
            except sr.UnknownValueError:
                print("Nie udało się rozpoznać mowy.")
            except sr.RequestError as e:
                print(f"Błąd podczas połączenia z usługą rozpoznawania mowy: {e}")
    except KeyboardInterrupt:
        print("\nProgram przerwany ręcznie.")

    print("\nProgram zakończony.")
    print(f"Liczba wykrytych wulgarnych słów: {len(liczba_wulgaryzmow)}")
    print("Lista wykrytych wulgaryzmów:")
    for slowo in liczba_wulgaryzmow:
        print(slowo)

if __name__ == "__main__":
    glowna_petla()
