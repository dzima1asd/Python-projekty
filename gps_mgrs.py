import os
import json
import time
import mgrs  # Biblioteka do konwersji MGRS
import subprocess

def get_gps():
    try:
        result = os.popen("termux-location").read().strip()
        if not result:
            raise Exception("Błąd GPS! Sprawdź uprawnienia Termux!")
        data = json.loads(result)
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat is None or lon is None:
            raise Exception("Brak danych GPS w odpowiedzi.")
        return lat, lon
    except json.JSONDecodeError:
        raise Exception(f"Błąd parsowania JSON: {result}")
    except Exception as e:
        raise Exception(f"Błąd podczas pobierania GPS: {str(e)}")

def latlon_to_mgrs(lat, lon):
    try:
        m = mgrs.MGRS()
        mgrs_coord = m.toMGRS(lat, lon)
        # Rozdzielamy część strefy (np. "34UFC") i współrzędne
        mgrs_zone = mgrs_coord[:5]  # Strefa MGRS (np. 34UFC)
        easting = mgrs_coord[5:10]  # Część wschodnią
        northing = mgrs_coord[10:]  # Część północną
        
        # Zaokrąglamy tylko na poziomie easting i northing, reszta pozostaje
        easting = easting[:5]  # Zaokrąglamy do 5 cyfr
        northing = northing[:5]  # Zaokrąglamy do 5 cyfr
        
        # Formatowanie MGRS bez kropek, z zaokrąglonymi wartościami
        mgrs_coord_formatted = f"{mgrs_zone} {easting} {northing}"
        return mgrs_coord_formatted
    except Exception as e:
        raise Exception(f"Błąd konwersji GPS na MGRS: {str(e)}")

def mgrs_to_latlon(mgrs_str):
    try:
        m = mgrs.MGRS()
        lat, lon = m.toLatLon(mgrs_str)
        
        # Logowanie przed zwróceniem wyników
        print(f"Konwertowane z MGRS: {mgrs_str} na GPS: {lat}, {lon}")
        return lat, lon
    except Exception as e:
        raise Exception(f"Błąd konwersji MGRS na GPS: {str(e)}")

def open_google_maps(lat, lon):
    try:
        # Logowanie przed otwarciem map
        print(f"Otwieram Google Maps z GPS: {lat}, {lon}")
        subprocess.run(["termux-open-url", f"geo:{lat},{lon}"], check=False)
    except Exception as e:
        print(f"Nie udało się otworzyć Google Maps: {str(e)}")

def main():
    try:
        print("\033[32m=== MGRS Konwerter GPS ===")
        while True:
            try:
                # Pobierz współrzędne GPS
                lat, lon = get_gps()
                print(f"\033[1;32mPobrano współrzędne GPS: {lat}, {lon}\033[0m")

                # Konwertuj na MGRS
                mgrs_coord = latlon_to_mgrs(lat, lon)
                os.system("clear")
                print(f"\033[1;32mAktualna pozycja MGRS: {mgrs_coord}\033[0m")

                # Wprowadź współrzędne MGRS od użytkownika
                user_input = input("\nPodaj MGRS (np. 34UFC 12345 67890): ")
                user_input = user_input.strip().replace(" ", "")  # Usuwamy niepotrzebne spacje
                lat_conv, lon_conv = mgrs_to_latlon(user_input)
                print(f"Konwertowane współrzędne GPS: {lat_conv}, {lon_conv}")

                # Otwórz Google Maps
                print("Otwieram Maps...")
                open_google_maps(lat_conv, lon_conv)

                # Poczekaj 5 sekund przed kolejnym odświeżeniem
                time.sleep(5)
            except KeyboardInterrupt:
                print("\nZakończono działanie programu.")
                break
            except Exception as e:
                print(f"\033[31mBłąd: {str(e)}\033[0m")
                time.sleep(5)  # Poczekaj przed ponowną próbą
    except Exception as e:
        print(f"\033[31mKrytyczny błąd: {str(e)}\033[0m")

if __name__ == "__main__":
    main()

