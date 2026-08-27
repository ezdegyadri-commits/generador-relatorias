import streamlit as st
import google.generativeai as genai
import tempfile
import os

# Configuración del Panel
st.set_page_config(page_title="Panel Directivo - Relatoría CTE", page_icon="🎛️", layout="wide")

# Autenticación segura
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta configurar la nueva clave GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

st.title("🎛️ Panel de Control Directivo: CTE USAER 2E")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Ajustes de la Sesión")
    num_sesion = st.selectbox("Sesión de CTE:", ["Fase Intensiva", "Primera Sesión", "Segunda Sesión", "Tercera Sesión"])
    enfoque_especial = st.text_input("Tema central:", placeholder="Ej. Ajustes razonables")

# MODO DE CAPTURA ROBUSTO
st.subheader("🎙️ Captura de Audio de la Plenaria")
modo_grabacion = st.radio(
    "Selecciona el método de captura:", 
    ["Subir archivo (Seguro si vas a cambiar de pestañas/presentar)", "Grabar en el navegador (Mejor para capturas cortas)"],
    horizontal=True
)

audio_path_temporal = None

col1, col2 = st.columns([1.5, 1])

with col1:
    if "Subir" in modo_grabacion:
        st.info("💡 Sugerencia: Abre la aplicación 'Grabadora de Voz' de tu equipo. Pon a grabar la sesión ahí, minimiza la ventana y expón tranquilamente. Al terminar, sube el archivo aquí.")
        archivo_subido = st.file_uploader("Arrastra tu archivo de audio (MP3, WAV, M4A)", type=["wav", "mp3", "m4a"])
        
        if archivo_subido:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Archivo cargado y listo para procesar.")
    else:
        st.warning("⚠️ Si cambias de pestaña por mucho tiempo, el navegador podría pausar la grabación.")
        # Componente nativo de Streamlit (más robusto visualmente)
        audio_grabado = st.audio_input("Haz clic para grabar en vivo")
        
        if audio_grabado:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_grabado.getvalue())
                audio_path_temporal = tmp_file.name
            st.success("Audio web capturado temporalmente.")

with col2:
    st.subheader("📝 Notas de Dirección")
    notas_directivo = st.text_area("Anota observaciones clave de la marcha (Opcional):", height=150)

# Lógica de Procesamiento IA
if audio_path_temporal:
    st.markdown("---")
    if st.button("🚀 Procesar Audio y Generar Relatoría Oficial", type="primary", use_container_width=True):
        with st.spinner("Subiendo audio a Gemini y redactando el documento..."):
            try:
                # Subir archivo mediante API de Gemini
                audio_file = genai.upload_file(path=audio_path_temporal)

                # Usamos el modelo Pro para audios largos y análisis profundo
                model = genai.GenerativeModel('gemini-1.5-pro')

                prompt = f"""
                Actúa como el secretario técnico de la USAER 2E. 
                Escucha el audio adjunto de la {num_sesion} del Consejo Técnico Escolar.
                Enfoque de la sesión: '{enfoque_especial}'.
                Notas de dirección: '{notas_directivo}'.

                Genera una relatoría institucional que contenga:
                1. **Contexto y Desarrollo:** Resumen del diálogo del colegiado.
                2. **Reflexiones y Retos:** Puntos críticos analizados.
                3. **Acuerdos y Compromisos:** Decisiones concretas acordadas.

                Tono directivo, formal y claro para archivo oficial.
                """

                response = model.generate_content([prompt, audio_file])
                
                st.markdown("---")
                st.header("📄 Relatoría Oficial Generada")
                st.markdown(response.text)

                # Limpieza de archivos
                os.remove(audio_path_temporal)
                genai.delete_file(audio_file.name)

            except Exception as e:
                st.error(f"Error al procesar: {e}")
