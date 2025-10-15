# -----------------------------------------------------------
# Dashboard Institucional de Emisiones del SEN
# Tipo Coordinador Eléctrico Nacional - Streamlit
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import streamlit.components.v1 as components

# --- Configuración regional (Chile) ---
locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')

# --- Configuración de la página ---
st.set_page_config(page_title="Emisiones SEN - Dashboard", layout="wide")

# --- Cargar datos ---
df = pd.read_excel("enero_2022_emisiones.xlsx")
df["FechaHora"] = pd.to_datetime(df["FechaHora"])

# --- Encabezado estilo Coordinador ---
st.markdown(
    """
    <h1 style='font-weight:700; color:#003366; margin-bottom:0;'>Indicadores de Emisiones del SEN</h1>
    <p style='color:#5a5a5a; margin-top:4px;'>Sistema Eléctrico Nacional (SEN) · Datos horarios de emisiones</p>
    <hr style="border: 1px solid #e0e0e0;">
    """,
    unsafe_allow_html=True,
)

# --- Selector de fecha ---
fechas_disponibles = df["FechaHora"].dt.date.unique()
fecha_seleccionada = st.selectbox(
    "Selecciona un día para analizar:",
    sorted(fechas_disponibles),
    index=0
)

# --- Filtrar datos para el día y el mes ---
anio_actual = pd.to_datetime(fecha_seleccionada).year
mes_actual = pd.to_datetime(fecha_seleccionada).month
df_dia = df[df["FechaHora"].dt.date == fecha_seleccionada]
df_mes = df[(df["FechaHora"].dt.month == mes_actual) & (df["FechaHora"].dt.year == anio_actual)]

# --- Cálculos para indicadores ---
total_mes = df_mes["CO2e_t"].sum()
gen_mes = df_mes["Generacion_MWh"].sum()
promedio_mes = (total_mes / gen_mes) if gen_mes > 0 else 0

# --- Panel de indicadores superiores ---
col1, col2, col3 = st.columns(3)
col1.metric("Emisiones totales mensuales", f"{locale.format_string('%.0f', total_mes, grouping=True).replace(',', '.') } mTCO₂")
col2.metric("Generación térmica mensual (Carbón, Gas Natural, Diésel y Fuel Oil)", f"{locale.format_string('%.0f', gen_mes, grouping=True).replace(',', '.')} MWh")
col3.metric("Intensidad promedio mensual", f"{str(promedio_mes).replace('.', ',')[:6]} tCO₂eq/MWh")

# -----------------------------------------------------------
#  Gráfico 1: Emisiones horarias por día seleccionado
# -----------------------------------------------------------
st.markdown(
    """
    <h2 style='font-weight:600; margin-top:40px;'>Emisiones Horarias (tCO₂/h)</h2>
    <p style='color:gray; margin-top:0;'>Suma de todas las centrales térmicas en el día seleccionado</p>
    """,
    unsafe_allow_html=True,
)

emisiones_dia = (
    df_dia.groupby("FechaHora")["CO2e_t"]
    .sum()
    .reset_index()
    .rename(columns={"CO2e_t": "Emisiones_tCO2_h"})
)

fig_emisiones = px.line(
    emisiones_dia,
    x="FechaHora",
    y="Emisiones_tCO2_h",
    labels={"FechaHora": "Hora", "Emisiones_tCO2_h": "mTCO₂/h"},
    line_shape="spline"
)

# --- Formato chileno en ejes y hover ---
fig_emisiones.update_traces(
    line=dict(color="#003366", width=3),
    hovertemplate="<b>%{x|%H:%M}</b><br>%{y:,.0f} tCO₂/h<extra></extra>"
)
fig_emisiones.update_layout(
    template="simple_white",
    hovermode="x unified",
    font=dict(size=14),
    xaxis_title="Hora del día",
    yaxis_title="mTCO₂/h",
    yaxis=dict(
        separatethousands=True,
        tickformat=",",
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=30, t=40, b=40)
)
st.plotly_chart(fig_emisiones, use_container_width=True)


