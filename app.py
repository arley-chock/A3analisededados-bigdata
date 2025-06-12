import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚓ Dashboard Marítimo de Cancelamentos",
    page_icon="🚢",
    layout="wide"
)

# ─── CSS tema marítimo ─────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0a1f2f 0%, #02111e 100%);
    color: #E0E0E0;
}
.dashboard-card {
    background: rgba(255,255,255,0.05);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    border: 1px solid #0f3851;
}
h1, h2, h3, h4 { text-align: center; }
.js-plotly-plot { margin-bottom: 3rem !important; }
section.main > div.block-container { padding: 2rem 1rem; }
[data-testid="stColumns"] > div { margin-bottom: 2rem; }
.stTextInput, .stFileUploader, .stSelectbox, .stButton { margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-card">
  <h1>⚓ Análise de Cancelamentos de Navios</h1>
  <p>Dashboard Marítimo Interativo</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload & Filtros")
    uploaded = st.file_uploader("Faça upload do Excel (.xlsx)", type="xlsx")
    termo = st.text_input("🔍 Buscar navio / armador / rota")
    st.markdown("---")
    st.markdown("### ⚓ Custos de Referência")
    st.write("""
      - THC (R$/TEU): 1.200  
      - Armazenagem (R$/TEU/dia): 575  
      - Despachante (R$): 950  
      - Scanner (R$/contêiner): 95  
      - Câmbio: R$5,10 / US$1
    """)
if not uploaded:
    st.stop()
df = pd.read_excel(xls)

# ——— Detectar colunas ———

col_status      = 'Situação' if 'Situação' in df.columns else None
col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_conteineres = 'Movs' if 'Movs' in df.columns else None
col_armador     = 'Armador' if 'Armador' in df.columns else None
col_rota        = 'De / Para' if 'De / Para' in df.columns else None
col_tipo_navio  = 'Tipo' if 'Tipo' in df.columns else None
col_navio_raw   = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None

# ——— Filtrar cancelados ———

if col_status:
    df[col_status] = df[col_status].astype(str).str.strip().str.lower()
    df_cancel = df[df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])].copy()
else:
    df_cancel = df.copy()

# ——— Converter tipos ———

if col_conteineres:
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce', dayfirst=True)

# ——— Extrair nome de navio ———

NAV_COL = 'Navio / Viagem.1' if 'Navio / Viagem.1' in df_cancel.columns else col_navio_raw
df_cancel['Navio'] = df_cancel[NAV_COL].astype(str).str.strip().str.title()
cnt_navios = df_cancel['Navio'].value_counts().reset_index()
cnt_navios.columns = ['Navio','Cancelamentos']

# ——— Série temporal mensal ———

if col_data:
    tmp = df_cancel.dropna(subset=[col_data]).copy()
    tmp['Mes'] = tmp[col_data].dt.to_period('M').astype(str)
    cnt_mensal = tmp.groupby('Mes').size().reset_index(name='Cancelamentos')
    cnt_mensal['Mes'] = pd.to_datetime(cnt_mensal['Mes'],format='%Y-%m')
    cnt_mensal = cnt_mensal.sort_values('Mes')
else:
    cnt_mensal = pd.DataFrame(columns=['Mes','Cancelamentos'])

# ——— Resumo na sidebar ———

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Resumo Rápido")
    st.write(f"- Total de cancelamentos: **{len(df_cancel):,}**")
    if not cnt_navios.empty:
        top = cnt_navios.iloc[0]
        st.write(f"- Navio mais cancelado: **{top['Navio']}** ({top['Cancelamentos']}x)")
    if not cnt_mensal.empty:
        pico = cnt_mensal.loc[cnt_mensal['Cancelamentos'].idxmax()]
        st.write(f"- Mês de pico: **{pico['Mes'].strftime('%Y-%m')}** ({int(pico['Cancelamentos'])} cancel.)")

