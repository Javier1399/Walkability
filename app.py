"""
URBAN-PULSE v4 — Simulador de Intervención por Zonas
=====================================================
Requisitos:
    pip install streamlit geopandas pydeck pandas numpy plotly

Estructura:
    app.py
    data/
        Atitalaquia_urban_analysis_final.gpkg
        Guanajuato_urban_analysis_final.gpkg
    .streamlit/
        config.toml
"""

import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import textwrap

# ─── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="URBAN-PULSE v4",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #070B12 !important;
    font-family: 'Space Grotesk', sans-serif;
}
[data-testid="stHeader"]  { background: transparent; height: 0; }
[data-testid="stSidebar"] {
    background-color: #0A0F1A !important;
    border-right: 1px solid #162032;
}
[data-testid="stSidebar"] * { color: #8B98A8 !important; }
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong { color: #C5CDD8 !important; }

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
    max-width: 100% !important;
}

/* ── Header ── */
.up-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 10px 0;
    border-bottom: 1px solid #162032;
    margin-bottom: 12px;
}
.up-logo {
    font-family: 'Space Mono', monospace;
    font-size: 15px;
    font-weight: 700;
    color: #38BDF8;
    letter-spacing: 0.06em;
}
.up-tagline {
    font-size: 10px;
    color: #374151;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 8px; margin-bottom: 10px; }
.kpi {
    flex: 1;
    background: #0A0F1A;
    border: 1px solid #162032;
    border-top: 2px solid;
    border-radius: 6px;
    padding: 10px 12px;
}
.kpi.g { border-top-color: #10D97E; }
.kpi.r { border-top-color: #F43F5E; }
.kpi.b { border-top-color: #38BDF8; }
.kpi.a { border-top-color: #F59E0B; }
.kpi-lbl {
    font-size: 9px; font-weight: 600;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #374151; margin-bottom: 3px;
}
.kpi-val {
    font-family: 'Space Mono', monospace;
    font-size: 19px; font-weight: 700; line-height: 1;
}
.kpi-val.g { color: #10D97E; }
.kpi-val.r { color: #F43F5E; }
.kpi-val.b { color: #38BDF8; }
.kpi-val.a { color: #F59E0B; }
.kpi-sub { font-size: 9px; color: #374151; margin-top: 2px; }

/* ── Panel cards ── */
.panel {
    background: #0A0F1A;
    border: 1px solid #162032;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}
.panel-title {
    font-size: 9px; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: #38BDF8; margin-bottom: 10px;
}

/* ── Zona badges ── */
.zbadge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 4px;
    font-size: 11px; font-weight: 600;
    margin-bottom: 6px;
}
.zbadge-viable    { background:#052E16; color:#10D97E; border:1px solid #10D97E44; }
.zbadge-esfuerzo  { background:#1C1007; color:#F59E0B; border:1px solid #F59E0B44; }
.zbadge-estructural { background:#1A0D14; color:#F87171; border:1px solid #F87171AA; }
.zbadge-nucleo    { background:#111827; color:#6B7280; border:1px solid #374151; }
.zbadge-excl      { background:#190010; color:#F43F5E; border:1px solid #F43F5E; }

/* ── Sim result box ── */
.sim-result {
    background: linear-gradient(135deg, #052E16, #064E3B);
    border: 1px solid #10D97E55;
    border-radius: 6px;
    padding: 10px 13px;
    margin-top: 8px;
}
.sim-delta {
    font-family: 'Space Mono', monospace;
    font-size: 20px; font-weight: 700;
    color: #10D97E;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #374151 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #38BDF8 !important;
    border-bottom: 2px solid #38BDF8 !important;
}

/* ── Misc ── */
#MainMenu, footer { visibility: hidden; }
hr { border-color: #162032 !important; }
</style>
""", unsafe_allow_html=True)


# ─── CONSTANTES ────────────────────────────────────────────────────────────────
RUTAS = {
    "Atitalaquia": "data/Atitalaquia_urban_analysis_final.gpkg",
    "Guanajuato":  "data/Guanajuato_urban_analysis_final.gpkg",
}

# Colores RGB para pydeck por rim_clasificacion
RIM_COLORS = {
    "Consolidado":               [16,  217, 126, 200],
    "En desarrollo":             [56,  189, 248, 180],
    "Transición viable":         [16,  217, 126, 230],
    "Transición con esfuerzo":   [245, 158,  11, 220],
    "Fronterizo estructural":    [248, 113, 113, 210],
    "Núcleo de periferia":       [75,   85, 99,  170],
    "Exclusión territorial":     [244,  63,  94, 240],
}
RIM_DEFAULT = [50, 60, 80, 150]

# Orden narrativo de clasificaciones RIM
RIM_ORDER = [
    "Consolidado", "En desarrollo",
    "Transición viable", "Transición con esfuerzo", "Fronterizo estructural",
    "Núcleo de periferia", "Exclusión territorial",
]

# Impactos documentados del RIM v4 (deltas medios del análisis de sensibilidad)
# Usados para la simulación de intervención agregada
IMPACTOS_INTERVENCION = {
    "Mejorar conectividad vial":          {"walk_score_delta": 0.045, "ict_delta": 0.3},
    "Reducir longitud de segmentos viales": {"walk_score_delta": 0.025, "ict_delta": 0.1},
    "Reducir calles sin salida":          {"walk_score_delta": 0.018, "ict_delta": 0.1},
    "Añadir servicio de alimentación":    {"walk_score_delta": 0.062, "ict_delta": 0.8},
    "Incrementar oferta alimentaria":     {"walk_score_delta": 0.055, "ict_delta": 0.6},
    "Añadir espacio de ocio/recreación":  {"walk_score_delta": 0.040, "ict_delta": 0.5},
    "Incrementar oferta recreativa":      {"walk_score_delta": 0.035, "ict_delta": 0.4},
    "Diversificar tipos de amenidades":   {"walk_score_delta": 0.048, "ict_delta": 0.6},
}

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8B98A8", size=11, family="Space Grotesk"),
    margin=dict(l=8, r=8, t=28, b=8),
)


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def safe_float(v, default=0.0) -> float:
    try:
        f = float(v)
        return default if np.isnan(f) else f
    except Exception:
        return default

def safe_str(v, default="—") -> str:
    if v is None: return default
    if isinstance(v, float) and np.isnan(v): return default
    return str(v)

def time_color(m: float) -> str:
    if m < 5:   return "#10D97E"
    if m < 10:  return "#38BDF8"
    if m < 20:  return "#F59E0B"
    if m < 45:  return "#F87171"
    return "#F43F5E"

def ws_to_class(ws: float) -> str:
    if ws >= 0.65: return "g"
    if ws >= 0.40: return "a"
    return "r"

def rim_badge_class(rim: str) -> str:
    mapping = {
        "Transición viable":        "zbadge-viable",
        "Transición con esfuerzo":  "zbadge-esfuerzo",
        "Fronterizo estructural":   "zbadge-estructural",
        "Núcleo de periferia":      "zbadge-nucleo",
        "Exclusión territorial":    "zbadge-excl",
        "Consolidado":              "zbadge-viable",
        "En desarrollo":            "zbadge-viable",
    }
    return mapping.get(rim, "zbadge-nucleo")


# ─── CARGA DE DATOS ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos…")
def cargar_ciudad(ruta: str) -> pd.DataFrame:
    try:
        gdf = gpd.read_file(ruta)
    except Exception as e:
        st.error(f"No se pudo cargar: `{ruta}`\n\n{e}")
        st.stop()

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    # Coordenadas para PolygonLayer
    def coords(geom):
        if geom is None or geom.is_empty: return []
        if geom.geom_type == "MultiPolygon":
            geom = list(geom.geoms)[0]
        return [[x, y] for x, y in zip(*geom.exterior.coords.xy)]

    gdf["coordinates"] = gdf["geometry"].apply(coords)

    # Centroide en CRS métrico → lon/lat
    cent = gdf["geometry"].to_crs("EPSG:6372").centroid.to_crs("EPSG:4326")
    gdf["lon"] = cent.x
    gdf["lat"] = cent.y

    # Color por RIM — pre-calculado, O(n) una sola vez
    def rim_rgba(label):
        return RIM_COLORS.get(label, RIM_DEFAULT)

    if "rim_clasificacion" in gdf.columns:
        rgba = gdf["rim_clasificacion"].apply(rim_rgba)
        gdf["cr"] = rgba.apply(lambda x: x[0])
        gdf["cg"] = rgba.apply(lambda x: x[1])
        gdf["cb"] = rgba.apply(lambda x: x[2])
        gdf["ca"] = rgba.apply(lambda x: x[3])
    else:
        gdf["cr"], gdf["cg"], gdf["cb"], gdf["ca"] = 80, 90, 110, 160

    # Walk score → color alternativo
    def ws_rgb(ws):
        s = float(np.clip(ws, 0, 1))
        if s < 0.5:
            return [255, int(s * 2 * 200), 40]
        return [int((1 - (s - 0.5) * 2) * 255), 200, 40]

    ws_col = gdf["walk_score"].fillna(0)
    ws_rgb_arr = ws_col.apply(ws_rgb)
    gdf["wsr"] = ws_rgb_arr.apply(lambda x: x[0])
    gdf["wsg"] = ws_rgb_arr.apply(lambda x: x[1])
    gdf["wsb"] = ws_rgb_arr.apply(lambda x: x[2])

    # Columnas de display para tooltip
    gdf["ws_pct"]   = (ws_col * 100).round(1).astype(str) + "%"
    gdf["pop_fmt"]  = gdf["population_count_1_2km"].fillna(0).astype(int)\
                        .apply(lambda x: f"{x:,}")
    wt = gdf.get("walk_time_nearest", pd.Series([np.nan]*len(gdf)))
    gdf["wt_fmt"]   = wt.fillna(0).apply(lambda x: f"{x:.0f} min")

    return gdf.drop(columns=["geometry"])


@st.cache_data(show_spinner="Cargando datos comparativos…")
def cargar_ambas() -> dict:
    out = {}
    for nombre, ruta in RUTAS.items():
        try:
            gdf = gpd.read_file(ruta)
            out[nombre] = pd.DataFrame(gdf.drop(columns=["geometry"]))
        except Exception:
            pass
    return out


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
_defaults = {
    "ciudad":       "Guanajuato",
    "rim_filtro":   None,        # clasificación RIM seleccionada
    "sim_result":   None,        # dict con resultado de simulación
    "color_mode":   "RIM",       # "RIM" o "Walk Score"
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── CARGA ─────────────────────────────────────────────────────────────────────
df_raw = cargar_ciudad(RUTAS[st.session_state["ciudad"]])


# ─── HEADER ───────────────────────────────────────────────────────────────────
hc1, hc2, hc3 = st.columns([2, 2, 1.5])
with hc1:
    st.markdown("""
    <div class="up-logo">⬡ URBAN-PULSE v4</div>
    <div class="up-tagline">Simulador de Intervención Urbana · México</div>
    """, unsafe_allow_html=True)

with hc2:
    ciudad_sel = st.radio(
        "Ciudad",
        options=["Atitalaquia", "Guanajuato"],
        horizontal=True,
        index=["Atitalaquia", "Guanajuato"].index(st.session_state["ciudad"]),
        label_visibility="collapsed",
    )
    if ciudad_sel != st.session_state["ciudad"]:
        st.session_state.update({
            "ciudad":     ciudad_sel,
            "rim_filtro": None,
            "sim_result": None,
        })
        st.rerun()

with hc3:
    color_mode = st.radio(
        "Colorear mapa",
        ["RIM", "Walk Score"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["color_mode"] = color_mode

st.divider()


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.divider()

    st.markdown("**Mostrar en mapa**")
    rim_disp = [r for r in RIM_ORDER if r in df_raw.get("rim_clasificacion",
                pd.Series()).unique().tolist()] \
        if "rim_clasificacion" in df_raw.columns else RIM_ORDER

    rim_activos = [
        r for r in rim_disp
        if st.checkbox(r, value=True, key=f"rim_{r}")
    ]

    st.divider()
    st.markdown("**Seleccionar zona para análisis**")
    rim_opciones = ["— Ver ciudad completa —"] + [
        r for r in RIM_ORDER
        if r not in ["Consolidado", "En desarrollo"]
        and r in rim_disp
    ]
    rim_sel = st.selectbox(
        "Zona de intervención",
        rim_opciones,
        label_visibility="collapsed",
    )
    if rim_sel == "— Ver ciudad completa —":
        st.session_state["rim_filtro"] = None
    else:
        if rim_sel != st.session_state["rim_filtro"]:
            st.session_state["rim_filtro"] = rim_sel
            st.session_state["sim_result"] = None

    st.divider()
    st.caption("Pipeline: INEGI + OSM\nPCA v2 · K-Means · RIM v4")


# ─── FILTRAR DATOS ─────────────────────────────────────────────────────────────
if "rim_clasificacion" in df_raw.columns and rim_activos:
    df = df_raw[df_raw["rim_clasificacion"].isin(rim_activos)].copy()
else:
    df = df_raw.copy()

# Zona seleccionada para análisis
rim_zona = st.session_state["rim_filtro"]
df_zona = df_raw[df_raw["rim_clasificacion"] == rim_zona].copy() \
    if rim_zona and "rim_clasificacion" in df_raw.columns else pd.DataFrame()


# ─── KPIs — reflejan filtros activos del sidebar ────────────────────────────────
ws_mean   = df["walk_score"].mean()
pop_media = df["population_count_1_2km"].mean()  # media por hex, no suma
n_hex     = len(df)
n_hex_raw = len(df_raw)
pct_excl  = (df["rim_clasificacion"] == "Exclusión territorial").mean() * 100 \
    if "rim_clasificacion" in df.columns else 0.0
pct_trans = df["rim_clasificacion"].isin(
    ["Transición viable", "Transición con esfuerzo"]).mean() * 100 \
    if "rim_clasificacion" in df.columns else 0.0

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi g">
        <div class="kpi-lbl">Caminabilidad media</div>
        <div class="kpi-val g">{ws_mean:.3f}</div>
        <div class="kpi-sub">Walk Score 0–1</div>
    </div>
    <div class="kpi r">
        <div class="kpi-lbl">Exclusión territorial</div>
        <div class="kpi-val r">{pct_excl:.1f}%</div>
        <div class="kpi-sub">&gt;45 min a cualquier servicio</div>
    </div>
    <div class="kpi a">
        <div class="kpi-lbl">Zonas en transición</div>
        <div class="kpi-val a">{pct_trans:.1f}%</div>
        <div class="kpi-sub">hexágonos fronterizos</div>
    </div>
    <div class="kpi b">
        <div class="kpi-lbl">Pob. media por hexágono</div>
        <div class="kpi-val b">{pop_media:,.0f}</div>
        <div class="kpi-sub">hab. en radio 1.2 km</div>
    </div>
    <div class="kpi b">
        <div class="kpi-lbl">Hexágonos visibles</div>
        <div class="kpi-val b">{n_hex:,}</div>
        <div class="kpi-sub">de {n_hex_raw:,} totales</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── TABS ──────────────────────────────────────────────────────────────────────
tab_mapa, tab_sim, tab_analisis = st.tabs([
    "⬡  MAPA DE OPORTUNIDADES",
    "⚡  SIMULADOR DE INTERVENCIÓN",
    "📊  ANÁLISIS ESTRATÉGICO",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MAPA DE OPORTUNIDADES
# ══════════════════════════════════════════════════════════════════════════════
with tab_mapa:
    mc1, mc2 = st.columns([4, 1.6])

    with mc1:
        # Color según modo
        if st.session_state["color_mode"] == "RIM":
            fill_col = ["cr", "cg", "cb", "ca"]
        else:
            fill_col = ["wsr", "wsg", "wsb", "ca"]

        # Resaltar zona seleccionada: bajar alpha del resto
        df_mapa = df.copy()
        if rim_zona and "rim_clasificacion" in df_mapa.columns:
            mask_otros = df_mapa["rim_clasificacion"] != rim_zona
            df_mapa.loc[mask_otros, "ca"] = 40

        capa = pdk.Layer(
            "PolygonLayer",
            data=df_mapa,
            get_polygon="coordinates",
            get_fill_color=fill_col,
            get_line_color=[10, 20, 35, 100],
            line_width_min_pixels=0.3,
            pickable=True,
            auto_highlight=True,
            highlight_color=[255, 255, 255, 50],
            extruded=False,   # sin 3D — más rápido y más legible
        )

        vista = pdk.ViewState(
            latitude=df["lat"].median(),
            longitude=df["lon"].median(),
            zoom=12 if st.session_state["ciudad"] == "Atitalaquia" else 11,
            pitch=0,
            bearing=0,
        )

        tooltip = {
            "html": """
            <div style="background:#070B12;border:1px solid #162032;
                        border-radius:6px;padding:9px 12px;
                        font-family:'Space Grotesk',sans-serif;min-width:180px;">
                <div style="font-size:9px;letter-spacing:.12em;text-transform:uppercase;
                            color:#38BDF8;margin-bottom:4px;">⬡ {rim_clasificacion}</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:4px;">
                    <div>
                        <div style="font-size:9px;color:#374151;">Walk Score</div>
                        <div style="font-size:15px;font-weight:700;
                                    font-family:'Space Mono';color:#10D97E;">{ws_pct}</div>
                    </div>
                    <div>
                        <div style="font-size:9px;color:#374151;">T. más cercano</div>
                        <div style="font-size:13px;color:#F59E0B;
                                    font-family:'Space Mono';">{wt_fmt}</div>
                    </div>
                    <div>
                        <div style="font-size:9px;color:#374151;">Población</div>
                        <div style="font-size:12px;color:#8B98A8;">{pop_fmt}</div>
                    </div>
                    <div>
                        <div style="font-size:9px;color:#374151;">ID</div>
                        <div style="font-size:12px;color:#8B98A8;">{id}</div>
                    </div>
                </div>
            </div>""",
            "style": {"color": "white"},
        }

        st.pydeck_chart(
            pdk.Deck(
                layers=[capa],
                initial_view_state=vista,
                tooltip=tooltip,
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            ),
            width="stretch",
            height=500,
        )

        # Leyenda
        if st.session_state["color_mode"] == "RIM":
            items = "".join([
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'margin-right:12px;">'
                f'<span style="width:10px;height:10px;border-radius:2px;'
                f'background:rgb({c[0]},{c[1]},{c[2]});display:inline-block;"></span>'
                f'<span style="font-size:10px;color:#6B7280;">{lbl}</span></span>'
                for lbl, c in RIM_COLORS.items()
            ])
            st.markdown(f'<div style="margin-top:4px;">{items}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
                <span style="font-size:10px;color:#6B7280;">0.0</span>
                <div style="background:linear-gradient(to right,#F43F5E,#F59E0B,#10D97E);
                            width:120px;height:7px;border-radius:4px;"></div>
                <span style="font-size:10px;color:#6B7280;">1.0 Walk Score</span>
            </div>""", unsafe_allow_html=True)

    # Panel resumen de zona seleccionada
    with mc2:
        if df_zona.empty:
            st.markdown("""
            <div class="panel" style="text-align:center;padding:24px 14px;">
                <div style="font-size:22px;margin-bottom:8px;color:#162032;">⬡</div>
                <div style="font-size:11px;color:#374151;line-height:1.7;">
                    Selecciona una zona<br/>en el panel izquierdo<br/>para ver su diagnóstico
                </div>
            </div>""", unsafe_allow_html=True)

            # Distribución RIM como referencia
            if "rim_clasificacion" in df_raw.columns:
                st.markdown('<div class="panel-title" '
                            'style="font-size:9px;color:#38BDF8;letter-spacing:.14em;'
                            'text-transform:uppercase;margin-top:4px;">'
                            'DISTRIBUCIÓN RIM</div>', unsafe_allow_html=True)
                counts = df_raw["rim_clasificacion"].value_counts()
                fig_donut = go.Figure(go.Pie(
                    labels=counts.index.tolist(),
                    values=counts.values.tolist(),
                    hole=0.62,
                    marker=dict(
                        colors=[f"rgb({RIM_COLORS.get(l, RIM_DEFAULT)[0]},"
                                f"{RIM_COLORS.get(l, RIM_DEFAULT)[1]},"
                                f"{RIM_COLORS.get(l, RIM_DEFAULT)[2]})"
                                for l in counts.index],
                        line=dict(color="#070B12", width=2),
                    ),
                    textinfo="none",
                    hovertemplate="%{label}<br>%{value} hex (%{percent})<extra></extra>",
                ))
                fig_donut.update_layout(
                    **PLOTLY_BASE,
                    height=220,
                    showlegend=False,
                    annotations=[dict(
                        text=f"<b>{n_hex_raw:,}</b><br><span style='font-size:9px'>"
                             f"hexágonos</span>",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=13, color="#C5CDD8"),
                    )],
                )
                st.plotly_chart(fig_donut, width="stretch",
                                config={"displayModeBar": False})
        else:
            # Panel de diagnóstico de zona
            ws_z   = df_zona["walk_score"].median()
            pop_z  = df_zona["population_count_1_2km"].mean()  # media por hex
            n_z    = len(df_zona)
            ws_cls = ws_to_class(ws_z)

            interv_top = "—"
            if "intervencion_1" in df_zona.columns:
                interv_top = df_zona["intervencion_1"].value_counts().index[0] \
                    if df_zona["intervencion_1"].notna().any() else "—"

            st.markdown(f"""
            <div class="panel">
                <div class="panel-title">◈ ZONA SELECCIONADA</div>
                <div class="{rim_badge_class(rim_zona)} zbadge">{rim_zona}</div>
                <hr style="border-color:#162032;margin:8px 0;"/>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div>
                        <div class="kpi-lbl">Walk Score mediano</div>
                        <div class="kpi-val {ws_cls}">{ws_z:.3f}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">Hexágonos</div>
                        <div class="kpi-val b">{n_z:,}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">Población impactada</div>
                        <div class="kpi-val b">{pop_z:,.0f}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">% del total</div>
                        <div class="kpi-val b">{n_z/n_hex_raw*100:.1f}%</div>
                    </div>
                </div>
                <hr style="border-color:#162032;margin:8px 0;"/>
                <div class="kpi-lbl">Intervención más frecuente</div>
                <div style="font-size:12px;color:#10D97E;font-weight:600;
                            margin-top:3px;">{interv_top}</div>
            </div>""", unsafe_allow_html=True)

            # Tiempos de caminata de la zona
            cols_t = {
                "Comida":    "walk_time_food",
                "Salud":     "walk_time_healthcare",
                "Educación": "walk_time_educational",
                "Ocio":      "walk_time_leisure",
            }
            tiempos = {k: df_zona[v].median() for k, v in cols_t.items()
                       if v in df_zona.columns}

            if tiempos:
                fig_t = go.Figure(go.Bar(
                    x=list(tiempos.values()), y=list(tiempos.keys()),
                    orientation="h",
                    marker=dict(color=[time_color(v) for v in tiempos.values()],
                                line=dict(width=0)),
                    text=[f"{v:.0f}'" for v in tiempos.values()],
                    textposition="outside",
                    textfont=dict(size=10, color="#8B98A8"),
                ))
                fig_t.add_vline(x=20, line=dict(color="rgba(245,158,11,0.2)",
                                                dash="dot", width=1))
                fig_t.update_layout(
                    **PLOTLY_BASE, height=165,
                    title=dict(text="⏱ Medianas de tiempo (min)",
                               font=dict(size=9, color="#38BDF8"), x=0),
                    showlegend=False,
                )
                fig_t.update_xaxes(
                    range=[0, max(max(tiempos.values()) * 1.25, 15)],
                    gridcolor="#162032", zerolinecolor="#162032")
                fig_t.update_yaxes(gridcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_t, width="stretch",
                                config={"displayModeBar": False})

            # Umbral mínimo para saltar de cluster
            st.markdown("""
            <div class="panel">
                <div class="panel-title">🎯 UMBRAL DE SALTO</div>
                <div style="font-size:10px;color:#6B7280;line-height:1.6;">
                    Para pasar a <b style="color:#38BDF8">Zona periurbana</b>,
                    esta zona necesita en promedio:
                </div>
            </div>""", unsafe_allow_html=True)

            umbrales = []
            if "dist_food_combined" in df_zona.columns:
                med_food = df_zona["dist_food_combined"].median()
                umbrales.append(("Dist. comida", f"{med_food:.0f}m → <800m",
                                 med_food > 800))
            if "intersection_density_ge3_1_2km" in df_zona.columns:
                med_int = df_zona["intersection_density_ge3_1_2km"].median()
                umbrales.append(("Intersecciones", f"{med_int:.0f} → >40/km²",
                                 med_int < 40))
            if "amenity_diversity_inegi" in df_zona.columns:
                med_div = df_zona["amenity_diversity_inegi"].median()
                umbrales.append(("Diversidad", f"{med_div:.2f} → >0.69",
                                 med_div < 0.69))

            for nombre, desc, necesita in umbrales:
                color = "#F43F5E" if necesita else "#10D97E"
                icon  = "✗" if necesita else "✓"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                            align-items:center;padding:4px 0;
                            border-bottom:1px solid #162032;">
                    <span style="font-size:10px;color:#8B98A8;">{nombre}</span>
                    <span style="font-size:10px;color:{color};">
                        {icon} {desc}</span>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SIMULADOR DE INTERVENCIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Qué columnas de tiempo afecta cada intervención
INTERV_A_TIEMPO = {
    "Mejorar conectividad vial":            ["walk_time_food", "walk_time_healthcare",
                                             "walk_time_educational", "walk_time_leisure"],
    "Reducir longitud de segmentos viales": ["walk_time_food", "walk_time_healthcare",
                                             "walk_time_educational", "walk_time_leisure"],
    "Reducir calles sin salida":            ["walk_time_food", "walk_time_healthcare",
                                             "walk_time_educational", "walk_time_leisure"],
    "Añadir servicio de alimentación":      ["walk_time_food"],
    "Incrementar oferta alimentaria":       ["walk_time_food"],
    "Añadir espacio de ocio/recreación":    ["walk_time_leisure"],
    "Incrementar oferta recreativa":        ["walk_time_leisure"],
    "Diversificar tipos de amenidades":     ["walk_time_food", "walk_time_leisure"],
}
TIEMPO_LABELS = {
    "walk_time_food":        "Comida",
    "walk_time_healthcare":  "Salud",
    "walk_time_educational": "Educación",
    "walk_time_leisure":     "Ocio",
}

with tab_sim:
    if not rim_zona or df_zona.empty:
        st.info("Selecciona una zona de intervención en el sidebar para activar el simulador.")
    else:
        sc1, sc2 = st.columns([1.8, 2.5])

        with sc1:
            # ── Diagnóstico de zona (igual que Tab 1) ───────────────────────
            ws_z   = df_zona["walk_score"].median()
            pop_z  = df_zona["population_count_1_2km"].mean()
            n_z    = len(df_zona)
            ws_cls = ws_to_class(ws_z)

            interv_sugerida = "—"
            if "intervencion_1" in df_zona.columns and df_zona["intervencion_1"].notna().any():
                interv_sugerida = df_zona["intervencion_1"].value_counts().index[0]

            # Construimos el HTML base
            html_diag = textwrap.dedent(f"""
            <div class="panel">
                <div class="panel-title">◈ DIAGNÓSTICO DE ZONA</div>
                <div class="{rim_badge_class(rim_zona)} zbadge">{rim_zona}</div>
                <hr style="border-color:#162032;margin:8px 0;"/>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div>
                        <div class="kpi-lbl">Walk Score mediano</div>
                        <div class="kpi-val {ws_cls}">{ws_z:.3f}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">Hexágonos</div>
                        <div class="kpi-val b">{n_z:,}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">Pob. media / hex</div>
                        <div class="kpi-val b">{pop_z:,.0f}</div>
                    </div>
                    <div>
                        <div class="kpi-lbl">% del total</div>
                        <div class="kpi-val b">{n_z/n_hex_raw*100:.1f}%</div>
                    </div>
                </div>
            """)

            # Agregamos la recomendación solo si existe
            if interv_sugerida != "—":
                html_diag += textwrap.dedent(f"""
                <hr style="border-color:#162032;margin:8px 0;"/>
                <div class="kpi-lbl">RIM v4 recomienda</div>
                <div style="font-size:11px;color:#10D97E;font-weight:600;margin-top:2px;">
                    {interv_sugerida}</div>
                """)

            # Cerramos el div principal y renderizamos
            html_diag += "\n</div>"
            st.markdown(html_diag, unsafe_allow_html=True)

            if "dist_food_combined" in df_zona.columns:
                med = df_zona["dist_food_combined"].median()
                umbrales.append(("Dist. comida", f"{med:.0f}m → <800m", med > 800))
            if "intersection_density_ge3_1_2km" in df_zona.columns:
                med = df_zona["intersection_density_ge3_1_2km"].median()
                umbrales.append(("Intersecciones", f"{med:.0f} → >40/km²", med < 40))
            if "amenity_diversity_inegi" in df_zona.columns:
                med = df_zona["amenity_diversity_inegi"].median()
                umbrales.append(("Diversidad", f"{med:.2f} → >0.69", med < 0.69))

            if umbrales:
                st.markdown(
                    '<div class="panel"><div class="panel-title">🎯 UMBRAL DE SALTO</div>',
                    unsafe_allow_html=True)
                for nombre, desc, necesita in umbrales:
                    color = "#F43F5E" if necesita else "#10D97E"
                    icon  = "✗" if necesita else "✓"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:4px 0;border-bottom:1px solid #162032;">
                        <span style="font-size:10px;color:#8B98A8;">{nombre}</span>
                        <span style="font-size:10px;color:{color};">{icon} {desc}</span>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Configuración ───────────────────────────────────────────────
            st.markdown(
                '<div class="panel"><div class="panel-title">⚡ CONFIGURAR INTERVENCIÓN</div>',
                unsafe_allow_html=True)

            interv_opciones = list(IMPACTOS_INTERVENCION.keys())
            idx_default = interv_opciones.index(interv_sugerida)                 if interv_sugerida in interv_opciones else 0

            interv_sel = st.selectbox(
                "Tipo de intervención", interv_opciones, index=idx_default,
                help="La intervención sugerida por RIM v4 está preseleccionada.",
            )
            cobertura = st.slider(
                "Cobertura", min_value=10, max_value=100, value=60, step=10,
                format="%d%%",
                help="% de hexágonos de la zona que recibirán la intervención.",
            )
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("▶ EJECUTAR SIMULACIÓN", use_container_width=False):
                impacto   = IMPACTOS_INTERVENCION.get(interv_sel, {})
                ws_delta  = impacto.get("walk_score_delta", 0.03) * (cobertura / 100)
                ict_delta = impacto.get("ict_delta", 0.2) * (cobertura / 100)
                ws_actual = df_zona["walk_score"].median()
                ws_nuevo  = min(ws_actual + ws_delta, 1.0)

                hex_impactados = int(n_z * cobertura / 100)
                pop_impact     = pop_z * hex_impactados

                # Candidatos a salto: viability_score >= 0.4
                n_viables = 0
                if "viability_score" in df_zona.columns:
                    n_viables = int(
                        df_zona["viability_score"].fillna(0).ge(0.4).sum()
                        * (cobertura / 100)
                    )

                # Tiempos: solo reducir categorías afectadas por la intervención
                cols_afectadas = INTERV_A_TIEMPO.get(interv_sel, [])
                t_antes, t_despues = {}, {}
                for col in ["walk_time_food", "walk_time_healthcare",
                            "walk_time_educational", "walk_time_leisure"]:
                    if col not in df_zona.columns:
                        continue
                    med = df_zona[col].median()
                    t_antes[col] = med
                    if col in cols_afectadas:
                        reduccion = min(med * ws_delta * 4, med * 0.40)
                        t_despues[col] = max(med - reduccion, 0)
                    else:
                        t_despues[col] = med  # sin cambio

                st.session_state["sim_result"] = {
                    "intervencion":   interv_sel,
                    "cobertura":      cobertura,
                    "ws_actual":      ws_actual,
                    "ws_nuevo":       ws_nuevo,
                    "ws_delta":       ws_delta,
                    "ict_delta":      ict_delta,
                    "pop_impact":     pop_impact,
                    "hex_impactados": hex_impactados,
                    "n_viables":      n_viables,
                    "zona":           rim_zona,
                    "t_antes":        t_antes,
                    "t_despues":      t_despues,
                    "cols_afectadas": cols_afectadas,
                }
                st.rerun()
        with sc2:
            res = st.session_state.get("sim_result")
            if res is None:
                st.markdown("""
                <div class="panel" style="text-align:center;padding:40px 20px;">
                    <div style="font-size:28px;color:#162032;margin-bottom:10px;">▶</div>
                    <div style="font-size:11px;color:#374151;line-height:1.7;">
                        Configura los parámetros<br/>y ejecuta la simulación
                    </div>
                </div>""", unsafe_allow_html=True)

            else:
                delta_pct = (res["ws_delta"] / res["ws_actual"] * 100) if res["ws_actual"] > 0 else 0

                # La clave es el "\" después de f""" y el .strip() al final
                html_card = textwrap.dedent(f"""\
                <div class="panel">
                    <div class="panel-title">📊 RESULTADO DE SIMULACIÓN</div>
                    <div style="font-size:10px;color:#6B7280;margin-bottom:10px;">
                        {res['intervencion']} · {res['cobertura']}% cobertura · {res['zona']}
                    </div>
                    <div class="sim-result">
                        <div style="font-size:9px;color:#10D97E;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2px;">
                            Mejora proyectada Walk Score
                        </div>
                        <div class="sim-delta">+{delta_pct:.1f}%</div>
                        <div style="font-size:11px;color:#6B7280;margin-top:2px;">
                            {res['ws_actual']:.3f} → {res['ws_nuevo']:.3f}
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px;">
                        <div>
                            <div class="kpi-lbl">Mejora ICT</div>
                            <div style="font-family:'Space Mono';font-size:16px;font-weight:700;color:#F59E0B;">+{res['ict_delta']:.1f}</div>
                            <div class="kpi-sub">categorías cubiertas</div>
                        </div>
                        <div>
                            <div class="kpi-lbl">Población impactada</div>
                            <div style="font-family:'Space Mono';font-size:16px;font-weight:700;color:#38BDF8;">{res['pop_impact']/1e3:.1f}K</div>
                            <div class="kpi-sub">{res['hex_impactados']} hex intervenidos</div>
                        </div>
                        <div>
                            <div class="kpi-lbl">Candidatos a salto</div>
                            <div style="font-family:'Space Mono';font-size:16px;font-weight:700;color:#10D97E;">~{res['n_viables']}</div>
                            <div class="kpi-sub">hex viability ≥ 0.4</div>
                        </div>
                    </div>
                </div>""").strip()

                st.markdown(html_card, unsafe_allow_html=True)
                # Debajo de esto continúan tus gráficos de Plotly...

                # Gráfico antes/después
                t_antes    = res.get("t_antes", {})
                t_despues  = res.get("t_despues", {})
                cols_afect = res.get("cols_afectadas", [])

                if t_antes:
                    labels      = [TIEMPO_LABELS.get(c, c) for c in t_antes]
                    y_antes     = list(t_antes.values())
                    y_desp      = list(t_despues.values())
                    colors_desp = [
                        "#10D97E" if c in cols_afect else "#2A3545"
                        for c in t_antes
                    ]

                    fig_ab = go.Figure()
                    fig_ab.add_trace(go.Bar(
                        name="Antes", x=labels, y=y_antes,
                        marker_color="#1E3A5F", width=0.35, offset=-0.2,
                    ))
                    fig_ab.add_trace(go.Bar(
                        name="Después", x=labels, y=y_desp,
                        marker=dict(color=colors_desp),
                        width=0.35, offset=0.2,
                    ))
                    fig_ab.update_layout(
                        **PLOTLY_BASE, height=230, barmode="overlay",
                        title=dict(
                            text="Tiempos de caminata: antes vs después (min)",
                            font=dict(size=9, color="#38BDF8"), x=0,
                        ),
                        legend=dict(x=0.75, y=0.95,
                                    bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
                    )
                    fig_ab.update_xaxes(gridcolor="#162032", zerolinecolor="#162032")
                    fig_ab.update_yaxes(gridcolor="#162032", zerolinecolor="#162032",
                                        title="minutos")
                    st.plotly_chart(fig_ab, width="stretch",
                                    config={"displayModeBar": False})

                    afect_labels = [TIEMPO_LABELS.get(c, c) for c in cols_afect
                                    if c in t_antes]
                    if afect_labels:
                        st.markdown(
                            f'<div style="font-size:9px;color:#374151;margin-top:2px;">'
                            f'Categorías reducidas: '
                            f'<span style="color:#10D97E;">'
                            f'{", ".join(afect_labels)}</span></div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("""
                <div style="background:#0A0F1A;border:1px solid #162032;
                            border-radius:5px;padding:8px 12px;margin-top:6px;">
                    <div style="font-size:9px;color:#374151;line-height:1.6;">
                        ⚠ Proyección basada en deltas del análisis de sensibilidad RIM v4.
                        Estimaciones de orden de magnitud, no predicciones exactas.
                    </div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANÁLISIS ESTRATÉGICO
# ══════════════════════════════════════════════════════════════════════════════
with tab_analisis:
    datos_ambas = cargar_ambas()
    C_COLORS = {"Atitalaquia": "#38BDF8", "Guanajuato": "#F59E0B"}

    if len(datos_ambas) < 2:
        st.warning("Se necesitan los dos archivos .gpkg para la comparativa.")
    else:
        ac1, ac2 = st.columns(2)

        with ac1:
            # Walk Score
            fig_ws = go.Figure()
            for nombre, dfc in datos_ambas.items():
                if "walk_score" not in dfc.columns: continue
                fig_ws.add_trace(go.Histogram(
                    x=dfc["walk_score"].dropna(), name=nombre,
                    nbinsx=40, marker_color=C_COLORS.get(nombre, "#888"),
                    opacity=0.75,
                ))
            fig_ws.update_layout(
                **PLOTLY_BASE, height=260, barmode="overlay",
                title=dict(text="Distribución Walk Score",
                           font=dict(size=11, color="#C5CDD8"), x=0),
                legend=dict(x=0.7, y=0.95, bgcolor="rgba(0,0,0,0)",
                            font=dict(size=10)),
            )
            fig_ws.update_xaxes(title="Walk Score", range=[0, 1],
                                gridcolor="#162032", zerolinecolor="#162032")
            fig_ws.update_yaxes(title="Hexágonos",
                                gridcolor="#162032", zerolinecolor="#162032")
            st.plotly_chart(fig_ws, width="stretch",
                            config={"displayModeBar": False})

        with ac2:
            # Info Gap
            fig_ig = go.Figure()
            for nombre, dfc in datos_ambas.items():
                if "info_gap" not in dfc.columns: continue
                p95 = dfc["info_gap"].quantile(0.95)
                fig_ig.add_trace(go.Histogram(
                    x=dfc["info_gap"].clip(upper=p95).dropna(), name=nombre,
                    nbinsx=40, marker_color=C_COLORS.get(nombre, "#888"),
                    opacity=0.75,
                ))
            fig_ig.update_layout(
                **PLOTLY_BASE, height=260, barmode="overlay",
                title=dict(text="Distribución Info Gap (P95)",
                           font=dict(size=11, color="#C5CDD8"), x=0),
                legend=dict(x=0.7, y=0.95, bgcolor="rgba(0,0,0,0)",
                            font=dict(size=10)),
            )
            fig_ig.update_xaxes(title="Info Gap (m)",
                                gridcolor="#162032", zerolinecolor="#162032")
            fig_ig.update_yaxes(title="Hexágonos",
                                gridcolor="#162032", zerolinecolor="#162032")
            st.plotly_chart(fig_ig, width="stretch",
                            config={"displayModeBar": False})

        # RIM comparativo
        st.markdown("##### Clasificación RIM v4 por ciudad")
        fig_rim = go.Figure()
        for nombre, dfc in datos_ambas.items():
            if "rim_clasificacion" not in dfc.columns: continue
            counts = dfc["rim_clasificacion"].value_counts(normalize=True) * 100
            fig_rim.add_trace(go.Bar(
                name=nombre, x=RIM_ORDER,
                y=[counts.get(r, 0) for r in RIM_ORDER],
                marker_color=C_COLORS.get(nombre, "#888"), opacity=0.85,
                text=[f"{counts.get(r, 0):.1f}%" for r in RIM_ORDER],
                textposition="outside", textfont=dict(size=9),
            ))
        fig_rim.update_layout(
            **PLOTLY_BASE, height=280, barmode="group",
            title=dict(text="Proporción de hexágonos por clasificación RIM",
                       font=dict(size=11, color="#C5CDD8"), x=0),
            legend=dict(x=0.82, y=0.95, bgcolor="rgba(0,0,0,0)"),
        )
        fig_rim.update_xaxes(tickangle=-18, tickfont=dict(size=9),
                             gridcolor="#162032", zerolinecolor="#162032")
        fig_rim.update_yaxes(title="% hexágonos", ticksuffix="%",
                             gridcolor="#162032", zerolinecolor="#162032")
        st.plotly_chart(fig_rim, width="stretch",
                        config={"displayModeBar": False})

        # Tabla KPIs
        st.markdown("##### KPIs comparativos")
        rows = []
        for nombre, dfc in datos_ambas.items():
            pct_excl = (dfc["rim_clasificacion"] == "Exclusión territorial").mean() * 100 \
                if "rim_clasificacion" in dfc.columns else np.nan
            pct_acc = (dfc["walk_time_nearest"] < 10).mean() * 100 \
                if "walk_time_nearest" in dfc.columns else np.nan
            n_viab = int((dfc["rim_clasificacion"] == "Transición viable").sum()) \
                if "rim_clasificacion" in dfc.columns else 0
            rows.append({
                "Ciudad":                   nombre,
                "Walk Score mediano":        f"{dfc['walk_score'].median():.3f}" if "walk_score" in dfc.columns else "—",
                "% Accesible <10 min":       f"{pct_acc:.1f}%" if not np.isnan(pct_acc) else "—",
                "% Exclusión territorial":   f"{pct_excl:.1f}%" if not np.isnan(pct_excl) else "—",
                "N Transición viable":       f"{n_viab:,}",
                "Total hexágonos":           f"{len(dfc):,}",
            })
        st.dataframe(
            pd.DataFrame(rows).set_index("Ciudad"),
            width="stretch",
        )
