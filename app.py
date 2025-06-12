# -*- coding: utf-8 -*-
"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este aplicativo foi desenvolvido como projeto acadêmico para:
- Arley do Nascimento Vinagre   (12722132338)
- Vinicius Santana              (1272221567)
- Tauan Santos Santana          (12722216126)

Objetivo:
Analisar planilhas Excel de portos sobre navios cancelados, identificando
padrões temporais, navios mais afetados, rotas, serviços cancelados e custos,
incluindo armadores que geraram maior prejuízo.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Função para aplicar estilo Plotly
def ajustar_layout_grafico(fig, altura=500):
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# Configuração da página
st.set_page_config(
    page_title="⚓ Dashboard Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# Cabeçalho
st.markdown("""
<div style="background:rgba(255,255,255,0.05); padding:1rem; border-radius:8px; text-align:center;">
  <h1>🚢 Análise de Cancelamentos de Navios</h1>
  <p><b>Projeto Acadêmico</b> – Arley, Vinicius, Tauan</p>
  <em>Objetivo: gráficos interativos e análises detalhadas de cancelamentos portuários.</em>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar: upload e filtros
with st.sidebar:
    st.header("📂 Upload & Filtros")
    uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type="xlsx")
    st.markdown("---")

if not uploaded_file:
    st.warning("Por favor, faça o upload de um arquivo Excel para prosseguir.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Leitura dos dados
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()  # remover espaços extras

# Mapeamento de colunas
col_navio       = 'Navio / Viagem'         if 'Navio / Viagem'         in df.columns else None
col_status      = 'Situação'               if 'Situação'               in df.columns else None
col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_etd         = 'Estimativa Saída ETD'   if 'Estimativa Saída ETD'   in df.columns else None
col_rota        = 'De / Para'              if 'De / Para'              in df.columns else None
col_servico     = 'Serviço'                if 'Serviço'                in df.columns else None
col_armador     = 'Armador'                if 'Armador'                in df.columns else None
col_conteineres = 'Movs'                   if 'Movs'                   in df.columns else None

# Filtrar cancelamentos
df[col_status] = df[col_status].astype(str).str.strip().str.lower()
mask_cancel = df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])
df_canc     = df.loc[mask_cancel].copy()

# Converter datas e extrair período
if col_data:
    df_canc[col_data] = pd.to_datetime(df_canc[col_data], dayfirst=True, errors='coerce')
    df_canc.dropna(subset=[col_data], inplace=True)
    df_canc['Ano'] = df_canc[col_data].dt.year
    df_canc['Mês'] = df_canc[col_data].dt.month
    df_canc['Y-M'] = df_canc[col_data].dt.to_period('M').astype(str)

# Converter contêineres para numérico
if col_conteineres:
    df_canc[col_conteineres] = pd.to_numeric(df_canc[col_conteineres], errors='coerce').fillna(0)

# ──────────────────────────────────────────────────────────────────────────────
# Cálculo de custos
CUSTOS = {
    "THC":      1200.0,
    "OPER":     1150.0,
    "DOC":       950.0,
    "ARM_DAY":   575.0,
    "ARM_DAYS":    2,
    "INSP":       95.0
}
if col_conteineres:
    df_canc["C_TEUS"]      = df_canc[col_conteineres] * CUSTOS["THC"]
    df_canc["C_OPER"]      = CUSTOS["OPER"]
    df_canc["C_DOC"]       = CUSTOS["DOC"]
    df_canc["C_ARM"]       = df_canc[col_conteineres] * CUSTOS["ARM_DAY"] * CUSTOS["ARM_DAYS"]
    df_canc["C_INSP"]      = CUSTOS["INSP"]
    df_canc["CUSTO_TOTAL"] = df_canc[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)

# ──────────────────────────────────────────────────────────────────────────────
# Abas de navegação
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Visão Geral",
    "🚢 Navios",
    "📅 Temporal",
    "🌍 Rotas",
    "🔄 Serviços",
    "📊 Dist/Correl",
    "💰 Custos"
])

# ──────────────────────────────────────────────────────────────────────────────
# Aba 1: Visão Geral
with tab1:
    st.subheader("Distribuição de Cancelamentos")
    total = len(df)
    canc  = len(df_canc)
    st.metric("Total de Registros", f"{total:,}")
    st.metric("Total Cancelado",     f"{canc:,}", f"{canc/total*100:.1f}%")
    fig = px.pie(
        names=["Cancelados","Não Cancelados"],
        values=[canc, total-canc],
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    st.plotly_chart(ajustar_layout_grafico(fig, 350), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 2: Navios
with tab2:
    st.subheader("Top Navios Cancelados")
    cnt_nav = df_canc[col_navio].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(8,4))
    sns.barplot(x=cnt_nav.values, y=cnt_nav.index, palette="viridis", ax=ax)
    ax.set_xlabel("Cancelamentos")
    ax.set_ylabel("Navio")
    ax.set_title("Top 10 Navios")
    st.pyplot(fig)
    st.dataframe(cnt_nav.rename_axis("Navio").reset_index(name="Cancelamentos"), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 3: Temporal
with tab3:
    st.subheader("Cancelamentos por Mês")
    cnt_m = df_canc.groupby("Y-M").size().reset_index(name="Cancelamentos")
    cnt_m["Y-M"] = pd.to_datetime(cnt_m["Y-M"], format="%Y-%m")
    fig = px.line(cnt_m, x="Y-M", y="Cancelamentos", markers=True)
    fig.update_layout(xaxis_title="Mês", yaxis_title="Qtd Cancelamentos")
    st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
    st.dataframe(cnt_m.rename(columns={"Y-M":"Mês"}), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 4: Rotas
with tab4:
    st.subheader("Rotas mais Canceladas")
    if col_rota:
        cnt_r = df_canc[col_rota].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(8,4))
        sns.barplot(x=cnt_r.values, y=cnt_r.index, palette="magma", ax=ax)
        ax.set_xlabel("Cancelamentos")
        ax.set_ylabel("Rota")
        ax.set_title("Top 10 Rotas")
        st.pyplot(fig)
        st.dataframe(cnt_r.rename_axis("Rota").reset_index(name="Cancelamentos"), use_container_width=True)
    else:
        st.info("Coluna de rotas não encontrada.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 5: Serviços
with tab5:
    st.subheader("Serviços Cancelados")
    if col_servico:
        cnt_s = df_canc[col_servico].value_counts().reset_index()
        cnt_s.columns = ["Serviço","Cancelamentos"]
        top = cnt_s.iloc[0]
        st.metric("Serviço Top 1", top["Serviço"], f"{int(top['Cancelamentos'])} vezes")
        fig = px.pie(cnt_s.head(10), names="Serviço", values="Cancelamentos",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(ajustar_layout_grafico(fig,350), use_container_width=True)
        st.dataframe(cnt_s.head(10), use_container_width=True)
    else:
        st.info("Coluna de serviço não encontrada.")

# ──────────────────────────────────────────────────────────────────────────────
# Aba 6: Distribuições e Correlações
with tab6:
    st.subheader("Distribuição de TEUs")
    if col_conteineres:
        desc = df_canc[col_conteineres].describe().round(1)
        st.write(desc.to_frame("Estatísticas"))
        fig, ax = plt.subplots(figsize=(8,4))
        sns.histplot(df_canc[col_conteineres], bins=20, kde=True, color="seagreen", ax=ax)
        ax.set_xlabel("TEUs")
        ax.set_title("Histograma de TEUs em Cancelamentos")
        st.pyplot(fig)
    st.subheader("Matriz de Correlação")
    nums = df_canc.select_dtypes(include="number")
    if nums.shape[1] > 1:
        fig, ax = plt.subplots(figsize=(6,5))
        sns.heatmap(nums.corr(), annot=True, fmt=".2f", cmap="vlag", ax=ax)
        st.pyplot(fig)
        st.dataframe(nums.corr(), use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Aba 7: Custos
with tab7:
    st.subheader("Custos de Cancelamento")
    if "CUSTO_TOTAL" in df_canc:
        total_cost = df_canc["CUSTO_TOTAL"].sum()
        avg_cost   = df_canc["CUSTO_TOTAL"].mean()
        st.metric("Custo Total", f"R$ {total_cost:,.2f}")
        st.metric("Custo Médio", f"R$ {avg_cost:,.2f}")
        # Boxplot
        fig = px.box(df_canc, y="CUSTO_TOTAL", points="all",
                     title="Distribuição do Custo por Cancelamento")
        st.plotly_chart(ajustar_layout_grafico(fig), use_container_width=True)
        # Armadores por Prejuízo
        if col_armador:
            st.markdown("**Armadores com Maior Prejuízo**")
            df_canc[col_armador] = df_canc[col_armador].fillna("Não Informado")
            cost_a = df_canc.groupby(col_armador)["CUSTO_TOTAL"].sum().sort_values(ascending=False).head(10)
            fig, ax = plt.subplots(figsize=(8,4))
            sns.barplot(x=cost_a.values, y=cost_a.index, palette="rocket", ax=ax)
            ax.set_xlabel("Prejuízo (R$)")
            ax.set_ylabel("Armador")
            ax.set_title("Top 10 Armadores por Prejuízo")
            st.pyplot(fig)
            st.dataframe(cost_a.rename_axis("Armador").reset_index(name="Prejuízo (R$)"), use_container_width=True)
    else:
        st.info("Não há dados de custos disponíveis (coluna de TEUs ausente).")
