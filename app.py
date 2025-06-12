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

# ─── Leitura de todas as abas e concat ─────────────────────────────────────────
try:
    xls = pd.read_excel(uploaded, sheet_name=None)
    df = pd.concat(xls.values(), ignore_index=True)
except:
    df = pd.read_excel(uploaded)

# ─── Detecção flexível de colunas ─────────────────────────────────────────────
cols = {c.lower(): c for c in df.columns}
def achar(*candidatos):
    for c in candidatos:
        key = c.lower()
        if key in cols:
            return cols[key]
    return None

col_status    = achar('Situação','Status')
col_navio_raw = achar('Navio / Viagem','Navio')
col_navio_lim = achar('Navio / Viagem.1','Navio Limpo')
col_eta       = achar('Estimativa Chegada ETA','ETA')
col_etd       = achar('Estimativa Saída ETD','ETD')
col_movs      = achar('Movs','Contêineres','TEUs')
col_armador   = achar('Armador')
col_rota      = achar('De / Para','Rota')
col_tipo      = achar('Tipo','Tipo de Navio')

# ─── Filtrar apenas cancelados ─────────────────────────────────────────────────
if col_status:
    df[col_status] = df[col_status].astype(str).str.strip().str.lower()
    df_cancel = df[df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])].copy()
else:
    df_cancel = df.copy()

# ─── Conversões numéricas e datas ──────────────────────────────────────────────
if col_movs:
    df_cancel[col_movs] = pd.to_numeric(df_cancel[col_movs], errors='coerce').fillna(0)
if col_eta:
    df_cancel[col_eta] = pd.to_datetime(df_cancel[col_eta], errors='coerce', dayfirst=True)
if col_etd:
    df_cancel[col_etd] = pd.to_datetime(df_cancel[col_etd], errors='coerce', dayfirst=True)

# ─── Campos derivados ─────────────────────────────────────────────────────────
df_cancel['Navio'] = (df_cancel[col_navio_lim or col_navio_raw]
                      .astype(str).str.title().str.strip())

# Tempo de permanência (h)
if col_eta and col_etd:
    df_cancel['Tempo_Permanencia'] = (
      df_cancel[col_etd] - df_cancel[col_eta]
    ).dt.total_seconds().div(3600).clip(lower=0)

# Mês e dia da semana
if col_eta:
    df_cancel['Mes'] = df_cancel[col_eta].dt.to_period('M').astype(str)
    df_cancel['Dia_Semana'] = df_cancel[col_eta].dt.day_name()

# ─── Cálculo de custos ─────────────────────────────────────────────────────────
C = {"TEU":1200,"OPER":1150,"DOC":950,"ARM_DIA":575,"ARM_DIAS":2,"INSP":95}
if col_movs:
    df_cancel['C_TEUS'] = df_cancel[col_movs]*C['TEU']
    df_cancel['C_OPER'] = C['OPER']
    df_cancel['C_DOC']  = C['DOC']
    df_cancel['C_ARM']  = df_cancel[col_movs]*C['ARM_DIA']*C['ARM_DIAS']
    df_cancel['C_INSP']= C['INSP']
    df_cancel['CUSTO_TOTAL'] = df_cancel[[
        'C_TEUS','C_OPER','C_DOC','C_ARM','C_INSP'
    ]].sum(axis=1)

# ─── Funções de plot ──────────────────────────────────────────────────────────
def plot_heatmap(df):
    num = df.select_dtypes(float).columns
    if len(num)>1:
        fig,ax = plt.subplots(figsize=(8,6))
        sns.heatmap(df[num].corr(),annot=True,fmt=".2f",cmap='coolwarm',ax=ax)
        st.pyplot(fig)

def plot_hist(df):
    if col_movs:
        fig,ax=plt.subplots(figsize=(6,4))
        sns.histplot(df[col_movs],bins=20,ax=ax,kde=False)
        ax.set_title("Distribuição de TEUs Cancelados")
        st.pyplot(fig)

# ─── Abas ─────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📈 Geral","🚢 Navios","📅 Temporal",
    "🌍 Rotas","📊 Correlações","💰 Custos"
])

# — Geral
with tabs[0]:
    st.header("📈 Visão Geral")
    c1,c2,c3 = st.columns(3,gap="large")
    c1.metric("Registros totais",f"{len(df):,}",delta=f"{len(df_cancel):,}")
    pct = (len(df_cancel)/len(df)*100) if len(df)>0 else 0
    c2.metric("Taxa de cancelamento",f"{pct:.1f}%",delta=f"{pct:.1f}%")
    avg = (len(df_cancel)/30) if len(df_cancel)>0 else 0
    c3.metric("Média diária",f"{avg:.1f}",delta="cancel./dia")
    pie = px.pie(
        names=["Cancelados","Não cancelados"],
        values=[len(df_cancel),len(df)-len(df_cancel)],
        title=""
    )
    st.plotly_chart(pie,use_container_width=True)

# — Navios
with tabs[1]:
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
