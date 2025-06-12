# -*- coding: utf-8 -*-
"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este aplicativo foi desenvolvido como projeto acadêmico para:
- Arley do Nascimento Vinagre   (12722132338)
- Vinicius Santana              (1272221567)
- Tauan Santos Santana          (12722216126)

Objetivo:
Analisar, de forma interativa, os levantamentos em formato Excel dos portos
sobre navios cancelados, identificando padrões temporais, os navios mais
afetados, rotas, custos e outros insights operacionais.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Funções utilitárias
# ──────────────────────────────────────────────────────────────────────────────
def ajustar_layout_grafico(fig, altura=500):
    """Aplica estilo, transparência e margens a um gráfico Plotly."""
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

# Referências de custo (2024-25)
CUSTOS = {
    "THC": 1200.0,    # R$ / TEU
    "OPER": 1150.0,   # R$ fixo por cancelamento terminal
    "DOC": 950.0,     # R$ despachante
    "ARM_DAY": 575.0, # R$ / TEU / dia
    "ARM_DAYS": 2,    # dias extras
    "INSP": 95.0      # R$ / contêiner (scanner/fitossanitária)
}

def calcular_custos(df, col_teu):
    """Adiciona colunas de custo ao df de cancelamentos."""
    df = df.copy()
    df[col_teu] = pd.to_numeric(df[col_teu], errors='coerce').fillna(0)
    df["C_TEUS"]    = df[col_teu] * CUSTOS["THC"]
    df["C_OPER"]    = CUSTOS["OPER"]
    df["C_DOC"]     = CUSTOS["DOC"]
    df["C_ARM"]     = df[col_teu] * CUSTOS["ARM_DAY"] * CUSTOS["ARM_DAYS"]
    df["C_INSP"]    = CUSTOS["INSP"]
    df["CUSTO_TOTAL"] = df[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
    return df

# ──────────────────────────────────────────────────────────────────────────────
# Configuração da página e CSS
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚓ Dashboard Marítimo de Cancelamentos",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg,#0a1f2f 0%,#02111e 100%);
  color: #E0E0E0;
}
.dashboard-card {
  background: rgba(255,255,255,0.05);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  border: 1px solid #0f3851;
}
.js-plotly-plot {
  margin: 1rem 0 !important;
  padding: 1rem;
  background: rgba(255,255,255,0.07) !important;
  border-radius: 12px;
}
.stMetric {
  margin: 1rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Header com autores e objetivo
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-card" style="text-align:center;">
  <h1>🚢 Análise de Levantamentos de Cancelamentos de Navios</h1>
  <p><b>Projeto Acadêmico</b> – Arley do Nascimento Vinagre (12722132338), Vinicius Santana (1272221567), Tauan Santos Santana (12722216126)</p>
  <em>Objetivo: Analisar planilhas Excel de portos sobre navios cancelados, oferecendo gráficos e métricas interativas para apoiar decisões operacionais.</em>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar: Upload, filtro por nome e referências de custo
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload & Filtros")
    uploaded_file = st.file_uploader("Faça upload do Excel (.xlsx)", type="xlsx")
    nome_filtro = st.text_input("🔍 Filtrar Navio por Nome", help="Digite parte ou todo o nome do navio (case-insensitive).")
    st.markdown("---")
    st.markdown("### 💰 Referências de Custos (2024-25)")
    st.write(f"- THC: R$ {CUSTOS['THC']:,.2f} / TEU")
    st.write(f"- Operação Terminal: R$ {CUSTOS['OPER']:,.2f} / cancelamento")
    st.write(f"- Despachante: R$ {CUSTOS['DOC']:,.2f}")
    st.write(f"- Armazenagem: R$ {CUSTOS['ARM_DAY']:,.2f} / TEU / dia × {CUSTOS['ARM_DAYS']} dias")
    st.write(f"- Scanner/Fitossanitária: R$ {CUSTOS['INSP']:,.2f} / contêiner")

if not uploaded_file:
    st.warning("Por favor, carregue o arquivo Excel para iniciar a análise.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Leitura e pré-processamento do Excel
# ──────────────────────────────────────────────────────────────────────────────
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()

col_navio       = 'Navio / Viagem'             if 'Navio / Viagem' in df.columns else None
col_status      = 'Situação'                   if 'Situação'       in df.columns else None
col_data        = 'Estimativa Chegada ETA'     if 'Estimativa Chegada ETA' in df.columns else None
col_etd         = 'Estimativa Saída ETD'       if 'Estimativa Saída ETD'   in df.columns else None
col_rota        = 'De / Para'                  if 'De / Para'      in df.columns else None
col_tipo_navio  = 'Tipo'                       if 'Tipo'           in df.columns else None
col_conteineres = 'Movs'                       if 'Movs'           in df.columns else None
col_armador     = 'Armador'                    if 'Armador'        in df.columns else None
col_pais        = 'País'                       if 'País'           in df.columns else None
col_servico     = 'Serviço'                    if 'Serviço'        in df.columns else None
col_berco       = 'Berço'                      if 'Berço'          in df.columns else None

if col_navio is None or col_status is None:
    st.error("As colunas obrigatórias 'Navio / Viagem' e 'Situação' não foram encontradas.")
    st.stop()

# Filtrar apenas registros cancelados
df[col_status] = df[col_status].astype(str).str.strip().str.lower()
mask_cancel   = df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])
df_cancel     = df.loc[mask_cancel].copy()
if df_cancel.empty:
    st.warning("Não foram encontrados registros de navios cancelados.")
    st.stop()

