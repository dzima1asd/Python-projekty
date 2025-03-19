import paho.mqtt.client as mqtt
import speech_recognition as sr
import time

# Konfiguracja MQTT
MQTT_BROKER = "192.168.100.11"
MQTT_TOPIC = "led/control"

# Inicjalizacja klienta MQTT
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

# Inicjalizacja rozpoznawania mowy
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Nasłuchuję komendy 'światło'...")
print("Nasłuchuję komendy 'zgaś'...")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Mów...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznano: {text}")

            if "światło" in text.lower():
                client.publish(MQTT_TOPIC, "TOGGLE")
                print("Wysłano komendę TOGGLE")

        except sr.UnknownValueError:
            print("Nie rozpoznano mowy")
        except sr.RequestError:
            print("Błąd połączenia z Google API")
        except Exception as e:
            print(f"Błąd: {e}")

        time.sleep(2)

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Mów...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznano: {text}")

            if "zgaś" in text.lower():
                client.publish(MQTT_TOPIC, "ZGAŚ")
                print("Wysłano komendę ZGAŚ")

        except sr.UnknownValueError:
            print("Nie rozpoznano mowy")
        except sr.RequestError:
            print("Błąd połączenia z Google API")
        except Exception as e:
            print(f"Błąd: {e}")

        time.sleep(2)


print(f"Rozpoznany tekst: {tekst}")

if "koniec koniec" in tekst.lower():
print("Polecenie zakończenia programu wykryte. Kończę działanie.")
break
