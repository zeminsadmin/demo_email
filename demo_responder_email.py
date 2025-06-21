import streamlit as st # type: ignore
from openai import OpenAI # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Zemins - Demo IA", layout="centered")
st.title("✉️ Zemins - Respuesta automática de correos")

st.write("Pega a continuación un correo recibido. Zemins lo leerá y generará una respuesta automática profesional.")

email_text = st.text_area("✉️ Correo recibido", height=200)

if st.button("✍️ Generar respuesta"):
    if not email_text.strip():
        st.warning("Por favor, introduce un correo.")
    else:
        with st.spinner("Generando respuesta con IA..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente virtual corporativo de zemins. Tu tarea es redactar respuestas a correos electrónicos de clientes "
                            "de forma clara, amable y profesional. Adapta el tono al contenido del mensaje. Sé resolutivo y conciso. Solo responde los que sean comerciales y te intenten vender algo. Jamás digas que si, rechazalo con cordialidad. "
                            "Evita ambigüedades y asegúrate de que el cliente reciba una respuesta útil. Finaliza con una firma de atención al cliente de zemins."
                        )
                    },

                    {"role": "user", "content": email_text}
                ]
            )
            st.success("Respuesta generada:")
            respuesta = response.choices[0].message.content.strip()

            firma = (
                "\n\n---\n"
                "**Atentamente,**\n"
                "Departamento de Atención al Cliente  \n"
                "**zemins**  \n"
                "[www.zemins.com](http://www.zemins.com)"
            )

            st.write(respuesta + firma)
