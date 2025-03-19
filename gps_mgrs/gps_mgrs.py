import os
import re
import json
import time
import requests
import mgrs
import subprocess

def get_gps():
    """Pobiera aktualną pozycję GPS za pomocą Termux."""
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
    """Konwertuje współrzędne GPS na MGRS."""
    try:
        m = mgrs.MGRS()
        mgrs_coord = m.toMGRS(lat, lon)
        # Rozdzielamy część strefy (np. "34UFC") i współrzędne
        mgrs_zone = mgrs_coord[:5]  # Strefa MGRS (np. 34UFC)
        easting = mgrs_coord[5:10]  # Część wschodnią
        northing = mgrs_coord[10:]  # Część północną

        # Formatowanie MGRS bez kropek, z zaokrąglonymi wartościami
        mgrs_coord_formatted = f"{mgrs_zone} {easting} {northing}"
        return mgrs_coord_formatted
    except Exception as e:
        print(f"\033[31mBŁĄD KONWERSJI: {e}\033[0m")
        return None

def mgrs_to_latlon(mgrs_str):
    """Konwertuje współrzędne MGRS na GPS."""
    try:
        m = mgrs.MGRS()
        lat, lon = m.toLatLon(mgrs_str)
        return lat, lon
    except Exception as e:
        raise Exception(f"Błąd konwersji MGRS na GPS: {str(e)}")

def open_google_maps(lat, lon):
    """Otwiera Google Maps z podanymi współrzędnymi."""
    try:
        subprocess.run(["termux-open-url", f"geo:{lat},{lon}"], check=False)
    except Exception as e:
        print(f"Nie udało się otworzyć Google Maps: {str(e)}")

def expand_short_url(short_url):
    """Rozwija skrócony link i zwraca finalny URL oraz HTML."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(short_url, headers=headers, allow_redirects=True)
        final_url = response.url
        html = response.text
        return final_url, html
    except Exception as e:
        print(f"\033[31mBŁĄD: Nie udało się rozwinąć linku. Powód: {e}\033[0m")
        return None, None

def extract_coordinates(url):
    """Wyodrębnia współrzędne z linku Google Maps."""
    # Jeśli link jest skrócony
    if "goo.gl" in url or "maps.app.goo.gl" in url:
        final_url, html = expand_short_url(url)
        if not final_url:
            return None, None

        # Krok 1: Szukamy wzorca "@" w URL-u
        url_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if url_match:
            lat = float(url_match.group(1))
            lon = float(url_match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon

        # Krok 2: Szukamy wzorca "!3d...!4d..." w URL-u
        url_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if url_match:
            lat = float(url_match.group(1))
            lon = float(url_match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon

        # Krok 3: Szukamy współrzędnych w meta tagach i danych JSON
        patterns = [
            r'"latitude"\s*:\s*(-?\d+\.\d+),',
            r'"lat"\s*:\s*(-?\d+\.\d+),',
            r'name="geo.position"\s+content="(-?\d+\.\d+);(-?\d+\.\d+)"',
            r'data-lat="(-?\d+\.\d+)"\s+data-lng="(-?\d+\.\d+)"',
            r'GPS">\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*<',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if 49 <= lat <= 55 and 14 <= lon <= 24:
                    return lat, lon

        # Krok 4: Szukamy dowolnych współrzędnych w treści HTML
        coord_pattern = r'\b(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)\b'
        matches = re.findall(coord_pattern, html)
        if matches:
            valid_coords = []
            for lat_str, lon_str in matches:
                lat_val = float(lat_str)
                lon_val = float(lon_str)
                if 49 <= lat_val <= 55 and 14 <= lon_val <= 24:
                    valid_coords.append((lat_val, lon_val))
            if valid_coords:
                return valid_coords[0]
            else:
                return float(matches[0][0]), float(matches[0][1])

        return None, None

    else:
        # Link bezpośredni
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon
        return None, None

def main():
    try:
        # Pobierz aktualną pozycję GPS
        lat, lon = get_gps()
        mgrs_coord = latlon_to_mgrs(lat, lon)

        # Wyświetl aktualną pozycję MGRS
        print(f"\033[1;32mAktualna pozycja MGRS: {mgrs_coord}\033[0m")

        # Wyświetl komunikat pomocniczy
        print("\n\033[33mWprowadź dane w jednym polu:")
        print("   • Jeśli podasz współrzędne MGRS (np. 34UFC 80269 61320), otworzy się Google Maps.")
        print("   • Jeśli wkleisz link z Google Maps, program rozpozna go i przeliczy na MGRS.\033[0m")

        while True:
            user_input = input("\n\033[33mWprowadź dane: \033[0m").strip()

            # Sprawdź, czy to MGRS
            if re.match(r'^\d{2}[A-Z]{3}\s*\d{5}\s*\d{5}$', user_input.replace(" ", "")):
                lat, lon = mgrs_to_latlon(user_input.replace(" ", ""))
                if lat and lon:
                    open_google_maps(lat, lon)
            # Sprawdź, czy to link Google Maps
            elif "google.com/maps" in user_input or "goo.gl" in user_input or "maps.app.goo.gl" in user_input:
                lat, lon = extract_coordinates(user_input)
                if lat and lon:
                    mgrs_coord = latlon_to_mgrs(lat, lon)
                    print(f"\033[1;32mPozycja MGRS: {mgrs_coord}\033[0m")
            else:
                print("\033[31mNieprawidłowy format danych.\033[0m")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\033[0m\nProgram zakończony.")
    except Exception as e:
        print(f"\033[31mKRYTYCZNY BŁĄD: {e}\033[0m")

if __name__ == "__main__":
    main()
