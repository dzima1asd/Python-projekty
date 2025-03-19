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

print("Nasłuchuję komend: 'światło', 'zgaś', 'koniec koniec'")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Mów...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznano: {text}")

            if "światło" in text.lower():
                client.publish(MQTT_TOPIC, "ON")
                print("Wysłano komendę ON")

            elif "zgaś" in text.lower():
                client.publish(MQTT_TOPIC, "OFF")
                print("Wysłano komendę OFF")

            elif "koniec koniec" in text.lower():
                print("Polecenie zakończenia programu wykryte. Kończę działanie.")
                break

        except sr.UnknownValueError:
            print("Nie rozpoznano mowy")
        except sr.RequestError:
            print("Błąd połączenia z Google API")
        except Exception as e:
            print(f"Błąd: {e}")

        time.sleep(2)

print("Program zakończony.")
