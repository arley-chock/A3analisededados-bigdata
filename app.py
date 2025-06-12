"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este notebook contém um trabalho da faculdade feito por:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana (1272221567)
- Tauan Santos Santana (12722216126)

O objetivo deste trabalho é analisar os levantamentos em formato Excel dos portos sobre navios cancelados.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def ajustar_layout_grafico(fig, altura=500):
    fig.update_layout(
        height=altura,
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

# Configuração da página
st.set_page_config(
    page_title="Análise de Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Base Melhorado ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem; max-width: 1400px; }
    .card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    .header { text-align: center; margin-bottom: 2rem; }
    .header h1 { margin: 0; font-size: 2.5rem; }
    .header p { font-size: 1.1rem; color: #ddd; }
    .sidebar .stExpanderHeader {
        background: rgba(255,255,255,0.10);
        border-radius: 5px;
        margin-bottom: 0.5rem;
    }
    .sidebar .stExpanderContent { padding-left: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
with st.container():
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/color/96/000000/cruise-ship.png", width=80)
    st.markdown("## 🚢 Análise de Cancelamentos de Navios", unsafe_allow_html=True)
    st.markdown("<p>Dashboard interativo para monitorar cancelamentos, custos e tendências.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Sidebar com Upload, Filtros e Informações ---
with st.sidebar:
    with st.expander("📁 Upload e Filtros", expanded=True):
        uploaded_file     = st.file_uploader("Faça o upload do Excel", type=["xlsx"])
        termo_pesquisa    = st.text_input("🔍 Pesquisar por navio, armador ou rota")
        modelo_selecionado = st.selectbox(
            "📋 Modelo de Relatório",
            ["Análise Completa","Análise de Custos","Análise por Armador","Análise Temporal"]
        )
        if st.button("Aplicar Modelo"):
            st.session_state.termo = termo_pesquisa
            st.session_state.modelo = modelo_selecionado

    with st.expander("📋 Sobre o Projeto", expanded=False):
        st.markdown("""
        **Integrantes:**  
        - Arley do Nascimento Vinagre  
        - Vinicius Santana  
        - Tauan Santos Santana  

        _Objetivo_: Analisar levantamentos em Excel de portos sobre navios cancelados.
        """)

    with st.expander("💰 Referências de Custos", expanded=False):
        st.markdown("""
        - **THC:** R$ 1.200,00 / TEU  
        - **Armazenagem:** R$ 575,00 / TEU / dia × 2 dias  
        - **Despachante:** R$ 950,00  
        - **Scanner:** R$ 95,00 / contêiner  
        - **Câmbio:** R$ 5,10 / US$
        """)

# --- Carregamento e Processamento dos Dados ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Detectar colunas
    col_navio       = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None
    col_status      = 'Situação' if 'Situação' in df.columns else None
    col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
    col_motivo      = 'MotivoCancelamento' if 'MotivoCancelamento' in df.columns else None
    col_rota        = 'De / Para' if 'De / Para' in df.columns else None
    col_tipo_navio  = 'Tipo' if 'Tipo' in df.columns else None
    col_conteineres = 'Movs' if 'Movs' in df.columns else None
    col_armador     = 'Armador' if 'Armador' in df.columns else None

    # Filtrar cancelamentos
    valores_cancelados = ['cancelado','cancelada','rejeitado','rej.','canceled']
    if col_status:
        df[col_status] = df[col_status].astype(str).str.strip().str.lower()
        df_cancel = df[df[col_status].isin(valores_cancelados)].copy()
    else:
        df_cancel = pd.DataFrame(columns=df.columns)

    # Aplicar pesquisa por termo (se fornecido)
    termo = st.session_state.get('termo', '').strip().lower()
    if termo:
        mask_navio   = col_navio and df_cancel[col_navio].str.lower().str.contains(termo)
        mask_armador = col_armador and df_cancel[col_armador].str.lower().str.contains(termo)
        mask_rota    = col_rota and df_cancel[col_rota].str.lower().str.contains(termo)
        df_cancel = df_cancel.loc[
            mask_navio.fillna(False) |
            mask_armador.fillna(False) |
            mask_rota.fillna(False)
        ]

    # Conversões
    if col_data:
        df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
    if col_conteineres:
        df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)

    # Resumo na sidebar
    with st.sidebar:
        total_cancel = len(df_cancel)
        navio_mais   = df_cancel[col_navio].value_counts().idxmax() if col_navio and total_cancel>0 else '—'
        qt_mais      = df_cancel[col_navio].value_counts().max() if col_navio and total_cancel>0 else 0
        st.markdown("### 📊 Resumo dos Resultados")
        st.markdown(f"- **Total de cancelamentos:** {total_cancel:,}")
        st.markdown(f"- **Navio mais cancelado:** {navio_mais} ({qt_mais} vezes)")
        if col_data and not df_cancel[col_data].dropna().empty:
            df_cancel['Y-M'] = df_cancel[col_data].dt.to_period('M').astype(str)
            mes_top = df_cancel['Y-M'].value_counts().idxmax()
            qt_mes  = df_cancel['Y-M'].value_counts().max()
            st.markdown(f"- **Mês com mais cancelamentos:** {mes_top} ({qt_mes} cancelamentos)")

    # Preparar contagens e series temporais
    contagem_navios = df_cancel[col_navio].value_counts().reset_index()
    contagem_navios.columns = ['Navio','QuantidadeCancelamentos']

    df_temp = df_cancel.dropna(subset=[col_data]) if col_data else df_cancel.copy()
    if col_data:
        df_temp['Y-M'] = df_temp[col_data].dt.to_period('M').astype(str)
        contagem_mensal = df_temp.groupby('Y-M').size().reset_index(name='Cancelamentos')
        contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
        contagem_mensal = contagem_mensal.sort_values('Y-M')
    else:
        contagem_mensal = pd.DataFrame(columns=['Y-M','Cancelamentos'])

    # --- Abas Principais ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Visão Geral",
        "🚢 Análise de Navios",
        "📅 Análise Temporal",
        "🌍 Análise de Rotas",
        "🏷️ Motivos de Cancelamento",
        "💰 Análises de Custos"
    ])

    # Visão Geral
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Distribuição de Cancelamentos")
        fig = px.pie(
            names=['Cancelados','Não Cancelados'],
            values=[len(df_cancel), len(df)-len(df_cancel)],
            title="Cancelados vs Não Cancelados",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig = ajustar_layout_grafico(fig, altura=400)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Primeiros Registros de Cancelamento")
        st.dataframe(df_cancel.head(), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Navios
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🚢 Top 10 Navios com Mais Cancelamentos")
        if contagem_navios['QuantidadeCancelamentos'].nunique() == 1:
            st.info("Todos os navios cancelados registraram apenas 1 ocorrência.")
        st.dataframe(contagem_navios.head(10), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise Temporal
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📅 Evolução Mensal de Cancelamentos")
        if not contagem_mensal.empty:
            st.dataframe(contagem_mensal.rename(columns={'Y-M':'Mês'}), use_container_width=True, hide_index=True)
            fig = px.line(contagem_mensal, x='Y-M', y='Cancelamentos', title="Cancelamentos por Mês", markers=True)
            fig.update_layout(xaxis_title="Mês", yaxis_title="Quantidade")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sem dados de data para análise temporal.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Rotas
    with tab4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🗺️ Top 10 Rotas com Mais Cancelamentos")
        if col_rota:
            contagem_rotas = df_cancel[col_rota].value_counts().reset_index()
            contagem_rotas.columns = ['Rota','Cancelamentos']
            st.dataframe(contagem_rotas.head(10), use_container_width=True, hide_index=True)
            fig = px.bar(contagem_rotas.head(5), x='Rota', y='Cancelamentos', title="Top 5 Rotas", color='Cancelamentos')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Coluna de rotas não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Motivos de Cancelamento (adicionado)
    with tab5:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🏷️ Distribuição de Motivos de Cancelamento")
        if col_motivo:
            df_cancel[col_motivo] = df_cancel[col_motivo].astype(str).str.strip().replace('', 'Não Informado')
            contagem_motivos = df_cancel[col_motivo].value_counts().reset_index()
            contagem_motivos.columns = ['Motivo','Quantidade']
            st.dataframe(contagem_motivos, use_container_width=True, hide_index=True)
            fig = px.pie(contagem_motivos.head(10), names='Motivo', values='Quantidade',
                         title="Top 10 Motivos", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Coluna de motivo de cancelamento não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Custos (parte mantida sem alteração de casas decimais)
    with tab6:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("💰 Análise de Custos de Cancelamento")

        # Parâmetros de custos
        CUSTOS = {
            "TEU":               1200.0,
            "OPERACAO_PORTO":    1150.0,
            "DOCUMENTACAO":       950.0,
            "ARMAZENAGEM_DIA":    575.0,
            "ARMAZENAGEM_DIAS":      2,
            "INSPECAO":            95.0
        }

        def calcular_custos(df: pd.DataFrame, coluna_teu: str) -> pd.DataFrame:
            df = df.copy()
            df[coluna_teu] = pd.to_numeric(df[coluna_teu], errors="coerce").fillna(0)
            df["C_TEUS"] = df[coluna_teu] * CUSTOS["TEU"]
            df["C_OPER"] = CUSTOS["OPERACAO_PORTO"]
            df["C_DOC"]  = CUSTOS["DOCUMENTACAO"]
            df["C_ARM"]  = df[coluna_teu] * CUSTOS["ARMAZENAGEM_DIA"] * CUSTOS["ARMAZENAGEM_DIAS"]
            df["C_INSP"]= CUSTOS["INSPECAO"]
            df["CUSTO_TOTAL"] = df[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
            return df

        if col_conteineres:
            df_cancel = calcular_custos(df_cancel, col_conteineres)

            c1, c2, c3 = st.columns(3)
            c1.metric("Custo Total Perdido", 
                      f"R$ {df_cancel['CUSTO_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            c2.metric("Custo Médio por Cancelamento",
                      f"R$ {df_cancel['CUSTO_TOTAL'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            c3.metric("TEUs Afetados",
                      f"{int(df_cancel[col_conteineres].sum()):,}".replace(",", "."))

            st.plotly_chart(
                px.box(df_cancel, y="CUSTO_TOTAL",
                       title="Distribuição do Custo por Cancelamento",
                       labels={"CUSTO_TOTAL": "Custo Total (R$)"}),
                use_container_width=True
            )

            if col_data:
                df_cancel["Mes"] = pd.to_datetime(df_cancel[col_data]).dt.to_period("M")
                custos_mensais = (
                    df_cancel.groupby("Mes")["CUSTO_TOTAL"]
                    .sum().reset_index()
                    .assign(Mes=lambda d: d["Mes"].astype(str))
                )
                custos_mensais["CUSTO_TOTAL"] = custos_mensais["CUSTO_TOTAL"].apply(lambda x: float(f"{x:.2f}"))
                st.plotly_chart(
                    px.line(custos_mensais, x="Mes", y="CUSTO_TOTAL", title="Evolução Mensal dos Custos", markers=True,
                            labels={"CUSTO_TOTAL":"Custo Total (R$)"}),
                    use_container_width=True
                )

            # Detalhamento dos componentes
            componentes = (
                df_cancel[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]]
                .sum()
                .rename(index={
                    "C_TEUS":"THC (Terminal Handling Charge)",
                    "C_OPER":"Taxa de Cancelamento",
                    "C_DOC":"Honorários de Despacho",
                    "C_ARM":"Armazenagem (2 dias)",
                    "C_INSP":"Scanner/Fitossanitária"
                })
                .reset_index()
                .rename(columns={"index":"Tipo de Custo", 0:"Valor Total (BRL)"})
            )
            comp_fmt = componentes.copy()
            comp_fmt["Valor Total (BRL)"] = comp_fmt["Valor Total (BRL)"].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            cola, colb = st.columns(2)
            cola.dataframe(comp_fmt, use_container_width=True, hide_index=True)
            colb.plotly_chart(
                px.pie(componentes, values="Valor Total (BRL)", names="Tipo de Custo", title="Distribuição dos Custos"),
                use_container_width=True
            )

            # Custos por armador
            if col_armador:
                st.subheader("Análise de Custos por Armador")
                custos_armador = (
                    df_cancel.groupby(col_armador)["CUSTO_TOTAL"]
                    .agg(['sum','mean','count'])
                    .reset_index()
                    .rename(columns={'sum':'Custo Total','mean':'Custo Médio','count':'Quantidade'})
                    .sort_values('Custo Total', ascending=False)
                )
                custos_armador['Custo Total'] = custos_armador['Custo Total'].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                custos_armador['Custo Médio'] = custos_armador['Custo Médio'].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                ca, cb = st.columns(2)
                ca.dataframe(custos_armador.head(10), use_container_width=True, hide_index=True)

                df_plot = custos_armador.head(10).copy()
                df_plot['Custo Total'] = df_plot['Custo Total'].str.replace('R$ ','').str.replace('.','').str.replace(',','.').astype(float)
                fig = px.bar(df_plot, x=col_armador, y='Custo Total', title='Top 10 Armadores por Custo Total')
                cb.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("⚠️ Coluna de contêineres não encontrada; não é possível calcular os custos.")

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.warning("⚠️ Faça o upload do arquivo Excel para iniciar a análise.")
