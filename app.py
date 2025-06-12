# -*- coding: utf-8 -*-
"""
⚓ Dashboard Marítimo – Cancelamentos de Navios
Trabalho acadêmico:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana            (1272221567)
- Tauan Santos Santana        (12722216126)
"""
# ─────────────────────────────────── importações
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────── configuração global
st.set_page_config("⚓ Cancelamentos de Navios", "🚢", layout="wide")

THEME_CSS = """
<style>
[data-testid="stAppViewContainer"]{
  background:linear-gradient(180deg,#0a1f2f 0%,#02111e 100%);
  color:#E0E0E0;}
.dashboard-card{
  background:rgba(255,255,255,.05);
  padding:1.5rem;border-radius:12px;
  margin-bottom:2rem;border:1px solid #0f3851;}
h1,h2,h3,h4{text-align:center;margin-bottom:.5rem;}
section.main>div.block-container{padding:2rem 1rem;}
[data-testid="stSidebar"]>div{padding-top:1rem;}
.stSelectbox>div>div{color:#0a84ff;}
</style>"""
st.markdown(THEME_CSS, unsafe_allow_html=True)

# ─────────────────────────────────── cabeçalho
st.markdown(
    """
<div class="dashboard-card">
  <h1>⚓ Cancelamentos de Navios – Dashboard Interativo</h1>
  <p>Desenvolvido por <b>Arley</b>, <b>Vinicius</b> e <b>Tauan</b> – Análise de Dados Portuários.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────── funções utilitárias
def ajustar(fig, h=420):
    fig.update_layout(template="plotly_dark", height=h, margin=dict(l=40, r=40, t=60, b=40))
    return fig

def money(v):  # formatação BRL
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def map_col(name, df):  # mapeamento resiliente
    return name if name in df.columns else None

def calcular_custos(df, col_teu, custos):
    df = df.copy()
    df[col_teu] = pd.to_numeric(df[col_teu], errors="coerce").fillna(0)
    df["C_TEUS"] = df[col_teu] * custos["THC_TEUS"]
    df["C_OPER"] = custos["OPER_CANCEL"]
    df["C_DOC"]  = custos["DESPACHO"]
    df["C_ARM"]  = df[col_teu] * custos["ARMAZ_DIA_TEUS"] * custos["ARMAZ_DIAS_EXTRA"]
    df["C_INSP"] = custos["SCANNER"]
    df["CUSTO_TOTAL"] = df[["C_TEUS", "C_OPER", "C_DOC", "C_ARM", "C_INSP"]].sum(axis=1)
    return df

# ─────────────────────────────────── sidebar – upload & filtros
with st.sidebar:
    arquivo = st.file_uploader("📂 Carregar planilha Excel", type="xlsx")
    filtro  = st.text_input("🔍 Filtrar navio ou armador (contém)")

    st.markdown("---")
    st.markdown("<small>Base de custos 2024–25 (alterar em código se necessário).</small>",
                unsafe_allow_html=True)

if not arquivo:
    st.warning("Envie um arquivo '.xlsx' para iniciar.")
    st.stop()

# ─────────────────────────────────── leitura e pré-processamento
df = pd.read_excel(arquivo)

col_navio       = map_col("Navio / Viagem",        df)
col_status      = map_col("Situação",              df)
col_data        = map_col("Estimativa Chegada ETA",df)
col_rota        = map_col("De / Para",             df)
col_armador     = map_col("Armador",               df)
col_teu         = map_col("Movs",                  df)

if not col_status:
    st.error("Coluna 'Situação' ausente – ajuste a planilha.")
    st.stop()

df[col_status] = df[col_status].astype(str).str.lower().str.strip()
cancel_mask = df[col_status].isin(["cancelado","cancelada","rejeitado","rej.","canceled"])
df_cancel = df.loc[cancel_mask].copy()

if df_cancel.empty:
    st.error("Nenhuma linha com status de cancelamento encontrada.")
    st.stop()

# filtro por texto
if filtro:
    flt = filtro.lower()
    if col_navio:
        df_cancel = df_cancel[df_cancel[col_navio].astype(str).str.lower().str.contains(flt)]
    if col_armador and df_cancel.empty:
        df_cancel = df_cancel[df_cancel[col_armador].astype(str).str.lower().str.contains(flt)]
    if df_cancel.empty:
        st.warning("Filtro não retornou resultados.")
        st.stop()

# datas
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors="coerce")
    df_cancel["YM"] = df_cancel[col_data].dt.to_period("M").astype(str)

# custos
CUSTOS = dict(
    THC_TEUS        = 1200.0,
    OPER_CANCEL     = 1150.0,
    DESPACHO        =  950.0,
    ARMAZ_DIA_TEUS  =  575.0,
    ARMAZ_DIAS_EXTRA=    2 ,
    SCANNER         =   95.0,
)
if col_teu: df_cancel = calcular_custos(df_cancel, col_teu, CUSTOS)

# ─────────────────────────────────── abas
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["📊 Visão Geral", "🚢 Navios", "📅 Temporal", "🌍 Rotas", "💰 Custos"]
)

# ── aba 1: visão geral
with aba1:
    colA, colB, colC = st.columns(3)
    colA.metric("Linhas totais", f"{len(df):,}")
    colB.metric("Cancelamentos", f"{len(df_cancel):,}", f"{len(df_cancel)/len(df)*100:.1f}%")
    if col_teu:
        colC.metric("TEUs afetados", f"{df_cancel[col_teu].sum():,.0f}")

    # waffle / pizza
    fig_pie = px.pie(
        names=["Cancelados","Não cancelados"],
        values=[len(df_cancel),len(df)-len(df_cancel)],
        hole=.45, title="Proporção de Cancelamentos",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(ajustar(fig_pie,350), use_container_width=True)

# ── aba 2: navios
with aba2:
    st.subheader("Navios mais afetados")
    if col_navio:
        topn = df_cancel[col_navio].value_counts().reset_index()
        topn.columns = ["Navio","Cancelamentos"]

        fig = px.bar(
            topn.head(10), y="Navio", x="Cancelamentos", orientation="h",
            title="Top 10 Navios Cancelados", color="Cancelamentos",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(ajustar(fig), use_container_width=True)
        st.dataframe(topn, use_container_width=True)
    else:
        st.info("Coluna de navio não disponível.")

# ── aba 3: tempo
with aba3:
    if col_data:
        st.subheader("Evolução mensal")
        mensal = df_cancel["YM"].value_counts().sort_index().reset_index()
        mensal.columns = ["YM","Cancelamentos"]

        fig = px.line(mensal, x="YM", y="Cancelamentos", markers=True,
                      title="Cancelamentos por mês")
        st.plotly_chart(ajustar(fig), use_container_width=True)
        st.dataframe(mensal, use_container_width=True)
    else:
        st.info("Planilha não tem coluna de data.")

# ── aba 4: rotas
with aba4:
    if col_rota:
        st.subheader("Rotas com mais cancelamentos")
        rot = df_cancel[col_rota].value_counts().reset_index()
        rot.columns=["Rota","Cancelamentos"]
        fig = px.bar(rot.head(10), x="Rota", y="Cancelamentos",
                     title="Top 10 Rotas", color="Cancelamentos",
                     color_continuous_scale="Viridis")
        st.plotly_chart(ajustar(fig), use_container_width=True)
        st.dataframe(rot, use_container_width=True)
    else:
        st.info("Coluna de rota ausente.")

# ── aba 5: custos
with aba5:
    if "CUSTO_TOTAL" in df_cancel.columns:
        st.subheader("Resumo financeiro dos cancelamentos")

        total = df_cancel["CUSTO_TOTAL"].sum()
        medio = df_cancel["CUSTO_TOTAL"].mean()
        col1,col2 = st.columns(2)
        col1.metric("Custo total", money(total))
        col2.metric("Custo médio", money(medio))

        fig_box = px.box(df_cancel, y="CUSTO_TOTAL",
                         title="Distribuição do custo por cancelamento")
        st.plotly_chart(ajustar(fig_box), use_container_width=True)

        comp = df_cancel[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum().reset_index()
        comp.columns=["Tipo","Valor"]
        comp["Tipo"] = comp["Tipo"].map({
            "C_TEUS":"THC", "C_OPER":"Cancelamento",
            "C_DOC":"Despacho", "C_ARM":"Armazenagem", "C_INSP":"Scanner"})
        fig_pie2 = px.pie(comp, names="Tipo", values="Valor",
                          title="Composição de custos",
                          color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(ajustar(fig_pie2,400), use_container_width=True)
        st.dataframe(comp.assign(Valor=comp["Valor"].apply(money)),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Sem coluna de TEUs → custos não calculados.")
