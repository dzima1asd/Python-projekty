import os
import re
import requests
import time
import mgrs  # Dodajemy bibliotekę MGRS

def expand_short_url(short_url):
    """Rozwija skrócony link i zwraca finalny URL oraz HTML."""
    try:
        print(f"\033[34m[DEBUG] Rozpoczynam rozwijanie linku: {short_url}\033[0m")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(short_url, headers=headers, allow_redirects=True)
        final_url = response.url
        html = response.text
        print(f"\033[34m[DEBUG] Liczba przekierowań: {len(response.history)}\033[0m")
        print(f"\033[34m[DEBUG] Finalny URL: {final_url}\033[0m")
        print(f"\033[34m[DEBUG] Rozmiar HTML: {len(html)} znaków\033[0m")
        return final_url, html
    except Exception as e:
        print(f"\033[31mBŁĄD: Nie udało się rozwinąć linku. Powód: {e}\033[0m")
        return None, None

def extract_coordinates(url):
    """Główna funkcja wyodrębniająca współrzędne, z poprawką na wybór właściwych danych."""
    print(f"\n\033[34m{'='*50}\033[0m")
    print(f"\033[34m[DEBUG] Przetwarzam link: {url}\033[0m")

    # Jeśli link jest skrócony
    if "goo.gl" in url or "maps.app.goo.gl" in url:
        print("\033[34m[DEBUG] To jest link skrócony. Rozwijam...\033[0m")
        final_url, html = expand_short_url(url)
        if not final_url:
            print("\033[31m[DEBUG] Nie udało się rozwinąć linku.\033[0m")
            return None, None

        # Zapis HTML do analizy
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\033[34m[DEBUG] Zapisano HTML do pliku 'debug_page.html'.\033[0m")

        # Krok 1: Szukamy wzorca "@" w URL-u
        print("\033[34m[DEBUG] Szukam współrzędnych w finalnym URL (wzorzec '@')...\033[0m")
        url_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if url_match:
            lat = float(url_match.group(1))
            lon = float(url_match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                print(f"\033[32m[SUKCES] Znaleziono w URL: lat={lat}, lon={lon}\033[0m")
                return lat, lon
            else:
                print(f"\033[34m[DEBUG] Współrzędne z '@' nie mieszczą się w Polsce: lat={lat}, lon={lon}\033[0m")

        # Krok 2: Szukamy wzorca "!3d...!4d..." w URL-u
        print("\033[34m[DEBUG] Szukam współrzędnych w finalnym URL (wzorzec '!3d...!4d...')...\033[0m")
        url_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if url_match:
            lat = float(url_match.group(1))
            lon = float(url_match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                print(f"\033[32m[SUKCES] Znaleziono w URL: lat={lat}, lon={lon}\033[0m")
                return lat, lon
            else:
                print(f"\033[34m[DEBUG] Współrzędne z '!3d' nie mieszczą się w Polsce: lat={lat}, lon={lon}\033[0m")

        # Krok 3: Szukamy współrzędnych w meta tagach i danych JSON
        print("\033[34m[DEBUG] Szukam w meta tagach i danych JSON...\033[0m")
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
                    print(f"\033[32m[SUKCES] Znaleziono wzorcem: {pattern}\033[0m")
                    print(f"\033[32m        lat={lat}, lon={lon}\033[0m")
                    return lat, lon
                else:
                    print(f"\033[34m[DEBUG] Wzorzec {pattern} dał współrzędne nie mieszczące się w Polsce: lat={lat}, lon={lon}\033[0m")

        # Krok 4: Szukamy dowolnych współrzędnych w treści HTML
        print("\033[34m[DEBUG] Szukam dowolnych współrzędnych w treści...\033[0m")
        coord_pattern = r'\b(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)\b'
        matches = re.findall(coord_pattern, html)
        if matches:
            print(f"\033[34m[DEBUG] Znaleziono {len(matches)} potencjalnych współrzędnych:\033[0m")
            valid_coords = []
            for i, (lat_str, lon_str) in enumerate(matches, 1):
                lat_val = float(lat_str)
                lon_val = float(lon_str)
                print(f"  {i}. lat={lat_val}, lon={lon_val}")
                if 49 <= lat_val <= 55 and 14 <= lon_val <= 24:
                    valid_coords.append((lat_val, lon_val))
            if valid_coords:
                chosen = valid_coords[0]
                print(f"\033[32m[SUKCES] Wybrano współrzędne: lat={chosen[0]}, lon={chosen[1]}\033[0m")
                return chosen
            else:
                print("\033[34m[DEBUG] Żadne znalezione współrzędne nie mieszczą się w Polsce.\033[0m")
                lat_val, lon_val = float(matches[0][0]), float(matches[0][1])
                print(f"\033[34m[DEBUG] Używam pierwszych znalezionych: lat={lat_val}, lon={lon_val}\033[0m")
                return lat_val, lon_val

        print("\033[31m[DEBUG] Nie znaleziono żadnych współrzędnych.\033[0m")
        return None, None

    else:
        # Link bezpośredni
        print("\033[34m[DEBUG] To jest link bezpośredni. Przetwarzam...\033[0m")
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                print(f"\033[32m[SUKCES] Znaleziono w URL: lat={lat}, lon={lon}\033[0m")
                return lat, lon
            else:
                print(f"\033[34m[DEBUG] Współrzędne nie mieszczą się w Polsce: lat={lat}, lon={lon}\033[0m")
        print("\033[31m[DEBUG] Nieprawidłowy format linku.\033[0m")
        return None, None

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
        print(f"\033[32m[SUKCES] Wynik MGRS: {mgrs_coord_formatted}\033[0m")
        return mgrs_coord_formatted
    except Exception as e:
        print(f"\033[31mBŁĄD KONWERSJI: {e}\033[0m")
        return None

def main():
    try:
        print("\033[32m=== Konwersja Google Maps -> MGRS ===\033[0m")
        while True:
            url = input("\n\033[33mWklej link Google Maps: \033[0m")
            lat, lon = extract_coordinates(url)
            if lat is not None and lon is not None:
                mgrs_coord = latlon_to_mgrs(lat, lon)
                if mgrs_coord:
                    os.system("clear")
                    print(f"\n\033[1;32mPozycja MGRS: {mgrs_coord}\033[0m\n")
                else:
                    print("\033[31mNie udało się przekonwertować współrzędnych.\033[0m")
            else:
                print("\033[31mNie znaleziono współrzędnych w linku.\033[0m")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\033[0m\nProgram zakończony.")
    except Exception as e:
        print(f"\033[31mKRYTYCZNY BŁĄD: {e}\033[0m")

if __name__ == "__main__":
    main()