# Filtro adicional por nome de navio
if nome_filtro:
    df_cancel = df_cancel[df_cancel[col_navio].str.contains(nome_filtro, case=False, na=False)]
    if df_cancel.empty:
        st.warning(f"Nenhum navio contendo '{nome_filtro}' foi encontrado.")
        st.stop()

# Converter colunas numéricas e de data
if col_conteineres:
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)

if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
    df_cancel = df_cancel.dropna(subset=[col_data])
    df_cancel['Ano'] = df_cancel[col_data].dt.year
    df_cancel['Mês'] = df_cancel[col_data].dt.month
    df_cancel['Y-M'] = df_cancel[col_data].dt.to_period('M').astype(str)
else:
    st.warning("Coluna de data 'Estimativa Chegada ETA' não encontrada; análises temporais limitadas.")

if col_data and col_etd:
    df_cancel[col_etd] = pd.to_datetime(df_cancel[col_etd], dayfirst=True, errors='coerce')
    df_cancel['Tempo_Permanencia'] = (
        (df_cancel[col_etd] - df_cancel[col_data])
        .dt.total_seconds() / 3600
    )

if col_conteineres:
    df_cancel = calcular_custos(df_cancel, col_conteineres)

# ──────────────────────────────────────────────────────────────────────────────
# Pré-computar tabelas de contagem robustas
# ──────────────────────────────────────────────────────────────────────────────
# Navios
contagem_navios = (
    df_cancel[col_navio]
    .value_counts()
    .to_frame(name='Cancelamentos')
    .reset_index()
)
contagem_navios.columns = ['Navio', 'Cancelamentos']
contagem_navios['Cancelamentos'] = pd.to_numeric(contagem_navios['Cancelamentos'], errors='coerce').fillna(0)

# Mensal
contagem_mensal = (
    df_cancel.groupby('Y-M')
             .size()
             .reset_index(name='Cancelamentos')
             .sort_values('Y-M')
)

