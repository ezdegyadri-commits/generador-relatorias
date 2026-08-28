import streamlit as st
import tempfile
import os
import io
import time
from datetime import datetime

# Clientes de Inteligencia Artificial
from openai import OpenAI
from google import genai

# Librería para generación de PDF Oficial
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.pdfgen import canvas

# 1. Configuración de la interfaz
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")
st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

# Clase Canvas personalizada: Membrete de borde a borde
class PlantillaOficialYucatan(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for page in self.pages:
            self.__dict__.update(page)
            self.dibujar_membrete()
            super().showPage()
        super().save()

    def dibujar_membrete(self):
        ancho, alto = letter
        
        # ENCABEZADO: x=0, ancho=total del papel
        if os.path.exists("encabezado.png"):
            self.drawImage("encabezado.png", 0, alto - 90, width=ancho, height=90, preserveAspectRatio=True, mask='auto')
        
        # PIE DE PÁGINA: x=0, ancho=total del papel, anclado al fondo (y=0)
        if os.path.exists("pie_pagina.png"):
            self.drawImage("pie_pagina.png", 0, 0, width=ancho, height=50, preserveAspectRatio=True, mask='auto')

# Función que genera el documento PDF oficial
def generar_pdf_oficial(contenido_relatoria, num_asistentes):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=95,
        bottomMargin=70
    )
    
    styles = getSampleStyleSheet()
    
    estilo_fecha = ParagraphStyle('Fecha', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=2)
    estilo_titulo = ParagraphStyle('TituloRelatoria', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=1)
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, spaceBefore=10, spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('Cuerpo', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, alignment=4, spaceAfter=6)
    estilo_firma = ParagraphStyle('Firma', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=1)
    estilo_firma_negrita = ParagraphStyle('FirmaN', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=1)
    
    elementos = []
    
    # --- Fecha y Título ---
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    hoy = datetime.now()
    fecha_str = f"Mérida, Yucatán a {hoy.day:02d} de {meses[hoy.month-1]} de {hoy.year}"
    
    elementos.append(Paragraph(fecha_str, estilo_fecha))
    elementos.append(Spacer(1, 15))
    elementos.append(Paragraph("RELATORÍA", estilo_titulo))
    elementos.append(Spacer(1, 15))
    
    # --- Procesar párrafos generados por IA ---
    for linea in contenido_relatoria.split('\n'):
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
        
        if linea_limpia.startswith('###') or linea_limpia.startswith('##') or linea_limpia.startswith('#'):
            texto_sub = linea_limpia.replace('#', '').strip()
            elementos.append(Paragraph(texto_sub, estilo_subtitulo))
        else:
            partes = linea_limpia.split('**')
            texto_html = ""
            for i, p in enumerate(partes):
                texto_html += f"<b>{p}</b>" if i % 2 == 1 else p
            elementos.append(Paragraph(texto_html, estilo_cuerpo))
            
    # --- Bloque de Firma de la Dirección y Sello ---
    elementos.append(Spacer(1, 50)) 
    
    # Textos de la firma actualizados
    p_linea = Paragraph("___________________________________", estilo_firma)
    p_nombre = Paragraph("Psic. Edgar Adrián Yam Briceño MD", estilo_firma_negrita)
    p_cargo = Paragraph("Director de la USAER 02 Estatal", estilo_firma)
    
    columna_firma = [p_linea, p_nombre, p_cargo]
    
    columna_sello = ""
    if os.path.exists("sello.png"):
        columna_sello = RLImage("sello.png", width=1.5*inch, height=1.5*inch)
        
    tabla_direccion = Table([[columna_firma, columna_sello]], colWidths=[4.5*inch, 2*inch])
    tabla_direccion.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elementos.append(tabla_direccion)
    
    # --- Tabla de Asistencia del Personal (Dinámica) ---
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("FIRMAS DEL PERSONAL ASISTENTE", estilo_subtitulo))
    elementos.append(Spacer(1, 10))
    
    # Generación de filas dinámicas según el número de asistentes
    datos_personal = [["Nombre del Docente / Especialista", "Función", "Firma"]]
    for _ in range(num_asistentes):
        datos_personal.append(["", "", ""])
    
    # La altura de las filas se ajusta a la cantidad total (encabezado + asistentes)
    tabla_personal = Table(datos_personal, colWidths=[3.2*inch, 1.8*inch, 2.0*inch], rowHeights=[25] * (num_asistentes + 1))
    tabla_personal.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
    ]))
    elementos.append(tabla_personal)
    
    doc.build(elementos, canvasmaker=PlantillaOficialYucatan)
    buffer.seek(0)
    return buffer

