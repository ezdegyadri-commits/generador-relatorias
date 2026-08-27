import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
import tempfile
import os

# 1. Configuración de la página del Panel del Director
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")

# 2. Autenticación de la API de Gemini (desde los secrets de Streamlit Cloud)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta configurar la clave GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# 3. Interfaz Visual
st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

# 4. Barra lateral para metadatos de la sesión
with st.sidebar:
    st.header("⚙️ Ajustes de la Sesión")
    num_sesion = st.selectbox(
        "Sesión de CTE:",
        ["Fase Intensiva", "Primera Sesión Ordinaria", "Segunda Sesión Ordinaria", "Tercera Sesión Ordinaria"]
    )
    enfoque_especial = st.text_input("Enfoque o tema central de hoy:", placeholder="Ej. Barreras para el Aprendizaje, Ajustes Razonables...")
    st.markdown("---")
    st.info("ℹ️ **Instrucción:** Mantén esta pestaña abierta. Presiona el micrófono para iniciar la captura de audio ambiental durante la plenaria.")

# 5. Cuerpo principal (Columnas para grabación y notas)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Captura de Audio (Segundo Plano)")
    st.write("Presiona el ícono para comenzar a grabar la sesión:")
    
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c", # Rojo cuando graba
        neutral_color="#2980b9",   # Azul cuando está en pausa/espera
        icon_size="3x",
    )

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area(
        "Anota observaciones clave o nombres de docentes con participaciones destacadas (Opcional):",
        placeholder="Ej. El maestro de 3°A propuso un formato nuevo para el seguimiento de lectura...",
        height=150
    )

# 6. Lógica de Procesamiento de la IA
if audio_bytes:
    st.markdown("---")
    st.success("✅ Audio temporal capturado en la memoria del navegador.")
    
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        with st.spinner("Subiendo audio seguro a Gemini y redactando la relatoría... Esto tomará unos segundos dependiendo de la duración de la sesión."):
            try:
                # Crear archivo temporal para subir el audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_file_path = tmp_file.name

                # Subir archivo mediante la API de Archivos de Gemini
                audio_file = genai.upload_file(path=tmp_file_path)

                # Instanciar el modelo (gemini-1.5-pro es ideal para retener el hilo en audios largos)
                model = genai.GenerativeModel('gemini-1.5-pro')

                # Prompt estructurado para la generación
                prompt = f"""
                Actúa como el secretario técnico y asistente de dirección de la USAER 2E. 
                Escucha el archivo de audio adjunto, que corresponde a la {num_sesion} de nuestro Consejo Técnico Escolar.
                El enfoque pedagógico central de esta sesión fue: '{enfoque_especial}'.
                Considera también las siguientes notas tomadas por la dirección durante la sesión: '{notas_directivo}'.

                Genera una relatoría institucional, profesional y lista para archivar que contenga:
                1. **Contexto y Desarrollo de la Sesión:** Un resumen general del diálogo y la participación del colegiado.
                2. **Reflexiones y Retos Analizados:** Los puntos críticos sobre la práctica docente que se discutieron.
                3. **Acuerdos y Compromisos:** Tareas específicas, cambios metodológicos o decisiones acordadas por el colectivo.

                Redacta en un tono directivo, formal y claro. Omite el ruido ambiental o las pláticas fuera de tema.
                """

                # Generar la respuesta enviando el prompt y el archivo de audio
                response = model.generate_content([prompt, audio_file])
                
                # Mostrar resultados
                st.markdown("---")
                st.header("📄 Relatoría Oficial USAER 2E")
                st.markdown(response.text)

                # Limpieza por seguridad: eliminar el archivo del servidor de Google y del servidor temporal
                os.remove(tmp_file_path)
                genai.delete_file(audio_file.name)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar el audio: {e}")