# Rotas
contagem_rotas = pd.DataFrame()
if col_rota:
    contagem_rotas = (
        df_cancel[col_rota]
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_rotas.columns = ['Rota', 'Cancelamentos']

# Tipo de Navio
contagem_tipo = pd.DataFrame()
if col_tipo_navio:
    contagem_tipo = (
        df_cancel[col_tipo_navio]
        .astype(str).str.capitalize()
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_tipo.columns = ['TipoNavio', 'Cancelamentos']

# Armadores
contagem_armadores = pd.DataFrame()
if col_armador:
    contagem_armadores = (
        df_cancel[col_armador]
        .astype(str).str.capitalize()
        .replace({'nan': 'Não Informado', 'None': 'Não Informado', '': 'Não Informado'})
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_armadores.columns = ['Armador', 'Cancelamentos']

# Serviços
contagem_servicos = pd.DataFrame()
if col_servico:
    contagem_servicos = (
        df_cancel[col_servico]
        .astype(str).str.capitalize()
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_servicos.columns = ['Serviço', 'Cancelamentos']

# Países
contagem_paises = pd.DataFrame()
if col_pais:
    contagem_paises = (
        df_cancel[col_pais]
        .astype(str).str.capitalize()
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_paises.columns = ['País', 'Cancelamentos']

# Berços
contagem_bercos = pd.DataFrame()
if col_berco:
    contagem_bercos = (
        df_cancel[col_berco]
        .astype(str).str.capitalize()
        .value_counts()
        .to_frame(name='Cancelamentos')
        .reset_index()
    )
    contagem_bercos.columns = ['Berço', 'Cancelamentos']

# ──────────────────────────────────────────────────────────────────────────────
# Resumo rápido na sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Resumo Após Filtros")
    st.write(f"- Total de registros: {len(df):,}")
    st.write(f"- Total de cancelamentos filtrados: {len(df_cancel):,}")
    if not contagem_navios.empty:
        top_nav = contagem_navios.iloc[0]
        st.write(f"- Navio mais cancelado: **{top_nav['Navio']}** ({int(top_nav['Cancelamentos'])})")
    if not contagem_mensal.empty:
        m = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        st.write(f"- Mês crítico: **{m['Y-M']}** ({int(m['Cancelamentos'])})")

# ──────────────────────────────────────────────────────────────────────────────
# Abas de Análise
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Visão Geral",
    "🚢 Top Navios & Armadores",
    "📅 Análise Temporal",
    "🌍 Rotas & Países",
    "📊 Distribuições & Correlações",
    "💰 Análise de Custos"
])

# Tab 1: Visão Geral
with tab1:
    st.header("📈 Visão Geral dos Cancelamentos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Linhas", f"{len(df):,}")
    c2.metric("Cancelamentos", f"{len(df_cancel):,}", f"{len(df_cancel)/len(df)*100:.1f}%")
    if col_conteineres:
        c3.metric("TEUs Afetados", f"{df_cancel[col_conteineres].sum():,}")
    if col_data:
        dias = (df_cancel[col_data].max() - df_cancel[col_data].min()).days
        c4.metric("Período Analisado", f"{dias:,} dias")

    fig_pie = px.pie(
        names=['Cancelados', 'Não Cancelados'],
        values=[len(df_cancel), len(df) - len(df_cancel)],
        title='Distribuição de Cancelamentos',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(ajustar_layout_grafico(fig_pie, 350), use_container_width=True)

# Tab 2: Top Navios & Armadores
with tab2:
    st.header("🚢 Top Navios")
    if not contagem_navios.empty:
        fig_nav = px.bar(
            data_frame=contagem_navios.head(10),
            x='Cancelamentos', y='Navio',
            orientation='h', color='Cancelamentos',
            color_continuous_scale='Viridis',
            title="Top 10 Navios Cancelados"
        )
        st.plotly_chart(ajustar_layout_grafico(fig_nav), use_container_width=True)
        st.dataframe(contagem_navios.head(10), use_container_width=True)
    else:
        st.info("Nenhum dado de navio disponível.")

    st.markdown("---")
    st.header("🏢 Top Armadores")
    if not contagem_armadores.empty:
        fig_arm = px.bar(
            data_frame=contagem_armadores.head(10),
            x='Cancelamentos', y='Armador',
            orientation='h', color='Cancelamentos',
            color_continuous_scale='Viridis',
            title="Top 10 Armadores"
        )
        st.plotly_chart(ajustar_layout_grafico(fig_arm), use_container_width=True)
        st.dataframe(contagem_armadores.head(10), use_container_width=True)
    else:
        st.info("Nenhum dado de armador disponível.")

# Tab 3: Análise Temporal
with tab3:
    st.header("📅 Cancelamentos por Mês")
    if not contagem_mensal.empty:
        fig_time = px.line(
            data_frame=contagem_mensal,
            x='Y-M', y='Cancelamentos',
            title="Evolução Mensal de Cancelamentos",
            markers=True
        )
        fig_time.update_layout(xaxis_title="Mês", yaxis_title="Qtde")
        st.plotly_chart(ajustar_layout_grafico(fig_time), use_container_width=True)
        st.dataframe(contagem_mensal, use_container_width=True)
    else:
        st.info("Dados temporais indisponíveis.")

# Tab 4: Rotas & Países
with tab4:
    st.header("🌍 Rotas com Mais Cancelamentos")
    if not contagem_rotas.empty:
        fig_rot = px.bar(
            data_frame=contagem_rotas.head(10),
            x='Cancelamentos', y='Rota',
            orientation='h', color='Cancelamentos',
            color_continuous_scale='Viridis',
            title="Top 10 Rotas"
        )
        st.plotly_chart(ajustar_layout_grafico(fig_rot), use_container_width=True)
        st.dataframe(contagem_rotas.head(10), use_container_width=True)
    else:
        st.info("Dados de rotas indisponíveis.")

    st.markdown("---")
    st.header("🗺️ Países com Mais Cancelamentos")
    if not contagem_paises.empty:
        fig_pais = px.bar(
            data_frame=contagem_paises.head(10),
            x='Cancelamentos', y='País',
            orientation='h', color='Cancelamentos',
            color_continuous_scale='Viridis',
            title="Top 10 Países"
        )
        st.plotly_chart(ajustar_layout_grafico(fig_pais), use_container_width=True)
        st.dataframe(contagem_paises.head(10), use_container_width=True)
    else:
        st.info("Dados de países indisponíveis.")

# Tab 5: Distribuições & Correlações
with tab5:
    st.header("📊 Distribuições e Correlações")
    sub1, sub2, sub3 = st.tabs(["Tipo de Navio", "Contêineres", "Correlação Numérica"])

    with sub1:
        if not contagem_tipo.empty:
            fig_tipo = px.pie(
                data_frame=contagem_tipo,
                names='TipoNavio', values='Cancelamentos',
                title="Distribuição por Tipo de Navio",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(ajustar_layout_grafico(fig_tipo, 400), use_container_width=True)
            st.dataframe(contagem_tipo, use_container_width=True)
        else:
            st.info("Dados de tipo de navio indisponíveis.")

    with sub2:
        if col_conteineres:
            desc = df_cancel[col_conteineres].describe().round(1).reset_index()
            st.subheader("Estatísticas de Contêineres")
            st.dataframe(desc, use_container_width=True)
            fig_hist = px.histogram(
                data_frame=df_cancel,
                x=col_conteineres,
                nbins=20,
                title="Histograma de TEUs",
                color_discrete_sequence=['#4CAF50']
            )
            st.plotly_chart(ajustar_layout_grafico(fig_hist), use_container_width=True)
        else:
            st.info("Coluna de contêineres ausente.")

    with sub3:
        nums = df_cancel.select_dtypes(include=[np.number]).columns
        if len(nums) > 1:
            corr = df_cancel[nums].corr()
            fig_corr = px.imshow(
                data_frame=corr, text_auto=True,
                title="Matriz de Correlação",
                color_continuous_scale='RdBu'
            )
            st.plotly_chart(ajustar_layout_grafico(fig_corr), use_container_width=True)
            st.dataframe(corr, use_container_width=True)
        else:
            st.info("Colunas numéricas insuficientes para correlação.")

# Tab 6: Análise de Custos
with tab6:
    st.header("💰 Análise de Custos de Exportação")
    if 'CUSTO_TOTAL' in df_cancel.columns:
        total = df_cancel['CUSTO_TOTAL'].sum()
        medio = df_cancel['CUSTO_TOTAL'].mean()
        colA, colB = st.columns(2)
        colA.metric("Custo Total Perdido", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        colB.metric("Custo Médio / Cancel.", f"R$ {medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        fig_box = px.box(
            data_frame=df_cancel,
            y='CUSTO_TOTAL',
            title="Distribuição do Custo por Cancelamento"
        )
        st.plotly_chart(ajustar_layout_grafico(fig_box), use_container_width=True)

        componentes = (
            df_cancel[["C_TEUS", "C_OPER", "C_DOC", "C_ARM", "C_INSP"]]
            .sum()
            .rename(index={
                "C_TEUS": "THC (Terminal Handling Charge)",
                "C_OPER": "Taxa de Cancelamento",
                "C_DOC":  "Honorários de Despacho",
                "C_ARM":  "Armazenagem (2 dias)",
                "C_INSP":"Scanner/Fitossanitária"
            })
            .reset_index()
            .rename(columns={"index": "Tipo de Custo", 0: "Valor Total (BRL)"})
        )
        comp_fmt = componentes.copy()
        comp_fmt["Valor Total (BRL)"] = comp_fmt["Valor Total (BRL)"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        st.markdown("""
            <div style='background: rgba(255,255,255,0.10); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                <h4 style='color: #4CAF50; margin-bottom: 0.7rem;'>📊 Detalhamento dos Custos</h4>
                <p style='font-size: 0.9rem; margin-bottom: 0.5rem;'>Composição dos valores por item:</p>
                <ul style='font-size: 0.85rem; padding-left: 1rem;'>
                    <li><strong>THC:</strong> R$ 1.200,00 por TEU (20' dry)</li>
                    <li><strong>Taxa de Cancelamento:</strong> R$ 1.150,00 por operação</li>
                    <li><strong>Despachante:</strong> R$ 950,00 (mínimo tabela Sindaesc)</li>
                    <li><strong>Armazenagem:</strong> R$ 575,00/TEU/dia × 2 dias</li>
                    <li><strong>Scanner:</strong> R$ 95,00 por contêiner</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(comp_fmt, hide_index=True, use_container_width=True)
        with col2:
            fig_pie2 = px.pie(
                data_frame=componentes,
                values="Valor Total (BRL)",
                names="Tipo de Custo",
                title="Distribuição dos Custos",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(ajustar_layout_grafico(fig_pie2, 400), use_container_width=True)
    else:
        st.info("Não foi possível calcular custos (coluna de TEUs ausente).")
