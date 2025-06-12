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
from datetime import datetime

# ——— Tema unificado para gráficos ———
def theme_fig(fig, altura=450):
    fig.update_layout(
        height=altura,
        margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12, color='#E0E0E0'),
        legend=dict(yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ——— Gráfico de Top 10 Navios ———
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
    return theme_fig(fig, altura=450)

# ——— Configuração da página e CSS ———
st.set_page_config(page_title="🚢 Dashboard de Cancelamentos", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #121212; color: #E0E0E0; }
.dashboard-card { background: rgba(255,255,255,0.05); padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; }
h1, h2, h3, h4 { text-align: center; }
[data-testid="stColumns"] > div { padding: 0 1rem; }
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
      - THC: R$1.200,00 / TEU  
      - Armazenagem: R$575,00 / TEU / dia  
      - Despachante: R$950,00  
      - Scanner: R$95,00 / contêiner  
      Câmbio: R$5,10 / US$1
    """)

# ——— Upload de arquivo ———
uploaded = st.file_uploader("📁 Faça upload do arquivo Excel", type="xlsx")
if not uploaded:
    st.stop()

# Leitura dos dados
df = pd.read_excel(uploaded_file)

# Identificação automática de colunas
col_navio_raw     = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None
col_status        = 'Situação' if 'Situação' in df.columns else None
col_data          = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_conteineres   = 'Movs' if 'Movs' in df.columns else None
col_armador       = 'Armador' if 'Armador' in df.columns else None
col_rota          = 'De / Para' if 'De / Para' in df.columns else None
col_tipo_navio    = 'Tipo' if 'Tipo' in df.columns else None

# Filtrar cancelamentos
if col_status:
    df[col_status] = df[col_status].astype(str).str.strip().str.lower()
    cancel_vals = ['cancelado','cancelada','rejeitado','rej.','canceled']
    df_cancel = df[df[col_status].isin(cancel_vals)].copy()
else:
    df_cancel = df.copy()

# Converter colunas numéricas e datas
if col_conteineres:
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce')

# ——— Ajuste mínimo para Navio ———
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

# Preparar análise temporal mensal
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

# Resumo na Sidebar
with st.sidebar:
    st.markdown("### 📊 Resumo dos Resultados")
    total_cancel = len(df_cancel)
    navio_mais = contagem_navios.iloc[0] if not contagem_navios.empty else {'Navio':'—','QuantidadeCancelamentos':0}
    st.markdown(f"- **Total de cancelamentos:** {total_cancel:,}")
    st.markdown(f"- **Navio mais cancelado:** {navio_mais['Navio']} ({navio_mais['QuantidadeCancelamentos']} vezes)")
    if not contagem_mensal.empty:
        mes_pico = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        st.markdown(f"- **Mês com mais cancelamentos:** {mes_pico['Y-M'].strftime('%Y-%m')} ({int(mes_pico['Cancelamentos'])} cancel.)")

# Abas principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Visão Geral",
    "🚢 Análise de Navios",
    "📅 Análise Temporal",
    "🌍 Análise de Rotas",
    "📊 Análises Adicionais",
    "🔍 Análises Avançadas"
])

with tab1:
    st.header("📊 Visão Geral dos Cancelamentos")

    # Seletores de dimensão
    cx, cy = st.columns(2)
    with cx:
        dimensao_x = st.selectbox("Selecione a dimensão para o eixo X",
                                  ["Mês", "Navio", "Armador", "Rota", "Tipo de Navio"])
    with cy:
        dimensao_y = st.selectbox("Selecione a dimensão para o eixo Y",
                                  ["Quantidade de Cancelamentos", "Custo Total", "TEUs", "Tempo de Permanência"])

    # Métricas principais
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total de Registros", f"{len(df):,}", delta=f"{len(df_cancel):,} cancelamentos")
    with m2:
        taxa = (len(df_cancel)/len(df)*100) if len(df)>0 else 0
        st.metric("Taxa de Cancelamento", f"{taxa:.1f}%", delta=f"{taxa:.1f}% do total")
    with m3:
        media_dia = (len(df_cancel)/30) if len(df_cancel)>0 else 0
        st.metric("Média Diária", f"{media_dia:.1f}", delta="cancelamentos por dia")

    # Gráfico de cruzamento
    if dimensao_x and dimensao_y:
        try:
            if dimensao_x == "Mês":
                dados_x = df_cancel_valid['Y-M'].astype(str)
            elif dimensao_x == "Navio":
                dados_x = df_cancel['Navio']
            elif dimensao_x == "Armador":
                dados_x = df_cancel[col_armador] if col_armador else None
            elif dimensao_x == "Rota":
                dados_x = df_cancel[col_rota]
            elif dimensao_x == "Tipo de Navio":
                dados_x = df_cancel[col_tipo_navio]

            if dados_x is not None:
                if dimensao_y == "Quantidade de Cancelamentos":
                    y_vals = df_cancel.groupby(dados_x).size()
                elif dimensao_y == "Custo Total":
                    y_vals = df_cancel.groupby(dados_x)['CUSTO_TOTAL'].sum()
                elif dimensao_y == "TEUs":
                    y_vals = df_cancel.groupby(dados_x)[col_conteineres].sum()
                elif dimensao_y == "Tempo de Permanência":
                    y_vals = df_cancel.groupby(dados_x)['Tempo_Permanencia'].mean()

                df_graf = pd.DataFrame({
                    dimensao_x: dados_x.unique(),
                    dimensao_y: y_vals.values
                }).sort_values(by=dimensao_y, ascending=False)

                fig = px.bar(df_graf, x=dimensao_x, y=dimensao_y,
                             title=f"{dimensao_y} por {dimensao_x}",
                             color=dimensao_y, color_continuous_scale='Viridis')
                st.plotly_chart(ajustar_layout_grafico(fig, altura=500), use_container_width=True)
            else:
                st.warning(f"Não há dados para {dimensao_x}")
        except Exception as e:
            st.error(f"Erro: {e}")

    # Pizza Cancelados vs Não Cancelados
    fig_pie = px.pie(
        values=[len(df_cancel), len(df) - len(df_cancel)],
        names=['Cancelados', 'Não Cancelados'],
        title='Distribuição de Cancelamentos',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(ajustar_layout_grafico(fig_pie, altura=400), use_container_width=True)

    st.subheader("📋 Primeiros Registros de Cancelamento")
    st.dataframe(df_cancel.head(), hide_index=True, use_container_width=True)

# ——— Aba 2: Navios ———
with t2:
    st.header("🚢 Top 10 Navios")
    if contagem_navios['QuantidadeCancelamentos'].nunique() == 1:
        st.info("Todos os navios tiveram exatamente 1 cancelamento.")
        st.dataframe(contagem_navios, hide_index=True, use_container_width=True)
    else:
        g1, g2 = st.columns([1.3,1], gap="large")
        with g1:
            st.subheader("🏆 Ranking")
            st.plotly_chart(grafico_top_navios(df_cancel, 'Navio'), use_container_width=True)
        with g2:
            st.subheader("📋 Detalhe")
            st.dataframe(
                contagem_navios.head(10),
                hide_index=True,
                use_container_width=True,
                column_config={"QuantidadeCancelamentos": st.column_config.NumberColumn(format="%d")}
            )
        # Evolução do líder
        lider = contagem_navios.iloc[0]['Navio']
        df_l = df_cancel[df_cancel['Navio'] == lider].copy()
        if col_data:
            df_l['Mes'] = df_l[col_data].dt.to_period('M').astype(str)
            if df_l['Mes'].nunique() > 1:
                st.markdown(f"### 📈 Evolução mensal – {lider}")
                evo = (
                    df_l['Mes']
                    .value_counts()
                    .sort_index()
                    .rename_axis('Mes')
                    .reset_index(name='Cancelamentos')
                )
                fig_evo = px.line(evo, x='Mes', y='Cancelamentos', markers=True)
                st.plotly_chart(theme_fig(fig_evo, altura=350), use_container_width=True)

# ——— Aba 3: Temporal ———
with t3:
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
        fig = px.line(cont_mensal, x='Mes', y='Cancelamentos', markers=True,
                      title='Evolução Mensal de Cancelamentos')
        st.plotly_chart(theme_fig(fig), use_container_width=True)

# ——— Aba 4: Rotas ———
with t4:
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
            fig = px.bar(rot.head(5), x='Rota', y='Cancelamentos',
                         title='Top 5 Rotas', color='Cancelamentos')
            st.plotly_chart(theme_fig(fig), use_container_width=True)
    else:
        st.warning("Coluna de rotas não encontrada.")

# ——— Aba 5: Análises Adicionais ———
with t5:
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
                             title='Cancelamentos por Tipo', color_discrete_sequence=px.colors.qualitative.Set3)
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
                fig = px.histogram(df_cancel, x=col_conteineres,
                                   title='Distribuição de TEUs', nbins=20)
                st.plotly_chart(theme_fig(fig), use_container_width=True)
        else:
            st.warning("Coluna 'Movs' não encontrada.")

    with sub3:
        st.subheader("Top Armadores")
        if col_armador:
            df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip().replace({'':'Não Informado','nan':'Não Informado','None':'Não Informado'})
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

# ——— Aba 6: Custos ———
with t6:
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
        m1, m2, m3 = st.columns(3, gap="large")
        with m1:
            st.metric("Total Perdido", f"R$ {df_c['CUSTO_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with m2:
            st.metric("Médio por Cancel.", f"R$ {df_c['CUSTO_TOTAL'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with m3:
            st.metric("TEUs Afetados", f"{df_c[col_conteineres].sum():,.0f}".replace(",", "."))

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
        comp = (
            df_c[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]]
            .sum()
            .rename(index={
                "C_TEUS":"THC (R$/TEU)",
                "C_OPER":"Taxa Terminal",
                "C_DOC":"Despachante",
                "C_ARM":"Armazenagem (2 dias)",
                "C_INSP":"Scanner"
            })
            .to_frame("Valor")
            .reset_index()
            .rename(columns={"index":"Tipo de Custo"})
        )
        c1, c2 = st.columns([1.5,1], gap="large")
        with c1:
            st.subheader("Componentes de Custo")
            st.dataframe(comp, hide_index=True, use_container_width=True)
        with c2:
            fig = px.pie(comp, values="Valor", names="Tipo de Custo", title="Distribuição de Componentes")
            st.plotly_chart(theme_fig(fig, altura=350), use_container_width=True)

    else:
        st.warning("Coluna 'Movs' não encontrada; não foi possível calcular custos.")
