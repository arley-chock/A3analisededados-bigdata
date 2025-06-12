"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este aplicativo Streamlit foi desenvolvido por:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana (1272221567)
- Tauan Santos Santana (12722216126)

Objetivo: analisar relatórios Excel de portos sobre navios cancelados.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ——— Funções utilitárias ———

def theme_fig(fig, altura=450):
    fig.update_layout(
        height=altura,
        margin=dict(l=40, r=40, t=60, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14, color='#E0E0E0'),
        legend=dict(yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_traces(marker_line_width=0)
    return fig

def grafico_top_navios(df_cancel, col_navio):
    cont = (
        df_cancel[col_navio]
        .value_counts()
        .rename_axis(col_navio)
        .reset_index(name='Cancelamentos')
    )
    fig = px.bar(
        cont.head(10),
        y=col_navio, x='Cancelamentos',
        orientation='h',
        title='Top 10 navios mais cancelados',
        color='Cancelamentos',
        color_continuous_scale='Blues'
    )
    fig.update_layout(yaxis_title=None, xaxis_title='Cancelamentos')
    return theme_fig(fig, altura=500)

# ——— Configuração da página e CSS ———

st.set_page_config(page_title="🚢 Dashboard de Cancelamentos", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #121212; color: #E0E0E0; }
.stMarkdown p, .dashboard-card p { font-size: 16px; line-height: 1.6; }
.dashboard-card { background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; }
h1, h2, h3, h4 { text-align: center; }
.js-plotly-plot { margin-bottom: 3rem !important; }
section.main > div.block-container { padding-top:2rem; padding-bottom:2rem; }
[data-testid="stColumns"] > div { margin-bottom: 2rem; }
.stTextInput, .stFileUploader, .stSelectbox, .stButton { margin-bottom:1.5rem; }
</style>
""", unsafe_allow_html=True)

# ——— Cabeçalho ———

st.markdown("""
<div class="dashboard-card">
    <h1>🚢 Análise de Cancelamentos de Navios</h1>
    <p>Insights interativos sobre navios cancelados em portos</p>
</div>
""", unsafe_allow_html=True)

# ——— Sidebar ———

with st.sidebar:
    st.markdown("### 📋 Sobre o Projeto")
    st.write("""
      Projeto acadêmico de análise de cancelamentos de navios.
      - Arley do Nascimento Vinagre  
      - Vinicius Santana  
      - Tauan Santos Santana
    """)
    st.markdown("---")
    st.markdown("### 🔍 Filtrar")
    termo = st.text_input("Pesquisar por navio, armador ou rota")
    st.markdown("---")
    st.markdown("### 💰 Referências de Custos")
    st.write("""
      - THC: R$ 1.200,00 / TEU  
      - Armazenagem: R$ 575,00 / TEU / dia  
      - Despachante: R$ 950,00  
      - Scanner: R$ 95,00 / contêiner  
      Câmbio: R$ 5,10 / US$ 1
    """)

# ——— Upload e leitura de arquivo ———

uploaded = st.file_uploader("📁 Faça upload do arquivo Excel", type="xlsx")
if not uploaded:
    st.stop()

# Leitura dos dados
df = pd.read_excel(uploaded_file)

# ——— Detectar colunas automaticamente ———
col_status      = 'Situação' if 'Situação' in df.columns else None
col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_conteineres = 'Movs' if 'Movs' in df.columns else None
col_armador     = 'Armador' if 'Armador' in df.columns else None
col_rota        = 'De / Para' if 'De / Para' in df.columns else None
col_tipo_navio  = 'Tipo' if 'Tipo' in df.columns else None
col_navio_raw   = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None

# ——— Filtrar somente cancelamentos ———
if col_status:
    df[col_status] = df[col_status].astype(str).str.strip().str.lower()
    vals = ['cancelado','cancelada','rejeitado','rej.','canceled']
    df_cancel = df[df[col_status].isin(vals)].copy()
else:
    df_cancel = df.copy()

# ——— Converter tipos ———
if col_conteineres:
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce')

# ——— Extrair nome limpo do Navio ———

NAVIO_COL = 'Navio / Viagem.1' if 'Navio / Viagem.1' in df_cancel.columns else col_navio_raw
df_cancel['Navio'] = (
    df_cancel[NAVIO_COL]
    .astype(str)
    .str.strip()
    .str.title()
)
contagem_navios = (
    df_cancel['Navio']
    .value_counts()
    .rename_axis('Navio')
    .reset_index(name='QuantidadeCancelamentos')
)

# ——— Série temporal mensal ———
if col_data:
    df_cancel_valid = df_cancel.dropna(subset=[col_data]).copy()
    df_cancel_valid['Y-M'] = df_cancel_valid[col_data].dt.to_period('M').astype(str)
    contagem_mensal = (
        df_cancel_valid.groupby('Y-M')
        .size()
        .reset_index(name='Cancelamentos')
    )
    contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
    contagem_mensal = contagem_mensal.sort_values('Y-M')
else:
    contagem_mensal = pd.DataFrame(columns=['Y-M','Cancelamentos'])

# ——— Resumo rápido na sidebar ———
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Resumo")
    st.write(f"- **Cancelamentos totais:** {len(df_cancel):,}")
    if not contagem_navios.empty:
        top = contagem_navios.iloc[0]
        st.write(f"- **Navio mais afetado:** {top['Navio']} ({top['QuantidadeCancelamentos']}x)")
    if not cont_mensal.empty:
        pico = cont_mensal.loc[cont_mensal['Cancelamentos'].idxmax()]
        st.write(f"- **Mês de pico:** {pico['Mes'].strftime('%Y-%m')} ({int(pico['Cancelamentos'])} cancel.)")

# ——— Abas principais ———
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📈 Visão Geral",
    "🚢 Navios",
    "📅 Temporal",
    "🌍 Rotas",
    "📊 Adicionais",
    "💰 Custos"
])

# ——— Aba 1: Visão Geral ———

with tab1:
    st.header("📈 Visão Geral dos Cancelamentos")
    # Métricas principais
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.metric("Total de Registros", f"{len(df):,}", delta=f"{len(df_cancel):,} cancel.")
    with c2:
        taxa = (len(df_cancel)/len(df)*100) if len(df)>0 else 0
        st.metric("Taxa de Cancelamento", f"{taxa:.1f}%", delta=f"{taxa:.1f}%")
    with c3:
        media = (len(df_cancel)/30) if len(df_cancel)>0 else 0
        st.metric("Média diária", f"{media:.1f}", delta="cancel./dia")

    # Pizza Cancelados vs Não
    fig_pie = px.pie(
        values=[len(df_cancel), len(df) - len(df_cancel)],
        names=['Cancelados', 'Não Cancelados'],
        title='Distribuição de Cancelamentos',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(theme_fig(fig_pie, altura=400), use_container_width=True)

    st.subheader("📋 Primeiros Registros de Cancelamento")
    st.dataframe(df_cancel.head(), hide_index=True, use_container_width=True)

with tab2:
    st.header("🚢 Top 10 Navios Mais Cancelados")
    if contagem_navios['QuantidadeCancelamentos'].nunique() == 1:
        st.info("Todos os navios tiveram exatamente 1 cancelamento.")
        st.dataframe(contagem_navios, hide_index=True, use_container_width=True)
    else:
        g1, g2 = st.columns([1.3,1], gap="large")
        with g1:
            st.subheader("🏆 Ranking")
            st.plotly_chart(grafico_top_navios(df_cancel, 'Navio'), use_container_width=True)
        with g2:
            st.subheader("📋 Detalhe Top 10")
            st.dataframe(
                contagem_navios.head(10),
                hide_index=True,
                use_container_width=True,
                column_config={"QuantidadeCancelamentos": st.column_config.NumberColumn(format="%,d")}
            )
        lider = contagem_navios.iloc[0]['Navio']
        df_l = df_cancel[df_cancel['Navio'] == lider].copy()
        if col_data:
            df_l['Mes'] = df_l[col_data].dt.to_period('M').astype(str)
            if df_l['Mes'].nunique() > 1:
                st.markdown(f"### 📈 Evolução Mensal – {lider}")
                evo = (
                    df_l['Mes']
                    .value_counts()
                    .sort_index()
                    .rename_axis('Mes')
                    .reset_index(name='Cancelamentos')
                )
                fig_evo = px.line(evo, x='Mes', y='Cancelamentos', markers=True)
                st.plotly_chart(theme_fig(fig_evo, altura=350), use_container_width=True)

with tab3:
    st.header("📅 Análise Temporal")
    m1, m2 = st.columns(2, gap="large")
    with m1:
        st.subheader("Cancelamentos por Mês")
        st.dataframe(
            cont_mensal.assign(Mes=cont_mensal['Mes'].dt.strftime('%Y-%m')),
            hide_index=True,
            use_container_width=True
        )
    with m2:
        fig = px.line(cont_mensal, x='Mes', y='Cancelamentos', markers=True, title='Evolução Mensal')
        st.plotly_chart(theme_fig(fig), use_container_width=True)

with tab4:
    st.header("🌍 Análise de Rotas")
    if col_rota:
        rot = (
            df_cancel[col_rota]
            .value_counts()
            .rename_axis('Rota')
            .reset_index(name='Cancelamentos')
        )
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.subheader("Top 10 Rotas")
            st.dataframe(rot.head(10), hide_index=True, use_container_width=True)
        with r2:
            fig = px.bar(rot.head(5), x='Rota', y='Cancelamentos', title='Top 5 Rotas', color='Cancelamentos')
            st.plotly_chart(theme_fig(fig), use_container_width=True)
    else:
        st.warning("Coluna de rotas não encontrada.")

with tab5:
    st.header("📊 Análises Adicionais")
    sub1, sub2, sub3 = st.tabs(["Tipo de Navio","Contêineres","Armadores"])

    with sub1:
        st.subheader("Distribuição por Tipo de Navio")
        if col_tipo_navio:
            df_cancel[col_tipo_navio] = df_cancel[col_tipo_navio].astype(str).str.strip().str.capitalize()
            ct = (
                df_cancel[col_tipo_navio]
                .value_counts()
                .rename_axis('TipoNavio')
                .reset_index(name='Cancelamentos')
            )
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.dataframe(ct, hide_index=True, use_container_width=True)
            with c2:
                fig = px.pie(ct, values='Cancelamentos', names='TipoNavio',
                             title='Cancelamentos por Tipo',
                             color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(theme_fig(fig, altura=350), use_container_width=True)
        else:
            st.warning("Coluna 'Tipo' não encontrada.")

    with sub2:
        st.subheader("Estatísticas de Contêineres")
        if col_conteineres:
            stats = df_cancel[col_conteineres].describe().to_frame().reset_index()
            h1, h2 = st.columns(2, gap="large")
            with h1:
                st.dataframe(stats, hide_index=True, use_container_width=True)
            with h2:
                fig = px.histogram(df_cancel, x=col_conteineres, title='Distribuição de TEUs', nbins=20)
                st.plotly_chart(theme_fig(fig), use_container_width=True)
        else:
            st.warning("Coluna 'Movs' não encontrada.")

    with sub3:
        st.subheader("Top Armadores")
        if col_armador:
            df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip() \
                                     .replace({'':'Não Informado','nan':'Não Informado','None':'Não Informado'})
            ca = (
                df_cancel[col_armador]
                .value_counts()
                .rename_axis('Armador')
                .reset_index(name='Cancelamentos')
            )
            a1, a2 = st.columns(2, gap="large")
            with a1:
                st.dataframe(ca.head(10), hide_index=True, use_container_width=True)
            with a2:
                fig = px.bar(ca.head(5), x='Armador', y='Cancelamentos',
                             title='Top 5 Armadores', color='Cancelamentos')
                st.plotly_chart(theme_fig(fig), use_container_width=True)
        else:
            st.warning("Coluna 'Armador' não encontrada.")

with tab6:
    st.header("💰 Análise de Custos")
    C = {"TEU":1200.0,"OPER":1150.0,"DOC":950.0,"ARM_DIA":575.0,"ARM_DIAS":2,"INSP":95.0}
    def calc_custos(df, col_t):
        df = df.copy()
        df[col_t] = pd.to_numeric(df[col_t], errors='coerce').fillna(0)
        df["C_TEUS"] = df[col_t]*C["TEU"]
        df["C_OPER"] = C["OPER"]
        df["C_DOC"]  = C["DOC"]
        df["C_ARM"]  = df[col_t]*C["ARM_DIA"]*C["ARM_DIAS"]
        df["C_INSP"]= C["INSP"]
        df["CUSTO_TOTAL"] = df[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
        return df

    if col_conteineres:
        df_c = calc_custos(df_cancel, col_conteineres)

        # Métricas de custo
        m1, m2, m3 = st.columns(3, gap="large")
        with m1:
            st.metric("Total Perdido",
                      f"R$ {df_c['CUSTO_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with m2:
            st.metric("Médio por Cancel.",
                      f"R$ {df_c['CUSTO_TOTAL'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with m3:
            st.metric("TEUs Afetados",
                      f"{df_c[col_conteineres].sum():,.0f}".replace(",", "."))

        # Distribuição de custos
        fig = px.box(df_c, y="CUSTO_TOTAL", title="Distribuição de Custo por Cancelamento")
        st.plotly_chart(theme_fig(fig), use_container_width=True)

        # Evolução mensal de custos
        if col_data:
            df_c["Mes"] = df_c[col_data].dt.to_period("M").astype(str)
            cm = df_c.groupby("Mes")["CUSTO_TOTAL"].sum().reset_index()
            fig = px.line(cm, x="Mes", y="CUSTO_TOTAL", markers=True, title="Evolução Mensal de Custos")
            st.plotly_chart(theme_fig(fig), use_container_width=True)

        # Componentes de custo
        total_components = df_c[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum()
        total_components.index = [
            "THC (R$/TEU)",
            "Taxa Terminal",
            "Despachante",
            "Armazenagem (2 dias)",
            "Scanner"
        ]
        comp_numerical = total_components.reset_index()
        comp_numerical.columns = ["Tipo de Custo","Valor"]

        # Tabela formatada
        comp_display = comp_numerical.copy()
        comp_display["Valor"] = comp_display["Valor"]\
            .apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.subheader("Componentes de Custo")
        st.dataframe(comp_display, hide_index=True, use_container_width=True)

        # Gráfico de pizza
        fig = px.pie(
            comp_numerical,
            values="Valor",
            names="Tipo de Custo",
            title="Distribuição de Componentes"
        )
        st.plotly_chart(theme_fig(fig, altura=350), use_container_width=True)

    else:
        st.warning("Coluna 'Movs' não encontrada; não foi possível calcular custos.")
