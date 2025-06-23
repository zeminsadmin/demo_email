import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = "imap.hostinger.com"

def listar_carpetas():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    mail.login(EMAIL_USER, EMAIL_PASS)
    estado, carpetas = mail.list()
    if estado == "OK":
        print("Carpetas disponibles:")
        for carpeta in carpetas:
            print(carpeta.decode())
    else:
        print("No se pudieron listar las carpetas.")
    mail.logout()

listar_carpetas()