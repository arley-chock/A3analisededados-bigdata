# -*- coding: utf-8 -*-
"""
Análise de Levantamentos de Portos sobre Navios Cancelados
Trabalho acadêmico desenvolvido por:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana            (1272221567)
- Tauan Santos Santana        (12722216126)
"""

# ────────────────────────────────────────────────────────
# 1. Importações
# ────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ────────────────────────────────────────────────────────
# 2. Configuração da página
# ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚓ Dashboard Marítimo de Cancelamentos",
    page_icon="🚢",
    layout="wide"
)

# ────────────────────────────────────────────────────────
# 3. Estilo global (tema náutico)
# ────────────────────────────────────────────────────────
st.markdown(
    """
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
    h1,h2,h3,h4 {text-align:center;margin-bottom:0.5rem;}
    section.main > div.block-container {padding:2rem 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────────────
# 4. Cabeçalho
# ────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dashboard-card">
      <h1>⚓ Análise de Cancelamentos de Navios</h1>
      <p>Dashboard interativo desenvolvido por:<br>
         <b>Arley do Nascimento Vinagre</b> · 
         <b>Vinicius Santana</b> · 
         <b>Tauan Santos Santana</b></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────────────
# 5. Funções utilitárias
# ────────────────────────────────────────────────────────
def ajustar_layout_grafico(fig, altura: int = 450):
    """Aplica tema e dimensões padrão aos gráficos Plotly."""
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def map_col(col_name: str, frame: pd.DataFrame) -> str | None:
    """Retorna o nome da coluna se existir; caso contrário, None."""
    return col_name if col_name in frame.columns else None


def calcular_custos(df: pd.DataFrame, coluna_teu: str) -> pd.DataFrame:
    """Adiciona campos de custo ao dataframe de cancelamentos."""
    CUSTOS = {
        "THC_TEUS":            1200.0,   # R$ / TEU
        "OPER_CANCEL":         1150.0,   # R$ fixo por operação
        "DESPACHO":             950.0,   # R$
        "ARMAZ_DIA_TEUS":       575.0,   # R$ / TEU / dia
        "ARMAZ_DIAS_EXTRA":        2,
        "SCANNER":               95.0    # R$ / contêiner
    }

    df = df.copy()
    df[coluna_teu] = pd.to_numeric(df[coluna_teu], errors="coerce").fillna(0)

    df["C_TEUS"] = df[coluna_teu] * CUSTOS["THC_TEUS"]
    df["C_OPER"] = CUSTOS["OPER_CANCEL"]
    df["C_DOC"]  = CUSTOS["DESPACHO"]
    df["C_ARM"]  = df[coluna_teu] * CUSTOS["ARMAZ_DIA_TEUS"] * CUSTOS["ARMAZ_DIAS_EXTRA"]
    df["C_INSP"] = CUSTOS["SCANNER"]

    df["CUSTO_TOTAL"] = df[["C_TEUS", "C_OPER", "C_DOC", "C_ARM", "C_INSP"]].sum(axis=1)
    return df


# ────────────────────────────────────────────────────────
# 6. Sidebar – Upload & filtros
# ────────────────────────────────────────────────────────
with st.sidebar:
    uploaded_file = st.file_uploader("📂 Faça upload do Excel (.xlsx)", type="xlsx")
    termo = st.text_input("🔍 Filtrar por navio, armador ou rota")

    st.markdown("---")
    st.markdown(
        """
        <small>Valores de custos referência (tabela 2024-25):<br>
        • THC R$ 1.200/TEU · Armazenagem R$ 575/TEU/dia ·
        Despachante R$ 950 · Scanner R$ 95/cont.</small>
        """,
        unsafe_allow_html=True,
    )

if uploaded_file is None:
    st.warning("Envie um arquivo Excel para iniciar a análise.")
    st.stop()

# ────────────────────────────────────────────────────────
# 7. Leitura do arquivo e mapeamento de colunas
# ────────────────────────────────────────────────────────
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Não foi possível ler o arquivo: {e}")
    st.stop()

col_navio       = map_col("Navio / Viagem",        df)
col_status      = map_col("Situação",              df)
col_data        = map_col("Estimativa Chegada ETA",df)
col_motivo      = map_col("MotivoCancelamento",    df)
col_rota        = map_col("De / Para",             df)
col_armador     = map_col("Armador",               df)
col_tipo_navio  = map_col("Tipo",                  df)
col_conteineres = map_col("Movs",                  df)

if col_status is None:
    st.error("Coluna de status ('Situação') não encontrada no Excel.")
    st.stop()

# ────────────────────────────────────────────────────────
# 8. Filtragem de cancelamentos
# ────────────────────────────────────────────────────────
df[col_status] = df[col_status].astype(str).str.strip().str.lower()
mask_cancel = df[col_status].isin(
    ["cancelado", "cancelada", "rejeitado", "rej.", "canceled"]
)
df_cancel = df.loc[mask_cancel].copy()

if df_cancel.empty:
    st.info("Nenhum registro de cancelamento encontrado.")
    st.stop()

# ───── Conversão de datas
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors="coerce")

# ───── Cálculo de custos antes de qualquer gráfico
if col_conteineres:
    df_cancel = calcular_custos(df_cancel, col_conteineres)

# ────────────────────────────────────────────────────────
# 9. Enriquecimento temporal
# ────────────────────────────────────────────────────────
if col_data:
    df_cancel["Ano"]  = df_cancel[col_data].dt.year
    df_cancel["Mês"]  = df_cancel[col_data].dt.month
    df_cancel["Y-M"]  = df_cancel[col_data].dt.to_period("M").astype(str)

# ────────────────────────────────────────────────────────
# 10. Resumo na sidebar
# ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Resumo")
    st.write(f"**Total de cancelamentos:** {len(df_cancel):,}")

    # Navio mais cancelado
    if col_navio:
        top_navio = (
            df_cancel[col_navio].value_counts().idxmax()
            if not df_cancel[col_navio].isna().all()
            else "N/D"
        )
        st.write(f"**Navio mais cancelado:** {top_navio}")

    # Mês com mais cancelamentos
    if col_data:
        contagem_mensal = df_cancel["Y-M"].value_counts()
        mes_max = contagem_mensal.idxmax()
        st.write(f"**Mês crítico:** {mes_max}")

# ────────────────────────────────────────────────────────
# 11. Criação das abas
# ────────────────────────────────────────────────────────
aba_visao, aba_navios, aba_tempo, aba_rotas, aba_custos = st.tabs(
    ["📈 Visão Geral", "🚢 Navios", "📅 Tempo", "🌍 Rotas", "💰 Custos"]
)

# 11-A ▸ Visão Geral
with aba_visao:
    st.header("📈 Visão Geral dos Cancelamentos")

    # Métricas principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Registros totais", f"{len(df):,}")
    col2.metric("Cancelados", f"{len(df_cancel):,}",
                delta=f"{len(df_cancel)/len(df)*100:.1f}%")
    if col_conteineres:
        col3.metric("TEUs afetados",
                    f"{df_cancel[col_conteineres].sum():,.0f}")

    # Gráfico de pizza cancelados × não cancelados
    fig_pizza = px.pie(
        names=["Cancelados", "Não cancelados"],
        values=[len(df_cancel), len(df) - len(df_cancel)],
        title="Distribuição de Cancelamentos",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(ajustar_layout_grafico(fig_pizza, 400), use_container_width=True)

# 11-B ▸ Navios
with aba_navios:
    st.header("🚢 Navios com Mais Cancelamentos")
    if col_navio:
        contagem_navios = df_cancel[col_navio].value_counts().reset_index()
        contagem_navios.columns = ["Navio", "Cancelamentos"]

        st.dataframe(contagem_navios.head(10), use_container_width=True)

        fig_bar = px.bar(
            contagem_navios.head(5),
            y="Navio",
            x="Cancelamentos",
            orientation="h",
            title="Top 5 Navios mais Cancelados",
            color="Cancelamentos",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(ajustar_layout_grafico(fig_bar), use_container_width=True)
    else:
        st.info("Coluna de navio não encontrada.")

# 11-C ▸ Tempo
with aba_tempo:
    st.header("📅 Cancelamentos ao Longo do Tempo")
    if col_data:
        contagem_mensal = (
            df_cancel["Y-M"].value_counts().sort_index().reset_index()
        )
        contagem_mensal.columns = ["Y-M", "Cancelamentos"]

        fig_line = px.line(
            contagem_mensal,
            x="Y-M",
            y="Cancelamentos",
            title="Evolução Mensal de Cancelamentos",
            markers=True,
        )
        st.plotly_chart(ajustar_layout_grafico(fig_line), use_container_width=True)
        st.dataframe(contagem_mensal, use_container_width=True)
    else:
        st.info("Coluna de data não disponível.")

# 11-D ▸ Rotas
with aba_rotas:
    st.header("🌍 Rotas Impactadas")
    if col_rota:
        contagem_rotas = df_cancel[col_rota].value_counts().reset_index()
        contagem_rotas.columns = ["Rota", "Cancelamentos"]

        st.dataframe(contagem_rotas.head(10), use_container_width=True)

        fig_rotas = px.bar(
            contagem_rotas.head(5),
            x="Rota",
            y="Cancelamentos",
            title="Top 5 Rotas com Mais Cancelamentos",
            color="Cancelamentos",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(ajustar_layout_grafico(fig_rotas), use_container_width=True)
    else:
        st.info("Coluna de rota não encontrada.")

# 11-E ▸ Custos
with aba_custos:
    st.header("💰 Análise de Custos de Exportação")
    if "CUSTO_TOTAL" in df_cancel.columns:
        total = df_cancel["CUSTO_TOTAL"].sum()
        medio = df_cancel["CUSTO_TOTAL"].mean()

        col1, col2 = st.columns(2)
        col1.metric("Custo total perdido", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Custo médio por cancelamento", f"R$ {medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        fig_custo = px.box(
            df_cancel,
            y="CUSTO_TOTAL",
            title="Distribuição do Custo por Cancelamento",
        )
        st.plotly_chart(ajustar_layout_grafico(fig_custo), use_container_width=True)
    else:
        st.info("Não foi possível calcular custos – coluna de TEUs ausente.")
