import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
import tempfile
import os

# 1. Configuración de la interfaz
st.set_page_config(page_title="Relatoría Inteligente", layout="centered")
st.title("🎙️ Asistente de Relatoría del CTE")
st.write("Graba el audio de la plenaria y añade notas clave. El sistema procesará ambos insumos para redactar la relatoría oficial.")

# 2. Autenticación de la API de Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Captura de texto
notas_docentes = st.text_area(
    "Notas adicionales o reportes específicos (Opcional)", 
    placeholder="Ej. Priorizar la evaluación psicopedagógica en el grupo de 3°B..."
)

# 4. Captura de audio
st.write("### 🔴 Grabar Sesión")
audio_bytes = audio_recorder(
    text="Haz clic en el micrófono para grabar",
    recording_color="#e74c3c",
    neutral_color="#95a5a6",
    icon_size="2x",
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    
    if st.button("Procesar y Generar Relatoría", type="primary"):
        with st.spinner("Analizando la conversación y estructurando el documento..."):
            try:
                # 5. Guardar el audio en un archivo temporal para subirlo a Gemini
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_file_path = tmp_file.name

                # 6. Subir el archivo mediante la API de Archivos de Gemini
                audio_file = genai.upload_file(path=tmp_file_path)

                # 7. Configurar el modelo (Flash es rápido y excelente para audio, Pro es mejor para razonamiento complejo)
                model = genai.GenerativeModel('gemini-1.5-flash')

                # 8. El Prompt Estructurado
                prompt = f"""
                Actúa como el secretario técnico de la USAER 2E. 
                Escucha el audio adjunto de la sesión plenaria de nuestro Consejo Técnico Escolar y lee las siguientes notas de los docentes.
                Genera una relatoría formal y estructurada en formato Markdown que incluya:
                1. Análisis y Reflexión del Colectivo (temas principales discutidos).
                2. Retos Pedagógicos Detectados.
                3. Acuerdos y Compromisos Generales.
                
                Omite charlas informales. Mantén un tono académico e institucional.
                
                Notas de los docentes: {notas_docentes}
                """

                # 9. Generar el contenido enviando el texto y el objeto de audio
                response = model.generate_content([prompt, audio_file])
                
                st.success("¡Relatoría generada con éxito!")
                
                st.markdown("---")
                st.markdown("### Documento Final")
                st.markdown(response.text)

                # 10. Limpieza de archivos temporales
                os.remove(tmp_file_path)
                genai.delete_file(audio_file.name)

            except Exception as e:
                st.error(f"Ocurrió un error durante el procesamiento: {e}")
