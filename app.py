import streamlit as st
import tempfile
import os

# Clientes de IA
from openai import OpenAI
from google import genai

# 1. Configuración de la interfaz
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")
st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

# 2. Configuración en la Barra Lateral
with st.sidebar:
    st.header("⚙️ Motor de IA y Ajustes")
    
    # Selector de Inteligencia Artificial para contingencias
    motor_ia = st.radio(
        "Selecciona el motor de IA:",
        ["ChatGPT (OpenAI - Alta estabilidad)", "Gemini (Google)"]
    )
    
    st.markdown("---")
    num_sesion = st.selectbox(
        "Sesión de CTE:",
        ["Fase Intensiva", "Primera Sesión Ordinaria", "Segunda Sesión Ordinaria", "Tercera Sesión Ordinaria"]
    )
    enfoque_especial = st.text_input("Tema central:", placeholder="Ej. Ajustes razonables, BAP...")
    st.info("ℹ️ **Consejo Directivo:** Si un servidor presenta saturación, puedes cambiar de motor en cualquier momento sin perder la sesión.")

# 3. Métodos de Captura de Audio
st.subheader("🎙️ Captura de Audio de la Plenaria")
modo_grabacion = st.radio(
    "Método de captura:", 
    ["Subir archivo de audio (Recomendado para no interrumpir exposición)", "Grabar en el navegador"],
    horizontal=True
)

audio_path_temporal = None
col1, col2 = st.columns([1.5, 1])

with col1:
    if "Subir" in modo_grabacion:
        st.info("💡 Graba con la grabadora nativa de tu laptop/teléfono en segundo plano y sube el archivo al concluir.")
        archivo_subido = st.file_uploader("Arrastra tu archivo (MP3, WAV, M4A)", type=["wav", "mp3", "m4a"])
        if archivo_subido:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Archivo listo para procesar.")
    else:
        st.warning("⚠️ Mantén la pestaña visible para evitar que el navegador suspenda el micrófono.")
        audio_grabado = st.audio_input("Haz clic para grabar en vivo")
        if audio_grabado:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_grabado.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Audio capturado.")

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area("Observaciones clave de la sesión (Opcional):", height=150)

# 4. Procesamiento Inteligente
if audio_path_temporal:
    st.markdown("---")
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        
        prompt_relatoria = f"""
        Actúa como el secretario técnico y asistente de dirección de la USAER 2E.
        Analiza el registro de la {num_sesion} del Consejo Técnico Escolar.
        Enfoque de la sesión: '{enfoque_especial}'.
        Notas directivas adicionales: '{notas_directivo}'.

        Genera una relatoría institucional estructurada en Markdown:
        1. **Contexto y Desarrollo:** Resumen del diálogo del colegiado.
        2. **Reflexiones y Retos Pedagógicos:** Puntos críticos analizados sobre la práctica docente.
        3. **Acuerdos y Compromisos:** Decisiones y tareas concretas acordadas.

        Redacta en un tono directivo, formal y claro para archivo oficial.
        """

        # --- OPCIÓN A: PROCESAMIENTO CON CHATGPT (OPENAI) ---
        if "ChatGPT" in motor_ia:
            with st.spinner("Transcribiendo con Whisper y redactando con GPT-4o..."):
                try:
                    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    
                    # 1. Transcripción con Whisper
                    with open(audio_path_temporal, "rb") as audio_file:
                        transcripcion = openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                    
                    # 2. Redacción con GPT-4o
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Eres un redactor técnico institucional experto en educación especial y gestión escolar."},
                            {"role": "user", "content": f"{prompt_relatoria}\n\nTranscripción del audio:\n{transcripcion.text}"}
                        ]
                    )

                    st.markdown("---")
                    st.header("📄 Relatoría Oficial USAER 2E (Generada con GPT-4o)")
                    st.markdown(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"Error con OpenAI: {e}")
                finally:
                    if os.path.exists(audio_path_temporal):
                        os.remove(audio_path_temporal)

        # --- OPCIÓN B: PROCESAMIENTO CON GEMINI ---
        else:
            with st.spinner("Subiendo audio y redactando relatoría con Gemini..."):
                try:
                    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    audio_file = gemini_client.files.upload(file=audio_path_temporal)

                    response = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt_relatoria, audio_file]
                    )

                    st.markdown("---")
                    st.header("📄 Relatoría Oficial USAER 2E (Generada con Gemini)")
                    st.markdown(response.text)

                    gemini_client.files.delete(name=audio_file.name)
                except Exception as e:
                    st.error(f"Error con Gemini: {e}")
                finally:
                    if os.path.exists(audio_path_temporal):
                        os.remove(audio_path_temporal)
