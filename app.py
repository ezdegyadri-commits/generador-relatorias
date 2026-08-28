import streamlit as st
import tempfile
import os
import io
from datetime import datetime

# Clientes de IA
from openai import OpenAI
from google import genai

# Librería para exportar a Documentos (Google Docs / Word)
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 1. Configuración de la interfaz
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")
st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

# Función para generar el documento oficial
def generar_documento_oficial(contenido_relatoria):
    doc = Document()
    
    # Inyectar la fecha actual con el formato del documento oficial
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    hoy = datetime.now()
    fecha_str = f"Mérida, Yucatán a {hoy.day:02d} de {meses[hoy.month-1]} de {hoy.year}"
    
    # Párrafo de fecha (Alineado a la derecha)
    p_fecha = doc.add_paragraph()
    r_fecha = p_fecha.add_run(fecha_str)
    r_fecha.font.name = 'Arial'
    r_fecha.font.size = Pt(11)
    p_fecha.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    doc.add_paragraph() # Espacio en blanco
    
    # Párrafo de Título (Centrado)
    p_titulo = doc.add_paragraph()
    r_titulo = p_titulo.add_run("RELATORÍA")
    r_titulo.bold = True
    r_titulo.font.name = 'Arial'
    r_titulo.font.size = Pt(12)
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph() # Espacio en blanco
    
    # Insertar el contenido procesado por la IA (Manejo de Markdown básico a Word)
    for linea in contenido_relatoria.split('\n'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Transformar títulos y negritas del formato Markdown
        if linea.startswith('##') or linea.startswith('#'):
            r = p.add_run(linea.replace('#', '').strip())
            r.bold = True
            r.font.size = Pt(12)
        else:
            partes = linea.split('**') # Divide el texto donde haya asteriscos de negrita
            for i, parte in enumerate(partes):
                r = p.add_run(parte)
                if i % 2 != 0:  # Si es impar, significa que estaba encerrado en **
                    r.bold = True
        
        # Aplicar fuente institucional a todo
        for run in p.runs:
            run.font.name = 'Arial'
            if not run.font.size:
                run.font.size = Pt(11)
                
    # Guardar en memoria para descarga directa
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# 2. Configuración en la Barra Lateral
with st.sidebar:
    st.header("⚙️ Motor de IA y Ajustes")
    motor_ia = st.radio("Selecciona el motor de IA:", ["ChatGPT (OpenAI)", "Gemini (Google)"])
    st.markdown("---")
    num_sesion = st.selectbox("Sesión de CTE:", ["Fase Intensiva", "Primera Sesión", "Segunda Sesión", "Tercera Sesión"])
    enfoque_especial = st.text_input("Tema central:", placeholder="Ej. Ajustes razonables, BAP...")

# 3. Métodos de Captura de Audio
st.subheader("🎙️ Captura de Audio de la Plenaria")
modo_grabacion = st.radio(
    "Método de captura:", 
    ["Subir archivo de audio (Recomendado para exponer sin pausas)", "Grabar en el navegador"],
    horizontal=True
)

audio_path_temporal = None
col1, col2 = st.columns([1.5, 1])

with col1:
    if "Subir" in modo_grabacion:
        archivo_subido = st.file_uploader("Arrastra tu archivo (MP3, WAV, M4A)", type=["wav", "mp3", "m4a"])
        if archivo_subido:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                audio_path_temporal = tmp_file.name
    else:
        audio_grabado = st.audio_input("Haz clic para grabar en vivo")
        if audio_grabado:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_grabado.getvalue())
                audio_path_temporal = tmp_file.name

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area("Observaciones clave de la sesión (Opcional):", height=150)

# Estado de la sesión para mantener el texto generado en pantalla y permitir su descarga
if 'texto_relatoria' not in st.session_state:
    st.session_state.texto_relatoria = None

# 4. Procesamiento Inteligente
if audio_path_temporal:
    st.markdown("---")
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        
        prompt_relatoria = f"""
        Actúa como el secretario técnico de la USAER 2E. Analiza el registro de la {num_sesion} del CTE.
        Enfoque: '{enfoque_especial}'. Notas directivas: '{notas_directivo}'.

        Genera el contenido de la relatoría (sin título ni fecha, de eso me encargo yo). Estructura el texto directamente:
        1. **Contexto y Desarrollo:** Resumen del diálogo del colegiado.
        2. **Reflexiones y Retos Pedagógicos:** Puntos críticos analizados.
        3. **Acuerdos y Compromisos:** Tareas concretas acordadas.
        Redacta en un tono directivo, formal y claro para archivo oficial.
        """

        # --- CHATGPT ---
        if "ChatGPT" in motor_ia:
            with st.spinner("Transcribiendo y redactando con ChatGPT..."):
                try:
                    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    with open(audio_path_temporal, "rb") as audio_file:
                        transcripcion = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Eres un redactor técnico institucional de educación especial."},
                            {"role": "user", "content": f"{prompt_relatoria}\n\nTranscripción:\n{transcripcion.text}"}
                        ]
                    )
                    st.session_state.texto_relatoria = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Error con OpenAI: {e}")

        # --- GEMINI ---
        else:
            with st.spinner("Subiendo audio y redactando con Gemini..."):
                try:
                    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    audio_file = gemini_client.files.upload(file=audio_path_temporal)
                    response = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt_relatoria, audio_file]
                    )
                    st.session_state.texto_relatoria = response.text
                    gemini_client.files.delete(name=audio_file.name)
                except Exception as e:
                    st.error(f"Error con Gemini: {e}")

        # Limpieza de archivo temporal
        if os.path.exists(audio_path_temporal):
            os.remove(audio_path_temporal)

# 5. Visualización y Exportación
if st.session_state.texto_relatoria:
    st.markdown("---")
    st.header("📄 Vista Previa de la Relatoría")
    st.markdown(st.session_state.texto_relatoria)
    
    # Generar el archivo DOCX en memoria
    archivo_docx = generar_documento_oficial(st.session_state.texto_relatoria)
    
    # Botón de Descarga
    st.markdown("### 💾 Exportar Documento")
    st.download_button(
        label="📥 Descargar formato oficial (Compatible con Google Docs / Word)",
        data=archivo_docx,
        file_name=f"Relatoria_CTE_{num_sesion.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary"
    )