# ——— Abas principais ———

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "📈 Geral","🚢 Navios","📅 Temporal","🌍 Rotas","📊 Adicionais","💰 Custos"
])

# ——— Aba 1: Visão Geral ———

# Aba 1: Visão Geral
with tab1:
    st.header("📈 Visão Geral")
    c1,c2,c3 = st.columns(3,gap="large")
    c1.metric("Registros totais",f"{len(df):,}",delta=f"{len(df_cancel):,} cancel.")
    pct = (len(df_cancel)/len(df)*100) if len(df)>0 else 0
    c2.metric("Taxa de cancelamento",f"{pct:.1f}%",delta=f"{pct:.1f}%")
    avg = (len(df_cancel)/30) if len(df_cancel)>0 else 0
    c3.metric("Média diária",f"{avg:.1f}",delta="cancel./dia")

    # Cancelados vs Não
    pie = px.pie(
        names=["Cancelados","Não cancelados"],
        values=[len(df_cancel),len(df)-len(df_cancel)],
        title="Distribuição de Cancelamentos",
        color_discrete_sequence=px.colors.sequential.Blues
    )
    st.plotly_chart(ajustar_layout_grafico(pie,altura=400),use_container_width=True)

# Aba 2: Top Navios
with tab2:
    st.header("🚢 Top 10 Navios")
    cnt = df_cancel['Navio'].value_counts().head(10).reset_index()
    cnt.columns=['Navio','Qtde']
    bar = px.bar(cnt,y='Navio',x='Qtde',orientation='h',
                 color='Qtde',color_continuous_scale='Blues',title="")
    st.plotly_chart(bar,use_container_width=True)
    st.dataframe(cnt,use_container_width=True)

# — Temporal
with tabs[2]:
    st.header("📅 Evolução Mensal")
    if 'Mes' in df_cancel:
        ts = df_cancel.groupby('Mes').size().reset_index(name='Qtde')
        ts['Mes'] = pd.to_datetime(ts['Mes'])
        line = px.line(ts,x='Mes',y='Qtde',markers=True,title="")
        st.plotly_chart(line,use_container_width=True)
    st.subheader("⌛ Tempo de Permanência")
    plot_hist(df_cancel)

# — Rotas
with tabs[3]:
    st.header("🌍 Rotas")
    if col_rota:
        rt = df_cancel[col_rota].value_counts().head(10).reset_index()
        rt.columns=['Rota','Qtde']
        st.dataframe(rt,use_container_width=True)
        br = px.bar(rt,x='Rota',y='Qtde',color='Qtde',color_continuous_scale='Blues',title="")
        st.plotly_chart(br,use_container_width=True)
    else:
        st.warning("Coluna de rotas não encontrada.")

# — Correlações
with tabs[4]:
    st.header("📊 Matriz de Correlação")
    plot_heatmap(df_cancel)

# — Custos
with tabs[5]:
    st.header("💰 Análise de Custos")
    if 'CUSTO_TOTAL' in df_cancel:
        total = df_cancel['CUSTO_TOTAL'].sum()
        media = df_cancel['CUSTO_TOTAL'].mean()
        st.metric("Total perdido",
                  f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
        st.metric("Média / cancel.",
                  f"R$ {media:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))

        box = px.box(df_cancel,y='CUSTO_TOTAL',title="")
        st.plotly_chart(box,use_container_width=True)

        comps = df_cancel[['C_TEUS','C_OPER','C_DOC','C_ARM','C_INSP']].sum().reset_index()
        comps.columns=['Componente','Valor']
        comps['Valor_R$'] = comps['Valor'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )
        st.subheader("Componentes de Custo")
        st.dataframe(comps[['Componente','Valor_R$']],use_container_width=True)

        pie2 = px.pie(comps,names='Componente',values='Valor',title="")
        st.plotly_chart(pie2,use_container_width=True)
    else:
        st.warning("Não foi possível calcular custos sem coluna 'Movs'.")
