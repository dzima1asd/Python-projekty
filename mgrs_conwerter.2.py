import os
import re
import json
import time
import requests
import mgrs
import subprocess
from urllib.parse import unquote_plus
import unicodedata

# Lista do przechowywania historii przetworzonych linków i pinezek
history = []

# Zbiór kodów krajów wymagających podwójnego dekodowania
DOUBLE_DECODE_COUNTRIES = {
    "at",  # Austria
    "be",  # Belgia
    "ad",  # Andora
    "am",  # Armenia
    "ba",  # Bośnia i Hercegowina
    "bg",  # Bułgaria
    "hr",  # Chorwacja
    "cy",  # Cypr
    "ee",  # Estonia
    "is",  # Islandia
    "xk",  # Kosovo
    "lv",  # Łotwa
    "li",  # Liechtenstein
    "lt",  # Litwa
    "lu",  # Luksemburg
    "mk",  # Macedonia (Północna Macedonia)
    "mt",  # Malta
    "md",  # Mołdawia
    "me",  # Czarnogóra
    "nl",  # Niderlandy
    "rs",  # Serbia
    "sk",  # Słowacja
    "si",  # Słowenia
    "ua",  # Ukraina
    "by",  # Białoruś
}

def double_decode(s, encoding='utf-8', max_iter=5):
    """Dekoduje ciąg percent-encoded wielokrotnie, aż wynik się ustabilizuje."""
    prev = s
    for _ in range(max_iter):
        decoded = unquote_plus(prev, encoding=encoding)
        if decoded == prev:
            break
        prev = decoded
    return prev

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
        mgrs_zone = mgrs_coord[:5]
        easting = mgrs_coord[5:10]
        northing = mgrs_coord[10:]
        return f"{mgrs_zone} {easting} {northing}"
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
        # Przekierowanie stderr do /dev/null, aby ukryć komunikaty systemowe
        with open(os.devnull, 'w') as devnull:
            subprocess.run(
                ["termux-open-url", f"geo:{lat},{lon}"],
                check=False,
                stderr=devnull  # Ukryj komunikaty błędów
            )
    except Exception as e:
        print(f"Nie udało się otworzyć Google Maps: {str(e)}")