# -----------------------------------------------------------
#  Gráfico 2: Distribución CAISO-style
# -----------------------------------------------------------
st.markdown(
    """
    <h2 style='font-weight:600; margin-top:60px;'>Distribución de CO₂ por tipo de combustible</h2>
    <p style='color:gray; margin-top:0;'>Porcentaje de emisiones térmicas separadas por recurso (tCO₂/h)</p>
    """,
    unsafe_allow_html=True,
)

# --- Slider de hora ---
horas_disponibles = sorted(df_dia["FechaHora"].dt.hour.unique())
hora_elegida = st.slider(
    "Selecciona la hora:",
    min_value=int(min(horas_disponibles)),
    max_value=int(max(horas_disponibles)),
    value=int(min(horas_disponibles)),
    step=1,
    format="%d",
)

df_hora = df_dia[df_dia["FechaHora"].dt.hour == hora_elegida]

# --- Agrupar y calcular porcentajes ---
co2_mix = (
    df_hora.groupby("Subtipo")["CO2e_t"]
    .sum()
    .reset_index()
    .rename(columns={"CO2e_t": "CO2e_t_h"})
)
co2_mix["Participacion_%"] = co2_mix["CO2e_t_h"] / co2_mix["CO2e_t_h"].sum() * 100

# --- Colores ---
colores_caiso = {
    "Carbón": "#3c3c3c",
    "Gas Natural": "#d87b00",
    "Diésel": "#9e2a2b",
    "Fuel Oil": "#5f0f40",
}

# --- Anillo ---
fig_caiso = px.pie(
    co2_mix,
    names="Subtipo",
    values="CO2e_t_h",
    color="Subtipo",
    color_discrete_map=colores_caiso,
    hole=0.65,
)
fig_caiso.update_traces(
    textinfo="percent",
    textposition="inside",
    textfont=dict(size=14, color="white"),
    hovertemplate="%{label}: %{percent:.1%} (%{value:,.0f} tCO₂/h)",
)
total_hora = co2_mix["CO2e_t_h"].sum()
fig_caiso.update_layout(
    annotations=[
        dict(
            text=f"<b>{hora_elegida:02d}:00</b><br>{fecha_seleccionada.strftime('%d-%m-%Y')}<br><br><b>{total_hora:,.0f} tCO₂/h</b>",
            x=0.5,
            y=0.5,
            font_size=14,
            showarrow=False,
        )
    ],
    showlegend=False,
    template="simple_white",
)

col1, col2 = st.columns([0.55, 0.45])
with col1:
    st.plotly_chart(fig_caiso, use_container_width=True)

