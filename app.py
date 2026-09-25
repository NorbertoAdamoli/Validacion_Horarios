import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la interfaz móvil
st.set_page_config(page_title="Validador de Horarios", page_icon="⏰", layout="centered")

st.title("⏰ Validador de Horarios Cátedra")
st.write("Pegá los horarios del sistema para controlar superposiciones y módulos.")

# 1. Cuadro de texto gigante para el celular
texto_bruto = st.text_area("Pegue aquí los horarios del sistema:", height=200, placeholder="Lunes\n09:55-10:35\n...")

if st.button("Procesar y Validar", type="primary"):
    if texto_bruto.strip():
        # Procesamiento del texto estructurado
        lineas = [linea.strip() for linea in texto_bruto.split('\n') if linea.strip()]
        
        datos = []
        dias_validos = ["Lunes", "Martes", "Miércoles", "Miercoles", "Jueves", "Viernes", "Sábado", "Sabado", "Domingo"]
        
        dia_actual = None
        
        for linea in lineas:
            if linea in dias_validos:
                dia_actual = linea
            elif "-" in linea and dia_actual:
                try:
                    inicio_str, fin_str = linea.split("-")
                    # Convertir a objeto tiempo para ordenar cronológicamente
                    h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                    h_fin = datetime.strptime(fin_str.strip(), "%H:%M").time()
                    
                    # Calcular minutos totales
                    dt_inicio = datetime.combine(datetime.today(), h_inicio)
                    dt_fin = datetime.combine(datetime.today(), h_fin)
                    minutos = int((dt_fin - dt_inicio).total_seconds() / 60)
                    
                    datos.append({
                        "Día": dia_actual,
                        "Inicio": h_inicio,
                        "Fin": h_fin,
                        "Texto_Horario": linea,
                        "Minutos": minutos,
                        "Horas Cátedra": round(minutos / 40, 1)
                    )
                except Exception:
                    pass # Ignora líneas con errores de formato

        if datos:
            df = pd.DataFrame(datos)
            
            # Definir orden de los días de la semana
            orden_dias = {d: i for i, d in enumerate(dias_validos)}
            df['Día_Num'] = df['Día'].map(orden_dias)
            
            # Ordenar cronológicamente (Día -> Hora de Inicio)
            df = df.sort_values(by=['Día_Num', 'Inicio']).drop(columns=['Día_Num'])
            
            # 2. Control de Superposiciones
            df['Superposición'] = False
            for i in range(len(df)):
                for j in range(len(df)):
                    if i != j and df.iloc[i]['Día'] == df.iloc[j]['Día']:
                        # Lógica de pisado de horarios
                        if (df.iloc[i]['Inicio'] >= df.iloc[j]['Inicio'] and df.iloc[i]['Inicio'] < df.iloc[j]['Fin']):
                            df.at[df.index[i], 'Superposición'] = True

            # Resumen general arriba
            total_horas_cat = df['Horas Cátedra'].sum()
            total_modulos = len(df)
            
            st.subheader("📊 Resumen del Bloque")
            col1, col2 = st.columns(2)
            col1.metric("Total Módulos", f"{total_modulos}")
            col2.metric("Total Horas Cátedra", f"{total_horas_cat} hs")
            
            # 3. Visualización en Tarjetas para el Celular
            st.subheader("📅 Cronograma Controlado")
            
            for index, fila in df.iterrows():
                hora_ini_form = fila['Inicio'].strftime('%H:%M')
                hora_fin_form = fila['Fin'].strftime('%H:%M')
                
                if fila['Superposición']:
                    # Tarjeta Roja de Alerta
                    st.error(f"⚠️ **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                             f"¡SUPERPOSICIÓN DETECTADA! Este horario se pisa con otro del mismo día.\n\n"
                             f"Módulos: 1 | Horas Cátedra: {fila['Horas Cátedra']}")
                else:
                    # Tarjeta Verde Correcta
                    st.success(f"🟢 **{fila['Día']} — {hora_ini_form} a {hora_fin_form}**\n\n"
                               f"Horario correcto.\n\n"
                               f"Módulos: 1 | Horas Cátedra: {fila['Horas Cátedra']}")
        else:
            st.warning("No se pudo reconocer ningún formato de día u horario válido.")
    else:
        st.info("Por favor, pegue el texto del sistema antes de procesar.")
    
