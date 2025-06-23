import imaplib
import smtplib
import email
import time
import os
import chardet # type: ignore
from dotenv import load_dotenv
from openai import OpenAI
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from langdetect import detect

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IMAP_SERVER = "imap.hostinger.com"
SMTP_SERVER = "smtp.hostinger.com"

client = OpenAI(api_key=OPENAI_API_KEY)

print("\n[START] Zemins - Respuesta Automática de Correos Comerciales")
print("[LOOP] Ejecutando...\n")

def conectar_imap():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    mail.login(EMAIL_USER, EMAIL_PASS)
    return mail

def conectar_smtp():
    server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
    server.login(EMAIL_USER, EMAIL_PASS)
    return server

def detectar_codificacion(data):
    result = chardet.detect(data)
    return result['encoding'] or 'utf-8'

def obtener_no_leidos(mail):
    mail.select("inbox")
    estado, mensajes = mail.search(None, '(UNSEEN)')
    return mensajes[0].split()

def obtener_cuerpo_email(mensaje):
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            content_type = parte.get_content_type()
            if content_type == "text/plain":
                charset = parte.get_content_charset() or detectar_codificacion(parte.get_payload(decode=True))
                cuerpo = parte.get_payload(decode=True).decode(charset, errors="ignore")
                break
    else:
        charset = mensaje.get_content_charset() or detectar_codificacion(mensaje.get_payload(decode=True))
        cuerpo = mensaje.get_payload(decode=True).decode(charset, errors="ignore")
    return cuerpo

def extraer_nombre_remitente(cuerpo):
    lineas = cuerpo.splitlines()
    for linea in lineas:
        if any(saludo in linea.lower() for saludo in ["atentamente", "saludos", "cordialmente"]):
            partes = linea.split()
            if len(partes) > 1:
                return partes[-1].strip(",.:;")
    return ""

def obtener_saludo_temporal():
    hora = datetime.now().hour
    if 6 <= hora < 14:
        return "Buenos días"
    elif 14 <= hora < 20:
        return "Buenas tardes"
    else:
        return "Buenas noches"

def detectar_idioma(texto):
    try:
        return detect(texto)
    except:
        return "es"

def generar_respuesta(cuerpo, nombre):
    idioma = detectar_idioma(cuerpo)
    saludo = nombre if nombre else obtener_saludo_temporal()

    prompts = {
        "es": "Eres un asistente corporativo de Zemins llamado Roberto Martínez. Tu tarea es responder amablemente a correos con fines comerciales, rechazando su propuesta de forma profesional, pero dejando la puerta abierta a futuras colaboraciones. Si tienes el nombre del remitente, salúdalo por su nombre; si no, utiliza un saludo apropiado como buenos días, buenas tardes o buenas noches. Siempre debes hablar en primera persona del plural (usamos, estamos, creemos, etc.). Usa párrafos separados, claros y cálidos. No incluyas firma.",
        "en": "You are a corporate assistant from Zemins named Roberto Martínez. Your task is to politely reply to commercial emails, professionally declining their proposal while leaving the door open for future collaboration. If you have the sender's name, greet them by name; otherwise, use a time-appropriate greeting like good morning, good afternoon, or good evening. Always speak in the first person plural (we believe, we are, we appreciate, etc.). Use clear, warm, separated paragraphs. Do not include a signature."
    }

    prompt_sistema = prompts.get(idioma, prompts["es"])

    mensaje_usuario = f"Saludo inicial: {saludo}\n\nCorreo:\n{cuerpo}"

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensaje_usuario}
        ]
    )

    return completion.choices[0].message.content.strip()