def expand_short_url(short_url):
    """Rozwija skrócony link i zwraca finalny URL oraz HTML."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(short_url, headers=headers, allow_redirects=True)
        return response.url, response.text
    except Exception as e:
        print(f"\033[31mBŁĄD: Nie udało się rozwinąć linku. Powód: {e}\033[0m")
        return None, None

def detect_country_code(place_name):
    """
    Wykrywa kod kraju na podstawie jawnych fraz oraz analizy znaków diakrytycznych.
    Rozszerzony słownik obejmuje kraje europejskie.
    """
    normalized = unicodedata.normalize('NFKC', place_name.lower())
    if "francja" in normalized or "france" in normalized:
        return "fr"
    if "niemcy" in normalized or "germany" in normalized:
        return "de"
    if "białoruś" in normalized or "belarus" in normalized:
        return "by"
    if "ukraina" in normalized or "ukraine" in normalized:
        return "ua"
    if "česká" in normalized or "česk" in normalized or "czech" in normalized:
        return "cz"
    if "słowacja" in normalized or "slovakia" in normalized:
        return "sk"
    if "polska" in normalized or "poland" in normalized:
        return "pl"
    if "hiszpania" in normalized or "spain" in normalized:
        return "es"
    if "włochy" in normalized or "italy" in normalized:
        return "it"
    if "finland" in normalized or "suomi" in normalized or "finlandia" in normalized:
        return "fi"
    if "szwecja" in normalized or "sweden" in normalized:
        return "se"
    if "norwegia" in normalized or "norway" in normalized:
        return "no"
    if "dania" in normalized or "denmark" in normalized:
        return "dk"
    if "portugalia" in normalized or "portugal" in normalized:
        return "pt"
    if "rumunia" in normalized or "romania" in normalized:
        return "ro"
    if "turcja" in normalized or "turkey" in normalized:
        return "tr"
    if "wielka brytania" in normalized or "united kingdom" in normalized:
        return "gb"
    if "irlandia" in normalized or "ireland" in normalized:
        return "ie"
    if "kosovo" in normalized:
        return "xk"
    if "łotwa" in normalized or "ļotwa" in normalized or "latvia" in normalized:
        return "lv"
    # Fallback: analiza znaków diakrytycznych
    country_chars = {
        "pl": set("ąćęłńóśźż"),
        "cz": set("čřžěšů"),
        "hu": set("áéíóöőúüű"),
        "de": set("äöüß"),
        "fr": set("àâçéèêëîïôùûüÿ"),
        "es": set("ñáéíóúü"),
        "it": set("àèìòù"),
        "fi": set("äö"),
        "se": set("åäö"),
        "dk": set("æøå"),
        "no": set("æøå"),
        "pt": set("ãáâçéíóôõú"),
        "ro": set("ăâîșț"),
        "tr": set("çğıöşü"),
        "lv": set("āēīūčģķļņšž")
    }
    scores = {}
    for code, chars in country_chars.items():
        score = sum(1 for ch in normalized if ch in chars)
        if score > 0:
            scores[code] = score
    if scores:
        best = max(scores.items(), key=lambda x: x[1])[0]
        return best
    return None

def clean_place_name(place_name, country):
    """Czyszczenie nazwy miejsca dla specyficznych krajów."""
    if country == "lv":
        # Dla Łotwy: usuń kod pocztowy, np. LV-4801, oraz słowa 'gmina' i 'parish'
        place_name = re.sub(r'\bLV-\d{4}\b', '', place_name, flags=re.IGNORECASE)
        place_name = re.sub(r'\bgmina\b', '', place_name, flags=re.IGNORECASE)
        place_name = re.sub(r'\bparish\b', '', place_name, flags=re.IGNORECASE)
        place_name = re.sub(r',\s*,', ',', place_name)
        place_name = re.sub(r'\s+', ' ', place_name)
        place_name = place_name.strip(' ,')
    elif country in ("cz", "sk"):
        # Dla Czech i Słowacji: usuń typowy kod pocztowy (5 cyfr z opcjonalną spacją)
        place_name = re.sub(r'\b\d{3}\s?\d{2}\b', '', place_name)
        # Rozdziel wg przecinków i wybierz pierwszy fragment, który nie zawiera cyfr
        parts = [p.strip() for p in place_name.split(",") if not re.search(r'\d', p)]
        if parts:
            place_name = parts[0]
        place_name = place_name.strip(' ,')
    return place_name

def geocode_place(place_name):
    """Geokodowanie przy pomocy Nominatim OpenStreetMap.
       Ustawia parametr countrycodes dynamicznie na podstawie wykrytego kraju.
       Dla Finlandii używa 'fi,sv'."""
    #print("DEBUG: Geokodowanie nazwy miejsca:", place_name)
    url = "https://nominatim.openstreetmap.org/search"
    country_code = detect_country_code(place_name)
    params = {"q": place_name, "format": "json", "limit": 1}
    if country_code:
        if country_code == "fi":
            params["countrycodes"] = "fi,sv"
            #print("DEBUG: Ustawiono countrycodes: fi,sv")
        else:
            params["countrycodes"] = country_code
            #print("DEBUG: Ustawiono countrycodes:", country_code)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MyApp/1.0)", "Accept-Language": "en"}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            #print("DEBUG: Wynik geokodowania:", lat, lon)
            return lat, lon
        #print("DEBUG: Geokodowanie nie zwróciło poprawnych współrzędnych.")
    except Exception as e:
        #print("DEBUG: Błąd geokodowania:", e)
        pass
    return None, None

def extract_coordinates(url):
    """
    Wyodrębnia współrzędne z linku Google Maps.
    Jeśli nie uda się bezpośrednio uzyskać współrzędnych, wyłuskuje nazwę miejsca (fragment po '/place/')
    i stosuje wielokrotne dekodowanie oraz czyszczenie dla krajów wymagających tego mechanizmu.
    """
    if "goo.gl" in url or "maps.app.goo.gl" in url:
        final_url, html = expand_short_url(url)
        if not final_url:
            return None, None

        # Krok 1: Szukamy wzorca "@lat,lon" w URL-u
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon

        # Krok 2: Szukamy wzorca "!3dlat!4dlon" w URL-u
        m = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon

        # Krok 3: Próba dodatkowych wzorców (w URL i HTML)
        patterns = [
            r'center=(-?\d+\.\d+),(-?\d+\.\d+)',
            r'\?q=(-?\d+\.\d+),(-?\d+\.\d+)',
            r'[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)',
            r'[?&]sll=(-?\d+\.\d+),(-?\d+\.\d+)',
            r'"latitude"\s*:\s*(-?\d+\.\d+)[,}]',
            r'"lat"\s*:\s*(-?\d+\.\d+)[,}]',
            r'name="geo.position"\s+content="(-?\d+\.\d+);(-?\d+\.\d+)"',
            r'data-lat="(-?\d+\.\d+)"\s+data-lng="(-?\d+\.\d+)"',
            r'GPS">\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*<',
        ]
        for pattern in patterns:
            m = re.search(pattern, final_url)
            if m and m.lastindex >= 2:
                lat, lon = float(m.group(1)), float(m.group(2))
                if 49 <= lat <= 55 and 14 <= lon <= 24:
                    return lat, lon
            m = re.search(pattern, html)
            if m and m.lastindex >= 2:
                lat, lon = float(m.group(1)), float(m.group(2))
                if 49 <= lat <= 55 and 14 <= lon <= 24:
                    return lat, lon

        # Krok 4: Fallback – przeszukujemy HTML w poszukiwaniu par współrzędnych
        coord_pattern = r'\b(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)\b'
        matches = re.findall(coord_pattern, html)
        for lat_str, lon_str in matches:
            lat_val, lon_val = float(lat_str), float(lon_str)
            if 49 <= lat_val <= 55 and 14 <= lon_val <= 24:
                return lat_val, lon_val

        # Krok 5: Jeśli nadal nic nie działa – wyłuskujemy nazwę miejsca z URL (po '/place/')
        m = re.search(r'/place/([^/@?]+)', final_url)
        if m:
            raw_name = m.group(1)
            # Używamy double_decode do wielokrotnego odszyfrowania
            place_name = double_decode(raw_name, encoding='utf-8')
            place_name = unicodedata.normalize('NFKC', place_name)
            country = detect_country_code(place_name)
            if country in DOUBLE_DECODE_COUNTRIES:
                place_name = clean_place_name(place_name, country)
            #print("DEBUG: Wyekstrahowana nazwa miejsca:", place_name)
            coords = geocode_place(place_name)
            if coords:
                return coords
        return None, None
    else:
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if 49 <= lat <= 55 and 14 <= lon <= 24:
                return lat, lon
        return None, None

def main():
    import sys

    print("\033[1;34m=== Konwerter GPS <-> MGRS ===\033[0m")

    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Przetwarzam link: {url}")
        lat, lon = extract_coordinates(url)
        if lat and lon:
            mgrs_coord = latlon_to_mgrs(lat, lon)
            history.append(("Przesłana pinezka", mgrs_coord))
            print(f"\033[1;34mPozycja MGRS: \033[1;32m{mgrs_coord}\033[0m")

    try:
        lat, lon = get_gps()
        mgrs_coord = latlon_to_mgrs(lat, lon)
        print(f"\033[1;34mAktualna pozycja MGRS: \033[1;32m{mgrs_coord}\033[0m")

        print("\n\033[33mWprowadź dane w jednym polu:")
        print("   • Jeśli podasz współrzędne MGRS (np. 33UWU 30571 27454), otworzy się Google Maps.")
        print("   • Jeśli wkleisz link z Google Maps, program rozpozna go i przeliczy na MGRS.")
        print("   • Możesz też wysłać tu pinezkę z Google Maps.\033[0m")

        if history:
            print("\nHistoria przetworzonych danych:")
            for i, (typ, dane) in enumerate(history, 1):
                print(f"{i}. {typ}: {dane}")

        while True:
            user_input = input("\n\033[33mWprowadź dane (lub 'q' aby wyjść): \033[0m").strip()
            if user_input.lower() == 'q':
                print("\033[0m\nProgram zakończony.")
                break

            if re.match(r'^\d{2}[A-Z]{3}\s*\d{5}\s*\d{5}$', user_input.replace(" ", "")):
                lat, lon = mgrs_to_latlon(user_input.replace(" ", ""))
                if lat and lon:
                    open_google_maps(lat, lon)
                    history.append(("Wklejony link", user_input))
            elif "google.com/maps" in user_input or "goo.gl" in user_input or "maps.app.goo.gl" in user_input:
                lat, lon = extract_coordinates(user_input)
                if lat and lon:
                    mgrs_coord = latlon_to_mgrs(lat, lon)
                    print(f"\033[1;34mPozycja MGRS: \033[1;32m{mgrs_coord}\033[0m")
                    history.append(("Wklejony link", mgrs_coord))
                else:
                    print("\033[31mNie udało się wyodrębnić poprawnych współrzędnych.\033[0m")
            else:
                print("\033[31mNieprawidłowy format danych.\033[0m")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\033[0m\nProgram zakończony.")
    except Exception as e:
        print(f"\033[31mKRYTYCZNY BŁĄD: {e}\033[0m")

if __name__ == "__main__":
    main()