# 2. Barra Lateral
with st.sidebar:
    st.header("⚙️ Ajustes")
    motor_ia = st.radio("Motor de IA:", ["ChatGPT (OpenAI)", "Gemini (Google)"])
    st.markdown("---")
    num_sesion = st.selectbox("Sesión de CTE:", ["Fase Intensiva", "Primera Sesión", "Segunda Sesión", "Tercera Sesión", "Cuarta Sesión", "Quinta Sesión", "Sexta Sesión", "Séptima Sesión", "Octava Sesión"])
    enfoque_especial = st.text_input("Tema central:", placeholder="Ej. Ajustes razonables, BAP...")
    # Nuevo selector numérico para los asistentes
    num_asistentes = st.number_input("Número de asistentes (para firmas):", min_value=1, max_value=30, value=6, step=1)

# 3. Captura
st.subheader("🎙️ Captura de Audio de la Plenaria")
modo_grabacion = st.radio("Método:", ["Subir archivo (Recomendado)", "Grabar web"], horizontal=True)

audio_path_temporal = None
col1, col2 = st.columns([1.5, 1])

with col1:
    if "Subir" in modo_grabacion:
        archivo_subido = st.file_uploader("Sube tu archivo (MP3, WAV, M4A)", type=["wav", "mp3", "m4a"])
        if archivo_subido:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                audio_path_temporal = tmp_file.name
    else:
        audio_grabado = st.audio_input("Grabar en vivo")
        if audio_grabado:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_grabado.getvalue())
                audio_path_temporal = tmp_file.name

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area("Observaciones clave:", height=150)

if 'texto_relatoria' not in st.session_state:
    st.session_state.texto_relatoria = None

# 4. Procesamiento
if audio_path_temporal:
    st.markdown("---")
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        
        prompt_relatoria = f"""
        Actúa como el secretario técnico de la USAER 2E. Analiza el registro de la {num_sesion} del CTE.
        Enfoque: '{enfoque_especial}'. Notas directivas: '{notas_directivo}'.

        Estructura el cuerpo directamente en:
        1. Contexto y Desarrollo: Resumen del diálogo del colegiado.
        2. Reflexiones y Retos Pedagógicos: Puntos críticos analizados.
        3. Acuerdos y Compromisos: Tareas y decisiones concretadas.
        Redacta formal y claro para archivo oficial. No incluyas fecha ni título principal.
        """

        if "ChatGPT" in motor_ia:
            with st.spinner("Procesando con ChatGPT..."):
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
                    st.error(f"Error OpenAI: {e}")

        else:
            with st.spinner("Procesando con Gemini..."):
                try:
                    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    audio_file = gemini_client.files.upload(file=audio_path_temporal)

                    modelos = ['gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-3.6-flash']
                    response = None

                    for modelo in modelos:
                        for intento in range(3):
                            try:
                                response = gemini_client.models.generate_content(model=modelo, contents=[prompt_relatoria, audio_file])
                                break
                            except Exception as err:
                                if "503" in str(err) or "UNAVAILABLE" in str(err):
                                    time.sleep(2 ** intento)
                                else:
                                    break
                        if response: break

                    if response:
                        st.session_state.texto_relatoria = response.text
                    else:
                        st.error("Servidores saturados. Cambia a ChatGPT.")

                    gemini_client.files.delete(name=audio_file.name)
                except Exception as e:
                    st.error(f"Error Gemini: {e}")

        if os.path.exists(audio_path_temporal):
            os.remove(audio_path_temporal)

# 5. Descarga PDF
if st.session_state.texto_relatoria:
    st.markdown("---")
    st.header("📄 Vista Previa")
    st.markdown(st.session_state.texto_relatoria)
    
    # Se envía la cantidad de asistentes para generar el PDF
    pdf_bytes = generar_pdf_oficial(st.session_state.texto_relatoria, num_asistentes)
    
    st.markdown("### 💾 Exportación Oficial")
    st.download_button(
        label="📥 Descargar Relatoría Oficial (PDF SEGEY)",
        data=pdf_bytes,
        file_name=f"Relatoria_CTE_{num_sesion.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary"
    )
