import paho.mqtt.client as mqtt
import speech_recognition as sr
import time

# Konfiguracja MQTT
MQTT_BROKER = "192.168.100.12"
MQTT_TOPIC = "led/control"

# Inicjalizacja klienta MQTT
client = mqtt.Client()

try:
    client.connect(MQTT_BROKER, 1883, 60)
    mqtt_connected = True
    print("Połączono z brokerem MQTT")
except Exception as e:
    mqtt_connected = False
    print(f"Nie można połączyć z brokerem: {e}. Program działa w trybie offline.")

# Inicjalizacja rozpoznawania mowy
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Nasłuchuję komendy 'światło', 'zgaś' lub 'koniec koniec'...")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Mów...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznano: {text}")

            if "światło" in text.lower():
                print("Rozpoznano komendę WŁĄCZ")
                if mqtt_connected:
                    client.publish(MQTT_TOPIC, "ON")
                    print("Wysłano MQTT: ON")

            elif "zgaś" in text.lower():
                print("Rozpoznano komendę WYŁĄCZ")
                if mqtt_connected:
                    client.publish(MQTT_TOPIC, "OFF")
                    print("Wysłano MQTT: OFF")

            elif "koniec koniec" in text.lower():
                print("Polecenie zakończenia programu wykryte. Kończę działanie.")
                break  # Zatrzymanie pętli while

        except sr.UnknownValueError:
            print("Nie rozpoznano mowy")
        except sr.RequestError:
            print("Błąd połączenia z Google API")
        except Exception as e:
            print(f"Błąd: {e}")

        time.sleep(2)

print("Program zakończył działanie.")
