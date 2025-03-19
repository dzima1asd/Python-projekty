import re

# Lista polskich funkcji Excela i ich minimalna liczba argumentów
FUNKCJE_EXCEL = {
    "SUMA": 1, "ŚREDNIA": 1, "MAKS": 1, "MIN": 1, "JEŻELI": 3, "LUB": 1, "ORAZ": 1,
    "LICZ.JEŻELI": 2, "ZAOKR": 2, "ILE.NIEPUSTYCH": 1, "DŁ": 1, "FRAGMENT.TEKSTU": 3, 
    "ZŁĄCZ.TEKSTY": 2, "LEWY": 1, "PRAWY": 1, "SZUKAJ.TEKST": 2, "PODSTAW": 3, 
    "INDEKS": 2, "ADR.POŚR": 1, "WYSZUKAJ.PIONOWO": 3, "PRZESUNIĘCIE": 3, 
    "DZIŚ": 0, "TERAZ": 0, "I": 1
}

def sprawdz_formule(formula):
    """Sprawdza poprawność składniową formuły Excela (polska wersja)"""

    if not formula.startswith("="):
        return "Błąd: Formuła musi zaczynać się od '='."

    # Sprawdzenie nawiasów
    if formula.count("(") != formula.count(")"):
        return "Błąd: Niezrównoważone nawiasy!"

    # Niedozwolone znaki (uwzględniając operatory porównania)
    dozwolone = "ABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻabcdefghijklmnopqrstuvwxyząćęłńóśźż0123456789+-*/^()[]:;= \"!'<>,"
    niedozwolone = [znak for znak in formula if znak not in dozwolone]
    if niedozwolone:
        return f"Błąd: Niedozwolone znaki w formule: {set(niedozwolone)}"

    # Błędne operatory
    if re.search(r"[\+\-\*/\^]{2,}", formula):
        return "Błąd: Podwójne operatory (np. '++', '--', '**') są niepoprawne."

    # Sprawdzenie separatorów argumentów funkcji
    funkcje = re.findall(r"([A-ZĄĆĘŁŃÓŚŹŻ]+)(.*?)", formula)
    for funkcja, argumenty in funkcje:
        if funkcja not in FUNKCJE_EXCEL:
            return f"Błąd: Nieznana funkcja Excela: {funkcja}"

        # Sprawdzenie błędnych przecinków (niebędących separatorami dziesiętnymi)
        argumenty_lista = re.split(r";|(?<!\d),(?!\d)", argumenty)  # Rozdziel po średniku lub przecinku, ale nie w liczbie
        liczba_argumentów = len(argumenty_lista)

        if "," in argumenty and ";" not in argumenty:
            return "Błąd: W polskim Excelu jako separator argumentów należy używać ';' zamiast ','."

        if liczba_argumentów < FUNKCJE_EXCEL[funkcja]:
            return f"Błąd: Funkcja {funkcja} wymaga co najmniej {FUNKCJE_EXCEL[funkcja]} argumentów, a podano {liczba_argumentów}."

    # Sprawdzenie poprawności adresów komórek
    adresy = re.findall(r"([A-Z]+\$?[0-9]+\$?)", formula)
    for adres in adresy:
        if not re.match(r"^[A-Z]+\$?[0-9]+$", adres):
            return f"Błąd: Niepoprawny adres komórki: {adres}"

    # Sprawdzenie niezrównoważonych cudzysłowów
    if formula.count('"') % 2 != 0:
        return "Błąd: Niezamknięty cudzysłów w formule."

    return "Formuła wygląda poprawnie."

# Tryb interaktywny
if __name__ == "__main__":
    print("Wklej formułę Excela (polska wersja), aby ją sprawdzić. Wpisz 'exit', aby zakończyć.")
    
    while True:
        formula = input("\nPodaj formułę: ").strip()
        
        if formula.lower() == "exit":
            print("Zakończono.")
            break
        
        wynik = sprawdz_formule(formula)
        print(wynik)
