import streamlit as st
from google import genai
from google.genai import types
import tempfile
import os

# 1. Configuración del Panel
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")

# 2. Autenticación con el nuevo cliente oficial
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta configurar la clave GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()
except Exception as e:
    st.error(f"Error de autenticación: {e}")
    st.stop()

st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Ajustes de la Sesión")
    num_sesion = st.selectbox("Sesión de CTE:", ["Fase Intensiva", "Primera Sesión", "Segunda Sesión", "Tercera Sesión"])
    enfoque_especial = st.text_input("Tema central:", placeholder="Ej. Ajustes razonables, BAP...")

# 3. Selector de captura
st.subheader("🎙️ Captura de Audio de la Plenaria")
modo_grabacion = st.radio(
    "Selecciona el método de captura:", 
    ["Subir archivo (Recomendado para exponer/cambiar pestañas)", "Grabar en el navegador"],
    horizontal=True
)

audio_path_temporal = None
col1, col2 = st.columns([1.5, 1])

with col1:
    if "Subir" in modo_grabacion:
        st.info("💡 Graba con la app de voz de tu dispositivo en segundo plano y sube el archivo al finalizar.")
        archivo_subido = st.file_uploader("Arrastra tu archivo de audio (MP3, WAV, M4A)", type=["wav", "mp3", "m4a"])
        if archivo_subido:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Archivo listo para procesar.")
    else:
        st.warning("⚠️ Mantén la pestaña visible para evitar que el navegador suspenda la grabación.")
        audio_grabado = st.audio_input("Haz clic para grabar en vivo")
        if audio_grabado:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_grabado.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Audio capturado.")

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area("Observaciones clave de la sesión (Opcional):", height=150)

# 4. Procesamiento
if audio_path_temporal:
    st.markdown("---")
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        with st.spinner("Subiendo audio y redactando relatoría con Gemini..."):
            try:
                # Subir archivo usando el nuevo SDK
                audio_file = client.files.upload(file=audio_path_temporal)

                prompt = f"""
                Actúa como el secretario técnico y asistente de dirección de la USAER 2E. 
                Escucha el archivo de audio adjunto, correspondiente a la {num_sesion} del Consejo Técnico Escolar.
                Enfoque de la sesión: '{enfoque_especial}'.
                Notas de dirección: '{notas_directivo}'.

                Genera una relatoría institucional estructurada en Markdown:
                1. **Contexto y Desarrollo:** Resumen del diálogo del colegiado.
                2. **Reflexiones y Retos:** Puntos críticos analizados sobre la práctica docente.
                3. **Acuerdos y Compromisos:** Decisiones concretas tomadas.

                Redacta en un tono directivo, formal y claro para archivo oficial.
                """

               # Llamada al modelo con la versión solicitada por la API
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt, audio_file]
                )
            

                st.markdown("---")
                st.header("📄 Relatoría Oficial USAER 2E")
                st.markdown(response.text)

                # Limpieza
                os.remove(audio_path_temporal)
                client.files.delete(name=audio_file.name)

            except Exception as e:
                st.error(f"Error al procesar: {e}")
