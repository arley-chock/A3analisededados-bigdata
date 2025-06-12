# -*- coding: utf-8 -*-
"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este aplicativo foi desenvolvido como projeto acadêmico para:
- Arley do Nascimento Vinagre   (12722132338)
- Vinicius Santana              (1272221567)
- Tauan Santos Santana          (12722216126)

Objetivo:
Analisar planilhas Excel de portos sobre navios cancelados, gerando
gráficos interativos e métricas detalhadas.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Formatação de moeda BRL
def br_currency(x: float) -> str:
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Configuração do tema e layout
st.set_page_config(
    page_title="⚓ Dashboard Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para ajustar layout dos gráficos
def ajustar_layout_grafico(fig, altura=500):
    fig.update_layout(
        height=altura,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E0E0E0'),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    return fig

# CSS customizado
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg,#0a1f2f 0%,#02111e 100%);
    color: #E0E0E0;
}
.card {
    background: rgba(255,255,255,0.07);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.metric-card {
    background: rgba(255,255,255,0.05);
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
}
.js-plotly-plot {
    margin: 1rem 0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
}
.stTabs [data-baseweb="tab"] {
    height: 4rem;
    white-space: pre-wrap;
    background-color: rgba(255,255,255,0.05);
    border-radius: 4px 4px 0 0;
    gap: 1rem;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("""
<div class="card" style="text-align:center;">
    <h1>🚢 Dashboard de Cancelamentos de Navios</h1>
    <p><b>Projeto Acadêmico</b> – Arley do Nascimento Vinagre, Vinicius Santana, Tauan Santos Santana</p>
    <em>Objetivo: analisar planilhas Excel de portos sobre navios cancelados, com gráficos e métricas interativas.</em>
</div>
""", unsafe_allow_html=True)

# Sidebar: Upload & referências de custo
with st.sidebar:
    st.header("📂 Upload & Custos")
    
    # Opção para usar arquivo padrão ou upload
    use_default = st.checkbox("Usar arquivo padrão", value=True)
    
    if use_default:
        default_file = "ProgramacaoDeNavios (1) (1).xlsx"
        if os.path.exists(default_file):
            uploaded_file = open(default_file, 'rb')
        else:
            st.error("Arquivo padrão não encontrado!")
            uploaded_file = None
    else:
        uploaded_file = st.file_uploader("Carregue um arquivo Excel (.xlsx)", type="xlsx")
    
    st.markdown("---")
    st.markdown("### 💰 Custos de Referência (2024-25)")
    
    # Custos editáveis
    thc = st.number_input("THC (R$/TEU)", value=1200.0, step=100.0)
    oper = st.number_input("Operação Terminal (R$/cancel.)", value=1150.0, step=100.0)
    doc = st.number_input("Despachante (R$)", value=950.0, step=50.0)
    arm_day = st.number_input("Armazenagem (R$/TEU/dia)", value=575.0, step=25.0)
    arm_days = st.number_input("Dias de Armazenagem", value=2, min_value=1, max_value=30)
    insp = st.number_input("Inspeção (R$/contêiner)", value=95.0, step=5.0)

if not uploaded_file:
    st.warning("Por favor, carregue um arquivo Excel ou selecione o arquivo padrão para iniciar a análise.")
    st.stop()

# Leitura e pré-processamento
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()

# Mapeamento de colunas essenciais
col_navio       = 'Navio / Viagem1'         if 'Navio / Viagem1'         in df.columns else None
col_status      = 'Situação'               if 'Situação'               in df.columns else None
col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_etd         = 'Estimativa Saída ETD'   if 'Estimativa Saída ETD'   in df.columns else None
col_rota        = 'De / Para'              if 'De / Para'              in df.columns else None
col_servico     = 'Serviço'                if 'Serviço'                in df.columns else None
col_armador     = 'Armador'                if 'Armador'                in df.columns else None
col_conteineres = 'Movs'                   if 'Movs'                   in df.columns else None

if not col_navio or not col_status:
    st.error("As colunas obrigatórias 'Navio / Viagem1' e 'Situação' não foram encontradas.")
    st.stop()

# Filtrar apenas cancelamentos
df[col_status] = df[col_status].astype(str).str.strip().str.lower()
mask_cancel = df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])
df_canc = df.loc[mask_cancel].copy()

# Converter datas e extrair período mês-ano
if col_data:
    df_canc[col_data] = pd.to_datetime(df_canc[col_data], dayfirst=True, errors='coerce')
    df_canc.dropna(subset=[col_data], inplace=True)
    df_canc['Y-M'] = df_canc[col_data].dt.to_period('M').astype(str)

# Converter TEUs para numérico
if col_conteineres:
    df_canc[col_conteineres] = pd.to_numeric(df_canc[col_conteineres], errors='coerce').fillna(0)

# Calcular custos por cancelamento
C = {
    "THC": thc,
    "OPER": oper,
    "DOC": doc,
    "ARM_DAY": arm_day,
    "ARM_DAYS": arm_days,
    "INSP": insp
}

if col_conteineres:
    df_canc["C_TEUS"]      = df_canc[col_conteineres] * C["THC"]
    df_canc["C_OPER"]      = C["OPER"]
    df_canc["C_DOC"]       = C["DOC"]
    df_canc["C_ARM"]       = df_canc[col_conteineres] * C["ARM_DAY"] * C["ARM_DAYS"]
    df_canc["C_INSP"]      = C["INSP"]
    df_canc["CUSTO_TOTAL"] = df_canc[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)

# Criação das abas
tabs = st.tabs([
    "📈 Visão Geral",
    "🚢 Navios",
    "📅 Temporal",
    "🌍 Rotas",
    "🔄 Serviços",
    "📊 Dist & Correl",
    "💰 Custos"
])

# Aba 1: Visão Geral
with tabs[0]:
    st.subheader("Visão Geral dos Cancelamentos")
    
    # Métricas principais
    total = len(df)
    canc  = len(df_canc)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de Registros", f"{total:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Cancelado", f"{canc:,}", f"{canc/total*100:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if col_conteineres:
            st.metric("TEUs Afetados", f"{int(df_canc[col_conteineres].sum()):,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if col_data and not df_canc.empty:
            periodo = f"{df_canc[col_data].min().strftime('%b %Y')} → {df_canc[col_data].max().strftime('%b %Y')}"
            st.metric("Período", periodo)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Gráfico de pizza
    fig = px.pie(
        names=["Cancelados","Não Cancelados"],
        values=[canc, total-canc],
        color_discrete_sequence=px.colors.qualitative.Set3,
        title="Distribuição de Cancelamentos"
    )
    st.plotly_chart(ajustar_layout_grafico(fig, 300), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 2: Navios
with tabs[1]:
    st.subheader(" Navios Cancelados")
    cnt_nav = df_canc[col_navio].value_counts().head(10).reset_index()
    cnt_nav.columns = ["Navio","Cancelamentos"]
    fig = px.bar(
        cnt_nav,
        x="Cancelamentos", y="Navio",
        orientation="h",
        color="Cancelamentos", color_continuous_scale="Viridis"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
    st.dataframe(cnt_nav, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 3: Temporal
with tabs[2]:
    st.subheader("Evolução Mensal de Cancelamentos")
    if col_data:
        cnt_m = df_canc.groupby("Y-M").size().reset_index(name="Cancelamentos")
        cnt_m["Y-M"] = pd.to_datetime(cnt_m["Y-M"], format="%Y-%m")
        fig = px.line(cnt_m, x="Y-M", y="Cancelamentos", markers=True)
        fig.update_layout(xaxis_title="Mês", yaxis_title="Cancelamentos")
        st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
        st.dataframe(cnt_m.rename(columns={"Y-M":"Mês"}), use_container_width=True)
    else:
        st.info("Coluna de data não encontrada.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 4: Rotas
with tabs[3]:
    st.subheader("Top 10 Rotas Canceladas")
    if col_rota:
        cnt_r = df_canc[col_rota].value_counts().head(10).reset_index()
        cnt_r.columns = ["Rota","Cancelamentos"]
        fig = px.bar(
            cnt_r,
            x="Cancelamentos", y="Rota",
            orientation="h",
            color="Cancelamentos", color_continuous_scale="Inferno"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
        st.dataframe(cnt_r, use_container_width=True)
    else:
        st.info("Coluna de rota não encontrada.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 5: Serviços
with tabs[4]:
    st.subheader("Top 10 Serviços Cancelados")
    if col_servico:
        cnt_s = df_canc[col_servico].value_counts().head(10).reset_index()
        cnt_s.columns = ["Serviço","Cancelamentos"]
        top = cnt_s.iloc[0]
        st.metric("Serviço Mais Cancelado", top["Serviço"], f"{top['Cancelamentos']} vezes")
        fig = px.pie(cnt_s, names="Serviço", values="Cancelamentos", color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(ajustar_layout_grafico(fig, 350), use_container_width=True)
        st.dataframe(cnt_s, use_container_width=True)
    else:
        st.info("Coluna de serviço não encontrada.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 6: Distribuições & Correlações
with tabs[5]:
    st.subheader("Distribuições e Correlações")
    if col_conteineres:
        st.markdown("**Distribuição de TEUs**")
        fig = px.histogram(df_canc, x=col_conteineres, nbins=20, title="Histograma de TEUs")
        st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
    nums = df_canc.select_dtypes(include="number")
    if nums.shape[1] > 1:
        st.markdown("**Matriz de Correlação**")
        corr = nums.corr()
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu", aspect="auto")
        st.plotly_chart(ajustar_layout_grafico(fig, 400), use_container_width=True)
        st.dataframe(corr, use_container_width=True)
    else:
        st.info("Não há colunas numéricas suficientes para correlação.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 7: Custos
with tabs[6]:
    st.subheader("Análise de Custos")
    if "CUSTO_TOTAL" in df_canc:
        total_cost = df_canc["CUSTO_TOTAL"].sum()
        avg_cost   = df_canc["CUSTO_TOTAL"].mean()
        colA, colB, colC = st.columns(3)
        colA.metric("Custo Total", br_currency(total_cost))
        colB.metric("Custo Médio", br_currency(avg_cost))
        if col_conteineres:
            colC.metric("TEUs Afetados", f"{int(df_canc[col_conteineres].sum()):,}")
        fig = px.box(df_canc, y="CUSTO_TOTAL", points="outliers", title="Distribuição de Custos")
        st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
        if col_armador:
            st.subheader("Top 10 Armadores por Prejuízo")
            df_canc[col_armador] = df_canc[col_armador].fillna("Não Informado")
            cost_arm = (
                df_canc.groupby(col_armador)["CUSTO_TOTAL"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            cost_arm.columns = ["Armador","Prejuízo"]
            cost_arm["Prejuízo BRL"] = cost_arm["Prejuízo"].apply(br_currency)
            st.dataframe(cost_arm[["Armador","Prejuízo BRL"]], use_container_width=True)
            # Gráfico
            cost_chart = cost_arm.copy()
            cost_chart["Prejuízo"] = cost_chart["Prejuízo"]
            fig2 = px.bar(
                cost_chart,
                x="Armador", y="Prejuízo",
                color="Prejuízo", color_continuous_scale="Viridis",
                title="Prejuízo por Armador"
            )
            st.plotly_chart(ajustar_layout_grafico(fig2), use_container_width=True)
    else:
        st.info("Não há dados de custos (coluna de TEUs ausente).")
