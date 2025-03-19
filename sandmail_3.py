import smtplib
import time
import sys
import threading
from email.mime.text import MIMEText

def send_email(message, recipients):
    sender_email = "mamba.pies123@gmail.com"  # Podmień na swój adres e-mail
    sender_password = "bxtu fvlk hwbb mvlz"  # Podmień na swoje hasło lub użyj App Password

    msg = MIMEText(message)
    msg['Subject'] = "Twoja wiadomość"
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print("Email wysłany pomyślnie!")
    except Exception as e:
        print(f"Błąd podczas wysyłania emaila: {e}")

def countdown():
    print("\nProgram wyłączy się automatycznie. Wciśnij Enter, aby zatrzymać.")

    stop_event = threading.Event()

    def wait_for_input():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=wait_for_input, daemon=True)
    input_thread.start()

    for i in range(10, -1, -1):
        print(f"Odliczanie: {i}  ", end="\r", flush=True)
        time.sleep(1)
        if stop_event.is_set():
            print("\nZatrzymano automatyczne wyłączenie.")
            return True  # Przerwanie odliczania

    sys.exit()  # Automatyczne zamknięcie po 10 sekundach

def main():
    while True:
        message = input("Wpisz wiadomość do wysłania: ")
        recipients = input("Podaj adresy email oddzielone spacją: ").split()
        
        send_email(message, recipients)
        
        if not countdown():
            break

if __name__ == "__main__":
    main()
