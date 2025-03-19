#!/bin/bash

# Definicja kodu Morse'a
declare -A morse=(
    ["a"]=".-"
    ["b"]="-..."
    ["c"]="-.-."
    ["d"]="-.."
    ["e"]="."
    ["f"]="..-."
    ["g"]="--."
    ["h"]="...."
    ["i"]=".."
    ["j"]=".---"
    ["k"]="-.-"
    ["l"]=".-.."
    ["m"]="--"
    ["n"]="-."
    ["o"]="---"
    ["p"]=".--."
    ["q"]="--.-"
    ["r"]=".-."
    ["s"]="..."
    ["t"]="-"
    ["u"]="..-"
    ["v"]="...-"
    ["w"]=".--"
    ["x"]="-..-"
    ["y"]="-.--"
    ["z"]="--.."
    ["1"]=".----"
    ["2"]="..---"
    ["3"]="...--"
    ["4"]="....-"
    ["5"]="....."
    ["6"]="-...."
    ["7"]="--..."
    ["8"]="---.."
    ["9"]="----."
    ["0"]="-----"
)

# Pobranie tekstu od użytkownika
read -p "Wpisz tekst: " input

# Zamiana na małe litery
input=$(echo "$input" | tr '[:upper:]' '[:lower:]')

# Przetwarzanie każdego znaku
for ((i = 0; i < ${#input}; i++)); do
    char="${input:$i:1}"  # Pobranie jednego znaku
    if [[ "$char" == " " ]]; then
        sleep 3  # Odstęp dla spacji
    elif [[ -n "${morse[$char]}" ]]; then
        # Przetwarzanie sekwencji Morse'a
        sequence="${morse[$char]}"
        echo "Litera: $char -> $sequence"
        for ((j = 0; j < ${#sequence}; j++)); do
            signal="${sequence:$j:1}"
            if [[ "$signal" == "." ]]; then
                termux-torch on
                sleep 0.1  # Długość kropki
                termux-torch off
            elif [[ "$signal" == "-" ]]; then
                termux-torch on
                sleep 1  # Długość kreski
                termux-torch off
            fi
            sleep 0.5  # Odstęp między sygnałami w literze
        done
        sleep 3  # Odstęp między literami
    fi
done

echo "koniec"


