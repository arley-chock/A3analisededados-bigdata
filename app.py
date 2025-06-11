# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Cancelamentos de navios", layout="wide")

# ------------------------------------------------------------------
# 1) Uploads
# ------------------------------------------------------------------
st.sidebar.header("📂 Arquivos necessários")
col1, col2 = st.sidebar.columns(2)
with col1:
    op_file = st.file_uploader("Programação de Navios", type="xlsx", key="op")
with col2:
    exp_file = st.file_uploader("Exportações mensais", type="xlsx", key="exp")

if not op_file:
    st.warning("Faça upload do arquivo de operações para iniciar.")
    st.stop()

# ------------------------------------------------------------------
# 2) Pré-processamento robusto
# ------------------------------------------------------------------
df = pd.read_excel(op_file)
df.columns = df.columns.str.strip()            # remove espaços extras

# Helper para pegar o 1º nome de coluna existente
def pick(*cands):
    return next((c for c in cands if c in df.columns), None)

col_navio   = pick('Navio / Viagem.1', 'Navio / Viagem')
col_status  = pick('Situação', 'Status')
col_data    = pick('ETA', 'Estimativa Chegada ETA')
col_conteineres = pick('Movs', 'TEU', 'QtdConteiner')
col_armador = pick('Armador')
col_rota    = pick('De / Para')
col_tipo    = pick('Tipo')

# Padroniza status
df[col_status] = df[col_status].str.lower().str.strip()
cancel_mask = df[col_status].isin(['cancelado','cancelada','canceled','rej.','rejeitado'])
df_cancel = df.loc[cancel_mask].copy()

# Converte datas
df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce', dayfirst=True)

# ------------------------------------------------------------------
# 3) Tratamento de outliers em Movs
# ------------------------------------------------------------------
df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
q99 = df_cancel[col_conteineres].quantile(0.99)      # limite superior
df_cancel.loc[df_cancel[col_conteineres] > q99, col_conteineres] = q99

# ------------------------------------------------------------------
# 4) Parâmetros ajustáveis pelo usuário
# ------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Parâmetros de custo")
    custo_teu   = st.number_input("Custo médio por contêiner (US$)",  min_value=10.0,
                                  max_value=1000.0, value=350.0, step=10.0)
    custo_op    = st.number_input("Custo fixo de operação", 1000.0, 20000.0, 8000.0, 500.0)
    custo_doc   = st.number_input("Custo fixo de documentação", 500.0, 15000.0, 3500.0, 500.0)
    custo_ins   = st.number_input("Custo de inspeção", 0.0, 10000.0, 1500.0, 100.0)
    dias_arm    = st.number_input("Dias de armazenagem considerados", 0, 30, 3, 1)
    custo_dia_arm = st.number_input("Custo armazenagem por TEU/dia", 10.0, 500.0, 200.0, 10.0)

# ------------------------------------------------------------------
# 5) Cálculo de custos (agora controlável)
# ------------------------------------------------------------------
df_cancel["C_Container"]  = df_cancel[col_conteineres] * custo_teu
df_cancel["C_Operacao"]   = custo_op
df_cancel["C_Documento"]  = custo_doc
df_cancel["C_Armazenagem"]= df_cancel[col_conteineres] * custo_dia_arm * dias_arm
df_cancel["C_Inspecao"]   = custo_ins

df_cancel["Custo_Total"]  = df_cancel[["C_Container","C_Operacao",
                                       "C_Documento","C_Armazenagem",
                                       "C_Inspecao"]].sum(axis=1)

# ------------------------------------------------------------------
# 6) Métricas-chave
# ------------------------------------------------------------------
st.title("🚢 Análise de Cancelamentos de Navios")

colA, colB, colC = st.columns(3)
colA.metric("Total de registros", f"{len(df):,}")
colA.metric("Total cancelados", f"{len(df_cancel):,}")

dias_periodo = (df_cancel[col_data].max() - df_cancel[col_data].min()).days + 1
taxa_diaria  = len(df_cancel) / dias_periodo if dias_periodo else np.nan
colB.metric("Média diária de cancelamentos",
            f"{taxa_diaria:.2f} / dia", help=f"Período: {dias_periodo} dias")

custo_total = df_cancel["Custo_Total"].sum()
colC.metric("Custo total estimado", f"US$ {custo_total:,.0f}")

# ------------------------------------------------------------------
# 7) Gráficos principais
# ------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Visão geral", "Custos", "Time series"])

with tab1:
    fig = px.pie(values=[len(df_cancel), len(df)-len(df_cancel)],
                 names=["Cancelados","Outros"], hole=.4,
                 title="Proporção de cancelamentos")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top navios")
    st.dataframe(df_cancel[col_navio].value_counts().head(10), use_container_width=True)

with tab2:
    fig = px.box(df_cancel, y="Custo_Total",
                 title="Distribuição dos custos por cancelamento")
    st.plotly_chart(fig, use_container_width=True)

    if col_armador:
        custos_arm = (df_cancel.groupby(col_armador)["Custo_Total"]
                      .sum().sort_values(ascending=False).head(10))
        st.subheader("Top 10 armadores por custo total")
        st.dataframe(custos_arm, use_container_width=True)

with tab3:
    serie = (df_cancel
             .dropna(subset=[col_data])
             .groupby(df_cancel[col_data].dt.to_period("M"))
             .size().rename("Cancelamentos")
             .to_frame()
             .reset_index())
    serie["Mês"] = serie[col_data].astype(str)
    fig = px.line(serie, x="Mês", y="Cancelamentos", markers=True,
                  title="Evolução mensal dos cancelamentos")
    st.plotly_chart(fig, use_container_width=True)

    # Integração opcional com arquivo de exportações
    if exp_file:
        df_exp = pd.read_excel(exp_file)
        # converte "Mês" (pt-BR) -> número
        mapa = {'Janeiro':1,'Fevereiro':2,'Março':3,'Abril':4,'Maio':5,
                'Junho':6,'Julho':7,'Agosto':8,'Setembro':9,
                'Outubro':10,'Novembro':11,'Dezembro':12}
        df_exp["mes_num"] = df_exp["Mês"].str.split(". ").str[0].map(mapa)
        df_exp["ano_mes"] = pd.to_datetime(dict(year=df_exp["Ano"],
                                               month=df_exp["mes_num"],
                                               day=1)).dt.to_period("M")
        merge = (serie.merge(df_exp[["ano_mes","Valor US$ FOB"]],
                             left_on=col_data, right_on="ano_mes", how="left"))
        merge["% FOB perdido"] = (merge["Cancelamentos"] * custo_teu) / merge["Valor US$ FOB"] * 100
        st.subheader("Impacto % sobre o FOB exportado")
        st.dataframe(merge[["ano_mes","% FOB perdido"]].round(4), use_container_width=True)