with col2:
    st.markdown("<h4 style='margin-top:10px;'>Detalle por combustible</h4>", unsafe_allow_html=True)
    legend_html = "<div style='margin-top:15px;font-family:Arial, sans-serif;'>"
    for _, row in co2_mix.iterrows():
        color = colores_caiso.get(row["Subtipo"], "#cccccc")
        porcentaje = str(round(row["Participacion_%"], 1)).replace('.', ',')
        valor = locale.format_string('%.0f', row["CO2e_t_h"], grouping=True).replace(',', '.')
        legend_html += f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    padding:6px 0;border-bottom:1px solid #f0f0f0;'>
            <div style='display:flex;align-items:center;'>
                <div style='width:14px;height:14px;border-radius:50%;
                            background-color:{color};margin-right:10px;'></div>
                <div style='font-weight:600;font-size:15px;color:{color};'>
                    {row["Subtipo"]} CO₂
                </div>
            </div>
            <div style='text-align:right;font-size:13px;color:#333;'>
                {porcentaje}%<br>
                <span style='color:#777;'>{valor} tCO₂/h</span>
            </div>
        </div>
        """
    legend_html += "</div>"
    components.html(legend_html, height=350, scrolling=True)

# -----------------------------------------------------------
#  Gráfico 3: CO₂ por tipo de recurso (tCO₂/h)
# -----------------------------------------------------------
st.markdown(
    """
    <h2 style='font-weight:600; margin-top:60px;'>Emisiones horarias por tipo de combustible</h2>
    <p style='color:gray; margin-top:0;'>CO₂ separado por recurso, promedio horario</p>
    """,
    unsafe_allow_html=True,
)

df["FechaHora"] = pd.to_datetime(df["FechaHora"], errors="coerce")
df["CO2e_t"] = pd.to_numeric(df["CO2e_t"], errors="coerce")
df_dia_emis = df[df["FechaHora"].dt.date == fecha_seleccionada]

if not df_dia_emis.empty:
    emis_horas = (
        df_dia_emis.groupby([df_dia_emis["FechaHora"].dt.hour, "Subtipo"])["CO2e_t"]
        .sum()
        .reset_index()
        .rename(columns={"FechaHora": "Hora", "CO2e_t": "Emisiones_tCO2_h"})
    )
    emis_horas = emis_horas.rename(columns={"FechaHora": "Hora"})

    fig_trend = px.line(
        emis_horas,
        x="Hora",
        y="Emisiones_tCO2_h",
        color="Subtipo",
        color_discrete_map=colores_caiso,
        line_shape="spline",
        markers=True,
    )

    fig_trend.update_traces(
        line=dict(width=3),
        marker=dict(size=8, line=dict(width=1, color="white")),
        hovertemplate="<b>%{fullData.name}</b><br>%{x}:00 — %{y:,.0f} tCO₂/h<extra></extra>",
    )

    fig_trend.update_layout(
        template="simple_white",
        xaxis_title="Hora del día",
        yaxis_title="tCO₂/h",
        yaxis=dict(separatethousands=True, tickformat=","),
        hovermode="x unified",
        font=dict(size=14),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig_trend, use_container_width=True)


# -----------------------------------------------------------
#  Gráfico 4: Intensidad térmica horaria
# -----------------------------------------------------------
st.markdown(
    """
    <h2 style='font-weight:600; margin-top:60px;'>Intensidad de Carbono Térmica (tCO₂eq/MWh)</h2>
    <p style='color:gray; margin-top:0;'>Promedio ponderado hora a hora del mes seleccionado</p>
    """,
    unsafe_allow_html=True,
)

intensidad_mes = (
    df_mes.groupby("FechaHora")[["CO2e_t", "Generacion_MWh"]].sum().reset_index()
)
intensidad_mes["Intensidad_tCO2eq_MWh"] = (
    intensidad_mes["CO2e_t"] / intensidad_mes["Generacion_MWh"]
)
promedio_mes_int = intensidad_mes["Intensidad_tCO2eq_MWh"].mean()

fig_int = px.line(
    intensidad_mes,
    x="FechaHora",
    y="Intensidad_tCO2eq_MWh",
    line_shape="spline",
)
fig_int.add_hline(
    y=promedio_mes_int,
    line_dash="dot",
    line_color="#1b4332",
    annotation_text=f"Promedio mensual: {str(round(promedio_mes_int,3)).replace('.', ',')} tCO₂eq/MWh",
    annotation_position="top right",
)
fig_int.update_traces(
    line=dict(color="#2a9d46", width=2.5),
    hovertemplate="%{x|%d-%m-%Y %H:%M}<br>%{y:,.3f} tCO₂eq/MWh<extra></extra>",
)
fig_int.update_layout(
    template="simple_white",
    hovermode="x unified",
    yaxis=dict(separatethousands=True, tickformat=","),
    xaxis_title="Fecha",
    yaxis_title="tCO₂eq/MWh",
)
st.plotly_chart(fig_int, use_container_width=True)

# -----------------------------------------------------------
#  Pie de página
# -----------------------------------------------------------
st.markdown(
    """
    <hr style="border: 1px solid #e0e0e0;">
    <p style='font-size:13px; color:gray;'>
    Fuente: Datos horarios de emisiones estimadas de generación térmica del SEN.<br>
    Elaboración: Coordinador Eléctrico Nacional - Unidad de Innovación.
    </p>
    """,
    unsafe_allow_html=True,
)