def enviar_respuesta(remitente, asunto, respuesta, smtp_server):
    mensaje_respuesta = MIMEMultipart("related")
    mensaje_respuesta["From"] = EMAIL_USER
    mensaje_respuesta["To"] = remitente
    mensaje_respuesta["Subject"] = f"Re: {asunto}"

    firma_html = """
    <br><br>
    <div style="max-width: 650px; font-family: Arial, sans-serif; font-size: 14px; color: #333; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 20px;">
      <table width="100%" cellspacing="0" cellpadding="0">
        <tr>
          <td style="vertical-align: middle; padding-right: 15px;">
            <p style="margin: 0; font-size: 15px;"><strong style='color: #000000;'>Roberto Martínez</strong></p>
            <p style="margin: 2px 0 0 0; font-size: 13px; color: #000000;">Departamento Comercial</p>
            <p style="margin: 2px 0 0 0; font-size: 13px;"><a href='http://www.zemins.com' style='color: #1a0dab; text-decoration: none;'>www.zemins.com</a></p>
            <p style="margin: 6px 0 0 0; font-size: 13px;">
              <a href='https://linkedin.com/company/zemins' style='margin-right: 10px; text-decoration: none;'><img src='https://cdn-icons-png.flaticon.com/24/145/145807.png' alt='LinkedIn' style='vertical-align: middle;'></a>
              <a href='https://twitter.com/wearezemins' style='margin-right: 10px; text-decoration: none;'><img src='https://cdn-icons-png.flaticon.com/24/733/733579.png' alt='Twitter' style='vertical-align: middle;'></a>
              <a href='https://instagram.com/wearezemins' style='text-decoration: none;'><img src='https://cdn-icons-png.flaticon.com/24/2111/2111463.png' alt='Instagram' style='vertical-align: middle;'></a>
            </p>
          </td>
          <td style="text-align: right; vertical-align: middle;">
            <img src="cid:logo_zemins" alt="Zemins" style="height: 100px; border-radius: 8px;">
          </td>
        </tr>
      </table>
    </div>
    """

    respuesta_html = respuesta.replace('\n', '<br>')
    html = f"""
    <html lang="es">
      <body style="line-height: 1.4; font-family: Arial, sans-serif; font-size: 15px; color: #333;">
        {respuesta_html}
        {firma_html}
      </body>
    </html>
    """

    mensaje_respuesta.attach(MIMEText(html, "html"))

    with open("assets/logo.png", "rb") as f:
        img_data = f.read()
        imagen = MIMEImage(img_data)
        imagen.add_header("Content-ID", "<logo_zemins>")
        imagen.add_header("Content-Disposition", "inline", filename="logo.png")
        mensaje_respuesta.attach(imagen)

    smtp_server.sendmail(EMAIL_USER, remitente, mensaje_respuesta.as_string())

    raw = mensaje_respuesta.as_bytes()
    with conectar_imap() as imap:
        imap.append('INBOX.Sent', '', imaplib.Time2Internaldate(time.time()), raw)

    print(f"[OK] Respuesta enviada a {remitente}")

def procesar_correos():
    mail = conectar_imap()
    smtp_server = conectar_smtp()

    while True:
        print("[WAIT] Revisando nuevos correos no leídos...")
        correos = obtener_no_leidos(mail)

        if not correos:
            print("[OK] No hay nuevos correos.")
        else:
            for correo_id in correos:
                _, datos = mail.fetch(correo_id, "(RFC822)")
                raw_email = datos[0][1]
                mensaje = email.message_from_bytes(raw_email)

                remitente = email.utils.parseaddr(mensaje["From"])[1]
                asunto = mensaje["Subject"]
                cuerpo = obtener_cuerpo_email(mensaje)

                print(f"\n[EMAIL] Nuevo correo de: {remitente} | Asunto: {asunto}")

                nombre_remitente = extraer_nombre_remitente(cuerpo)
                respuesta = generar_respuesta(cuerpo, nombre_remitente)
                print("[RESPONSE] Respuesta generada:")
                print(respuesta)

                enviar_respuesta(remitente, asunto, respuesta, smtp_server)

        print("[SLEEP] Esperando 5 minutos...")
        time.sleep(300)

procesar_correos()
