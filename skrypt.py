import requests
import json
import os
import unicodedata
import time

DANE_PLIK = "dane.json"

def usun_polskie_znaki(tekst):
    return ''.join(c for c in unicodedata.normalize('NFKD', tekst) if ord(c) < 128)

def pobierz_wspolrzedne(miasto):
    miasto_clean = usun_polskie_znaki(miasto)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={miasto_clean}&count=1&format=json"

    for _ in range(2):  
        try:
            odpowiedz = requests.get(url, timeout=5)
            odpowiedz.raise_for_status()
            dane = odpowiedz.json()

            if "results" in dane and len(dane["results"]) > 0:
                lat = dane["results"][0]["latitude"]
                lon = dane["results"][0]["longitude"]
                return lat, lon
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania danych: {e}")

        time.sleep(1)  

    print("Nie znaleziono miasta.")
    return None, None

def pobierz_pogode(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        odpowiedz = requests.get(url, timeout=5)
        odpowiedz.raise_for_status()
        dane = odpowiedz.json()

        if "current_weather" in dane:
            temperatura = dane["current_weather"]["temperature"]
            return temperatura
    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas pobierania pogody: {e}")

    return None

def zapisz_do_pliku(dane):
    try:
        if os.path.exists(DANE_PLIK):
            with open(DANE_PLIK, "r") as plik:
                istniejące_dane = json.load(plik)
                if not isinstance(istniejące_dane, list):
                    istniejące_dane = []
        else:
            istniejące_dane = []
    except (json.JSONDecodeError, FileNotFoundError):
        istniejące_dane = []

    istniejące_dane.append(dane)

    with open(DANE_PLIK, "w") as plik:
        json.dump(istniejące_dane, plik, indent=4)

def interaktywny_tryb():
    while True:
        miasto = input("Podaj nazwę miasta (lub 'q' aby wyjść): ").strip()
        if miasto.lower() == 'q':
            print("Zamykanie programu...")
            break

        lat, lon = pobierz_wspolrzedne(miasto)
        if lat is None or lon is None:
            continue

        temperatura = pobierz_pogode(lat, lon)
        if temperatura is not None:
            print(f"Aktualna temperatura w {miasto}: {temperatura}°C")
            zapisz_do_pliku({"miasto": miasto, "temperatura": temperatura})
        else:
            print("Nie udało się pobrać temperatury.")

if __name__ == "__main__":
    interaktywny_tryb()
