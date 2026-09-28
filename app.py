import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# Configuración de la interfaz móvil
st.set_page_config(page_title="Validador de Horarios", page_icon="⏰", layout="centered")

st.title("⏰ Validador de Horarios Cátedra")
st.write("Copia los horarios del sistema y presiona el botón para validar al instante.")

# Se inicializa el estado del texto si no existe
if "texto_entrada" not in st.session_state:
    st.session_state["texto_entrada"] = ""

# Parámetro en la URL para recibir los datos desde JavaScript de forma segura
query_params = st.query_params
if "clipboard_data" in query_params:
    st.session_state["texto_entrada"] = query_params["clipboard_data"]
    st.query_params.clear()

# 1. Cuadro de texto gigante para el celular (muestra el contenido actual)
texto_bruto = st.text_area(
    "Contenido a validar:", 
    value=st.session_state["texto_entrada"], 
    height=200, 
    placeholder="Los horarios pegados aparecerán aquí..."
)

# 2. Botón optimizado con JavaScript para leer la memoria del celular
boton_html = """
<button id="btn-paste" style="
    background-color: #ff4b4b;
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
    cursor: pointer;
    width: 100%;
    box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
">
📋 Pegar desde Memoria y Validar
</button>

<script>
document.getElementById('btn-paste').addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            const url = new URL(window.parent.location.href);
            url.searchParams.set('clipboard_data', text);
            window.parent.location.href = url.href;
        } else {
            alert("El portapapeles está vacío o no contiene texto.");
        }
    } catch (err) {
        alert("Para validar con un toque, por favor permite el acceso al portapapeles cuando el navegador te lo solicite.");
    }
});
</script>
"""

components.html(boton_html, height=60)

# 3. Procesamiento y Validación Automática si hay texto
if st.session_state["texto_entrada"].strip():
    lineas = [linea.strip() for linea in st.session_state["texto_entrada"].split('\n') if linea.strip()]
    
    datos = []
    dias_validos = ["Lunes", "Martes", "Miércoles", "Miercoles", "Jueves", "Viernes", "Sábado", "Sabado", "Domingo"]
    
    mapeo_orden = {
        "Lunes": 0, "Martes": 1, "Miércoles": 2, "Miercoles": 2, 
        "Jueves": 3, "Viernes": 4, "Sábado": 5, "Sabado": 5, "Domingo": 6
    }
    
    dia_actual = None
    
    for linea in lineas:
        if linea in dias_validos:
            dia_actual = linea
        elif "-" in linea and dia_actual:
            try:
                inicio_str, fin_str = linea.split("-")
                h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                h_fin = datetime.strptime(fin_str.strip(), "%H:%M").time()
                
                dt_inicio = datetime.combine(datetime.today(), h_inicio)
                dt_fin = datetime.combine(datetime.today(), h_fin)
                minutos = int((dt_fin - dt_inicio).total_seconds() / 60)
                
                datos.append({
                    "Día": dia_actual,
                    "Inicio": h_inicio,
                    "Fin": h_fin,
                    "Texto_Horario": linea,
                    "Minutos": minutos,
                    "Horas Cátedra": round(minutos / 40, 2)}
                )
            except Exception:
                pass

    if datos:
        df = pd.DataFrame(datos)
        df['Día_Num'] = df['Día'].map(mapeo_orden)
        df = df.sort_values(by=['Día_Num', 'Inicio']).reset_index(drop=True)
        df = df.drop(columns=['Día_Num'])
        
        df['Superposición'] = False
        for i in range(len(df)):
            for j in range(len(df)):
                if i != j and df.iloc[i]['Día'] == df.iloc[j]['Día']:
                    ini_i, fin_i = df.iloc[i]['Inicio'], df.iloc[i]['Fin']
                    ini_j, fin_j = df.iloc[j]['Inicio'], df.iloc[j]['Fin']
                    if ini_i < fin_j and fin_i > ini_j:
                        df.at[i, 'Superposición'] = True

        total_horas_cat = df['Horas Cátedra'].sum()
        total_modulos = len(df)
        
        # --- CONTEO DISCRIMINADO DE MÓDULOS ---
        mod_35 = len(df[df['Minutos'] == 35])
        mod_40 = len(df[df['Minutos'] == 40])
        mod_60 = len(df[df['Minutos'] == 60])
        mod_otros = len(df[~df['Minutos'].isin([35, 40, 60])])
        
        st.subheader("📊 Resumen del Bloque")
        col1, col2 = st.columns(2)
        col1.metric("Total Módulos", f"{total_modulos}")
        col2.metric("Total Horas Cátedra", f"{total_horas_cat:.2f} hs")
        
        # Panel expandible para no saturar la pantalla del celular pero ver el detalle al instante
        with st.expander("🔍 Ver desglose por tipo de módulo", expanded=True):
            # Usamos columnas pequeñas para diseño móvil amigable
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Módulos 35'**\n## {mod_35}")
            c2.markdown(f"**Módulos 40'**\n## {mod_40}")
            c3.markdown(f"**Módulos 60'**\n## {mod_60}")
            
            if mod_otros > 0:
                st.warning(f"⚠️ Hay **{mod_otros}** módulo(s) con una duración diferente a 35, 40 o 60 minutos.")
        
        # --- TARJETAS CRONOGRAMA ---
        st.subheader("📅 Cronograma Controlado")
        
        for index, fila in df.iterrows():
            hora_ini_form = fila['Inicio'].strftime('%H:%M')
            hora_fin_form = fila['Fin'].strftime('%H:%M')
            duracion = fila['Minutos']
            
            info_modulo = f"Duración: {duracion}' | Horas Cátedra: {fila['Horas Cátedra']:.2f}"
            
            if fila['Superposición']:
                st.error(f"⚠️ **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                         f"¡SUPERPOSICIÓN DETECTADA! Este horario se pisa con otro bloque.\n\n"
                         f"{info_modulo}")
            else:
                st.success(f"🟢 **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                           f"Horario correcto.\n\n"
                           f"{info_modulo}")
    else:
        st.warning("No se pudo reconocer ningún formato de día u horario válido.")

