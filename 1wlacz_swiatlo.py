import paho.mqtt.client as mqtt

# Konfiguracja MQTT
MQTT_BROKER = "87.205.207.243"
MQTT_PORT = 1883
MQTT_TOPIC = "led/control"

# Inicjalizacja klienta MQTT
client = mqtt.Client()

def connect_mqtt():
    """Funkcja do łączenia z brokerem MQTT."""
    global client
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # Uruchomienie pętli obsługi MQTT w tle
        print("Połączono z brokerem MQTT")
        return True
    except Exception as e:
        print(f"Nie można połączyć z brokerem: {e}. Program działa w trybie offline.")
        return False

mqtt_connected = connect_mqtt()

# Prosty interfejs tekstowy
print("Sterowanie LED:")
print("1 - Włącz")
print("2 - Wyłącz")
print("3 - Wyjście")

while True:
    # Sprawdzenie, czy klient jest połączony, jeśli nie - próba ponownego połączenia
    if not client.is_connected():
        print("Rozłączono z MQTT, próbuję połączyć ponownie...")
        mqtt_connected = connect_mqtt()

    choice = input("Wybierz opcję: ")

    if choice == "1":
        print("Wysyłam: ON")
        if mqtt_connected:
            client.publish(MQTT_TOPIC, "ON")

    elif choice == "2":
        print("Wysyłam: OFF")
        if mqtt_connected:
            client.publish(MQTT_TOPIC, "OFF")

    elif choice == "3":
        print("Koniec programu.")
        client.loop_stop()  # Zatrzymanie obsługi MQTT przed zamknięciem programu
        break

    else:
        print("Nieprawidłowy wybór. Spróbuj ponownie.")
