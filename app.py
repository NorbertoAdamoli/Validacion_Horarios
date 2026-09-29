import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la interfaz móvil y escritorio
st.set_page_config(page_title="Validador de Horarios", page_icon="⏰", layout="centered")

st.title("⏰ Validador de Horas Cátedra")
st.write("Pegue los horarios del sistema para controlar superposiciones y módulos.")

# Inicializamos el estado de la sesión para guardar los resultados procesados
if "resultados" not in st.session_state:
    st.session_state.resultados = None

# USAMOS clear_on_submit=True para limpiar el cuadro de texto automáticamente al presionar el botón
with st.form(key="validador_form", clear_on_submit=True):
    
    # Cuadro de texto gigante nativo
    texto_bruto = st.text_area(
        "Pegue aquí los horarios del sistema:", 
        height=200, 
        placeholder="Lunes\n09:55-10:35\nMartes\n08:00-09:20..."
    )
    
    # Botón nativo de envío del formulario
    procesar = st.form_submit_button("Procesar y Validar Horarios", type="primary")

# Procesamiento y Validación si se presionó el botón y hay texto
if procesar:
    if texto_bruto.strip():
        lineas = [linea.strip() for linea in texto_bruto.split('\n') if linea.strip()]
        
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
                        "Horas Cátedra": round(minutos / 40, 2)
                    })
                except Exception:
                    pass

        if datos:
            df = pd.DataFrame(datos)
            df['Día_Num'] = df['Día'].map(mapeo_orden)
            df = df.sort_values(by=['Día_Num', 'Inicio']).reset_index(drop=True)
            df = df.drop(columns=['Día_Num'])
            
            # Control de Superposiciones (Lógica de intervalos cruzados)
            df['Superposición'] = False
            for i in range(len(df)):
                for j in range(len(df)):
                    if i != j and df.iloc[i]['Día'] == df.iloc[j]['Día']:
                        ini_i, fin_i = df.iloc[i]['Inicio'], df.iloc[i]['Fin']
                        ini_j, fin_j = df.iloc[j]['Inicio'], df.iloc[j]['Fin']
                        if ini_i < fin_j and fin_i > ini_j:
                            df.at[i, 'Superposición'] = True
            
            # Guardamos el DataFrame generado con éxito en el estado
            st.session_state.resultados = df
        else:
            st.session_state.resultados = "invalido"
    else:
        st.session_state.resultados = "vacio"

# --- RENDERIZADO DE RESULTADOS ---
if st.session_state.resultados is not None:
    if isinstance(st.session_state.resultados, pd.DataFrame):
        df = st.session_state.resultados
        
        total_horas_cat = df['Horas Cátedra'].sum()
        total_modulos = len(df)
        
        # Conteo discriminado de módulos
        mod_35 = len(df[df['Minutos'] == 35])
        mod_40 = len(df[df['Minutos'] == 40])
        mod_60 = len(df[df['Minutos'] == 60])
        mod_otros = len(df[~df['Minutos'].isin([35, 40, 60])])
        
        st.subheader("📊 Resumen del Bloque")
        col1, col2 = st.columns(2)
        col1.metric("Total Módulos", f"{total_modulos}")
        col2.metric("Total Horas Cátedra", f"{total_horas_cat:.2f} hs")
        
        with st.expander("🔍 Ver desglose por tipo de módulo", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Módulos 35'**\n## {mod_35}")
            c2.markdown(f"**Módulos 40'**\n## {mod_40}")
            c3.markdown(f"**Módulos 60'**\n## {mod_60}")
            
            if mod_otros > 0:
                st.warning(f"⚠️ Hay **{mod_otros}** módulo(s) con una duración diferente a 35, 40 o 60 minutos.")
        
        # Tarjetas Cronograma
        st.subheader("📅 Cronograma Controlado")
        
        for index, fila in df.iterrows():
            hora_ini_form = fila['Inicio'].strftime('%H:%M')
            hora_fin_form = fila['Fin'].strftime('%H:%M')
            duracion = fila['Minutos']
            
            info_modulo = f"Duración: {duracion}' | Horas Cátedra: {fila['Horas Cátedra']:.2f}"
            
            if fila['Superposición']:
                st.error(f"⚠️ **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                         f"¡SUPERPOSICIÓN DETECTADA! Este horario se superpone con otro bloque.\n\n"
                         f"{info_modulo}")
            else:
                st.success(f"🟢 **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                           f"Horario correcto.\n\n"
                           f"{info_modulo}")
                           
    elif st.session_state.resultados == "invalido":
        st.warning("No se pudo reconocer ningún formato de día u horario válido. Verifique el texto pegado.")
    elif st.session_state.resultados == "vacio":
        st.info("Por favor, pegue el texto del sistema antes de procesar.")
