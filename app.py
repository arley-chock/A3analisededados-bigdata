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

# ——— Novo: tema unificado para gráficos ———
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

# ——— Novo: função para criar o gráfico de Top 10 Navios ———
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

# Função original de layout de gráficos para uso geral
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

# Barra de Pesquisa e Modelos
with st.sidebar:
    st.markdown("### 🔍 Pesquisa e Modelos")
    termo_pesquisa = st.text_input("Pesquisar por navio, armador ou rota")
    st.markdown("### 📋 Modelos de Relatórios")
    modelo_selecionado = st.selectbox(
        "Selecione um modelo de relatório",
        ["Análise Completa", "Análise de Custos", "Análise por Armador", "Análise Temporal"]
    )
    if st.button("Aplicar Modelo"):
        st.session_state['modelo_atual'] = modelo_selecionado
        st.session_state['termo_pesquisa'] = termo_pesquisa

# CSS personalizado para layout e responsividade
st.markdown("""
    <style>
    .main { padding:2rem; max-width:1400px; margin:0 auto; }
    .js-plotly-plot { margin:1rem 0; padding:1rem; background:rgba(255,255,255,0.07); border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1); }
    .stContainer { margin:1rem 0; padding:1rem; }
    [data-testid="column"] { padding:0 1rem; }
    .stMetric { margin:1rem 0; }
    .stTabs [data-baseweb="tab-list"] { gap:1rem; margin-bottom:1.5rem; }
    .stTabs [data-baseweb="tab"] { padding:0.8rem 1.5rem; margin-right:0.5rem; }
    .dashboard-card { margin:1.5rem 0; padding:1.5rem; }
    @media (max-width:1200px) { .main { padding:1rem; } [data-testid="column"]{ padding:0 0.5rem; } }
    @media (max-width:768px) { .main { padding:0.5rem; } .stTabs [data-baseweb="tab"]{ padding:0.6rem 1rem; font-size:0.9rem; } }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("""
    <div class='dashboard-card' style='text-align:center;'>
        <h1>🚢 Análise de Cancelamentos de Navios</h1>
        <p style='color:#e0e0e0;'>Dashboard Interativo com insights sobre cancelamentos</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar sobre o projeto e referências de custos
with st.sidebar:
    st.markdown("""
        <div style='text-align:center;'>
            <img src='https://img.icons8.com/color/96/000000/cruise-ship.png' style='width:90px;'/><br>
            <h3>📋 Sobre o Projeto</h3>
            <p>Projeto acadêmico de análise de dados de cancelamentos.</p>
            <ul>
                <li>👤 Arley do Nascimento Vinagre</li>
                <li>👤 Vinicius Santana</li>
                <li>👤 Tauan Santos Santana</li>
            </ul>
        </div>
        <hr>
        <h3>💰 Referências de Custos</h3>
        <ul style='font-size:0.9rem;'>
            <li>THC: R$1.200,00/TEU</li>
            <li>Armazenagem: R$575,00/TEU/dia</li>
            <li>Despachante: R$950,00</li>
            <li>Scanner: R$95,00/contêiner</li>
        </ul>
        <p style='color:#4CAF50;'>Câmbio médio: R$5,10/US$1</p>
    """, unsafe_allow_html=True)

# Upload de arquivo
uploaded_file = st.file_uploader("📁 Faça o upload do arquivo Excel", type=["xlsx"])
if uploaded_file is None:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel para começar a análise.")
    st.stop()

if uploaded_file is not None:
    # Carregar dados
    df = pd.read_excel(uploaded_file)
    
    # Identificar colunas
    col_navio = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None
    col_status = 'Situação' if 'Situação' in df.columns else None
    col_data = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
    col_motivo = 'MotivoCancelamento' if 'MotivoCancelamento' in df.columns else None
    col_rota = 'De / Para' if 'De / Para' in df.columns else None
    col_tipo_navio = 'Tipo' if 'Tipo' in df.columns else None
    col_conteineres = 'Movs' if 'Movs' in df.columns else None
    col_armador = 'Armador' if 'Armador' in df.columns else None

    # Filtrar cancelamentos
    if col_status is not None:
        df[col_status] = df[col_status].astype(str).str.strip().str.lower()
        valores_cancelados = ['cancelado', 'cancelada', 'rejeitado', 'rej.', 'canceled']
        mask_cancel = df[col_status].isin(valores_cancelados)
        df_cancel = df.loc[mask_cancel].copy()

        # Converter colunas numéricas
        if col_conteineres is not None:
            df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
            df[col_conteineres] = pd.to_numeric(df[col_conteineres], errors='coerce').fillna(0)

        # Converter datas
        if col_data is not None:
            df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce')
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')

    # Preparar dados para o resumo
    contagem_navios = df_cancel[col_navio].value_counts().reset_index()
    contagem_navios.columns = ['Navio', 'QuantidadeCancelamentos']
    
    # Converter data e preparar análise temporal
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
    df_cancel['Ano'] = df_cancel[col_data].dt.year
    df_cancel['Mês'] = df_cancel[col_data].dt.month
    # Remover registros sem data válida antes de criar 'Y-M'
    df_cancel_valid = df_cancel.dropna(subset=[col_data]).copy()
    df_cancel_valid['Y-M'] = df_cancel_valid[col_data].dt.to_period('M').astype(str)
    contagem_mensal = df_cancel_valid.groupby('Y-M').size().reset_index(name='Cancelamentos')
    contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
    contagem_mensal = contagem_mensal.sort_values('Y-M')

    # Resumo final na sidebar
    with st.sidebar:
        st.markdown("### 📊 Resumo dos Resultados")
        
        # Definir max_mes antes de usar
        max_mes = None
        if not contagem_mensal.empty:
            max_mes = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        
        resumo_texto = f"""
            - **Total de cancelamentos:** {len(df_cancel):,}
            - **Navio mais cancelado:** {contagem_navios.iloc[0]['Navio']} ({contagem_navios.iloc[0]['QuantidadeCancelamentos']} vezes)
        """
        
        if max_mes is not None:
            resumo_texto += f"""
            - **Mês com mais cancelamentos:** {max_mes['Y-M']} ({int(max_mes['Cancelamentos'])} cancelamentos)
            """
        
        st.markdown(resumo_texto)

    # Criar abas para diferentes análises
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
        
        # Adicionar seletores para cruzamento de dados
        col1, col2 = st.columns(2)
        with col1:
            dimensao_x = st.selectbox(
                "Selecione a dimensão para o eixo X",
                ["Mês", "Navio", "Armador", "Rota", "Tipo de Navio"]
            )
        with col2:
            dimensao_y = st.selectbox(
                "Selecione a dimensão para o eixo Y",
                ["Quantidade de Cancelamentos", "Custo Total", "TEUs", "Tempo de Permanência"]
            )
        
        # Métricas principais com cards estilizados
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total de Registros",
                f"{len(df):,}",
                delta=f"{len(df_cancel):,} cancelamentos"
            )
        with col2:
            st.metric(
                "Taxa de Cancelamento",
                f"{(len(df_cancel)/len(df)*100):.1f}%",
                delta=f"{(len(df_cancel)/len(df)*100):.1f}% do total"
            )
        with col3:
            st.metric(
                "Média Diária",
                f"{(len(df_cancel)/30):.1f}",
                delta="cancelamentos por dia"
            )

        # Gráfico de cruzamento de dados
        if dimensao_x and dimensao_y:
            try:
                # Preparar dados para o gráfico
                if dimensao_x == "Mês":
                    dados_x = df_cancel_valid['Y-M'].astype(str)
                elif dimensao_x == "Navio":
                    dados_x = df_cancel[col_navio].astype(str)
                elif dimensao_x == "Armador":
                    dados_x = df_cancel[col_armador].astype(str) if col_armador else None
                elif dimensao_x == "Rota":
                    dados_x = df_cancel[col_rota].astype(str)
                elif dimensao_x == "Tipo de Navio":
                    dados_x = df_cancel[col_tipo_navio].astype(str)

                if dados_x is not None:
                    if dimensao_y == "Quantidade de Cancelamentos":
                        dados_y = df_cancel.groupby(dados_x).size()
                    elif dimensao_y == "Custo Total":
                        dados_y = df_cancel.groupby(dados_x)['CUSTO_TOTAL'].sum()
                    elif dimensao_y == "TEUs":
                        dados_y = df_cancel.groupby(dados_x)[col_conteineres].sum()
                    elif dimensao_y == "Tempo de Permanência":
                        dados_y = df_cancel.groupby(dados_x)['Tempo_Permanencia'].mean()

                    # Criar DataFrame para o gráfico
                    df_grafico = pd.DataFrame({
                        dimensao_x: dados_x.unique(),
                        dimensao_y: dados_y.values
                    })

                    # Ordenar por valores
                    df_grafico = df_grafico.sort_values(by=dimensao_y, ascending=False)

                    # Criar gráfico com layout ajustado
                    fig = px.bar(
                        df_grafico,
                        x=dimensao_x,
                        y=dimensao_y,
                        title=f"{dimensao_y} por {dimensao_x}",
                        color=dimensao_y,
                        color_continuous_scale='Viridis'
                    )
                    fig = ajustar_layout_grafico(fig, altura=500)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Não há dados disponíveis para a dimensão {dimensao_x}")
            except Exception as e:
                st.error(f"Erro ao criar gráfico: {str(e)}")
                st.info("Tente selecionar outras dimensões para análise")

        # Gráfico de pizza com Plotly
        fig = px.pie(
            values=[len(df_cancel), len(df) - len(df_cancel)],
            names=['Cancelados', 'Não Cancelados'],
            title='Distribuição de Cancelamentos',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig = ajustar_layout_grafico(fig, altura=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Primeiros Registros de Cancelamento")
    st.dataframe(df_cancel.head(), hide_index=True, use_container_width=True)

with tab2:
    st.header("🚢 Análise de Navios")
    if contagem_navios['QuantidadeCancelamentos'].nunique() == 1:
        st.info("Todos os navios cancelados tiveram apenas 1 ocorrência no período analisado.")
        st.dataframe(contagem_navios, hide_index=True, use_container_width=True)
    else:
        col_graf, col_tab = st.columns([1.2,1], gap="large")
        with col_graf:
            st.subheader("🏆 Top 10 Navios com Mais Cancelamentos")
            st.plotly_chart(grafico_top_navios(df_cancel, 'Navio'), use_container_width=True)
        with col_tab:
            st.subheader("📋 Detalhe dos 10 primeiros")
            st.dataframe(
                contagem_navios.head(10),
                hide_index=True,
                use_container_width=True,
                column_config={"QuantidadeCancelamentos": st.column_config.NumberColumn(format="%d")}
            )
        # Evolução mensal do líder
        lider = contagem_navios.iloc[0]['Navio']
        df_lider = df_cancel[df_cancel['Navio']==lider].copy()
        if col_data:
            df_lider['Mês'] = df_lider[col_data].dt.to_period('M').astype(str)
            if df_lider['Mês'].nunique()>1:
                st.markdown(f"### 📈 Evolução mensal de cancelamentos – **{lider}**")
                evo = (
                    df_lider['Mês']
                    .value_counts()
                    .sort_index()
                    .rename_axis('Mês')
                    .reset_index(name='Cancelamentos')
                )
                fig_evo = px.line(evo, x='Mês', y='Cancelamentos', markers=True)
                st.plotly_chart(theme_fig(fig_evo, altura=350), use_container_width=True)

with tab3:
    st.header("📅 Análise Temporal")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Cancelamentos por Mês")
        st.dataframe(contagem_mensal, hide_index=True, use_container_width=True)
    with c2:
        fig = px.line(contagem_mensal, x='Y-M', y='Cancelamentos', markers=True,
                      title='Evolução Mensal de Cancelamentos')
        fig.update_layout(xaxis_title="Mês", yaxis_title="Número de Cancelamentos", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("🌍 Análise de Rotas")
    if col_rota:
        contagem_rotas = (
            df_cancel[col_rota]
            .value_counts()
            .rename_axis('Rota')
            .reset_index(name='Cancelamentos')
        )
        r1, r2 = st.columns(2)
        with r1:
            st.subheader("🗺️ Top 10 Rotas com Mais Cancelamentos")
            st.dataframe(contagem_rotas.head(10), hide_index=True, use_container_width=True)
        with r2:
            fig = px.bar(contagem_rotas.head(5), x='Rota', y='Cancelamentos',
                         title='Top 5 Rotas com Mais Cancelamentos',
                         color='Cancelamentos', color_continuous_scale='Viridis')
            fig.update_layout(xaxis_title="Rota", yaxis_title="Qtd Cancelamentos", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Coluna 'De / Para' não encontrada.")

with tab5:
    st.header("📊 Análises Adicionais")
    sub1, sub2, sub3 = st.tabs(["🚢 Tipo de Navio","📦 Contêineres","🏢 Outros"])

    with sub1:
        if col_tipo_navio:
            df_cancel[col_tipo_navio] = df_cancel[col_tipo_navio].astype(str).str.strip().str.capitalize()
            cont_tipo = (
                df_cancel[col_tipo_navio]
                .value_counts()
                .rename_axis('TipoNavio')
                .reset_index(name='Cancelamentos')
            )
            t1, t2 = st.columns(2)
            with t1:
                st.subheader("📊 Distribuição por Tipo de Navio")
                st.dataframe(cont_tipo, hide_index=True, use_container_width=True)
            with t2:
                fig = px.pie(cont_tipo, values='Cancelamentos', names='TipoNavio',
                             title='Distribuição por Tipo de Navio', color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna 'Tipo' não encontrada.")

    with sub2:
        if col_conteineres:
            df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce')
            df_cont = df_cancel.dropna(subset=[col_conteineres])
            if not df_cont.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("📊 Estatísticas de Contêineres")
                    st.dataframe(df_cont[col_conteineres].describe().reset_index(), hide_index=True, use_container_width=True)
                with c2:
                    fig = px.histogram(df_cont, x=col_conteineres, title='Distribuição da Quantidade de Contêineres', nbins=20)
                    fig.update_layout(xaxis_title="Quantidade de Contêineres", yaxis_title="Frequência", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Sem dados de contêineres válidos.")
        else:
            st.warning("⚠️ Coluna 'Movs' não encontrada.")

    with sub3:
        if col_armador:
            df_cancel[col_armador] = (df_cancel[col_armador].astype(str)
                                      .str.strip()
                                      .replace({'':'Não Informado','nan':'Não Informado','None':'Não Informado'}))
            cont_arm = (
                df_cancel[col_armador]
                .value_counts()
                .rename_axis('Armador')
                .reset_index(name='Cancelamentos')
            )
            if not cont_arm.empty:
                a1, a2 = st.columns(2)
                with a1:
                    st.subheader("📊 Top 10 Armadores")
                    st.dataframe(cont_arm.head(10), hide_index=True, use_container_width=True)
                    st.metric("Total de Armadores", f"{len(cont_arm):,}", delta=f"{len(cont_arm)/len(df_cancel)*100:.1f}% do total")
                with a2:
                    top5 = cont_arm.head(5) if len(cont_arm)>=5 else cont_arm
                    fig = px.bar(top5, x='Armador', y='Cancelamentos', title='Top Armadores', color='Cancelamentos', color_continuous_scale='Viridis')
                    fig.update_layout(xaxis_title="Armador", yaxis_title="Qtd Cancelamentos", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                st.subheader("📈 Análise Detalhada")
                d1, d2 = st.columns(2)
                with d1:
                    st.write(cont_arm['Cancelamentos'].describe())
                with d2:
                    fig = px.pie(cont_arm.head(10), values='Cancelamentos', names='Armador', title='Distribuição dos 10 Maiores Armadores', color_discrete_sequence=px.colors.qualitative.Set3)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Nenhum dado de armador disponível.")
        else:
            st.warning("⚠️ Coluna 'Armador' não encontrada.")

with tab6:
    st.header("🔍 Análises Avançadas")
    sb1, sb2, sb3, sb4, sb5, sb6, sb7, sb8 = st.tabs([
        "⏱️ Tempo de Permanência","🔄 Serviço","🌍 País","📏 Dimensões",
        "📊 Correlações","⚓ Berço","📅 Dia da Semana","💰 Custos"
    ])

    # ⏱️ Tempo de Permanência
    with sb1:
        col_eta = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df_cancel.columns else None
        col_etd = 'Estimativa Saída ETD' if 'Estimativa Saída ETD' in df_cancel.columns else None
        col_ini = 'Início Operação' if 'Início Operação' in df_cancel.columns else None
        col_fim = 'Fim Operação' if 'Fim Operação' in df_cancel.columns else None

        if (col_eta and col_etd) or (col_ini and col_fim):
            if col_eta and col_etd:
                df_cancel[col_eta] = pd.to_datetime(df_cancel[col_eta], errors='coerce')
                df_cancel[col_etd] = pd.to_datetime(df_cancel[col_etd], errors='coerce')
                df_cancel['Tempo_Permanencia'] = (df_cancel[col_etd] - df_cancel[col_eta]).dt.total_seconds()/3600
            else:
                df_cancel[col_ini] = pd.to_datetime(df_cancel[col_ini], errors='coerce')
                df_cancel[col_fim] = pd.to_datetime(df_cancel[col_fim], errors='coerce')
                df_cancel['Tempo_Permanencia'] = (df_cancel[col_fim] - df_cancel[col_ini]).dt.total_seconds()/3600

            df_tmp = df_cancel.dropna(subset=['Tempo_Permanencia'])
            df_tmp = df_tmp[df_tmp['Tempo_Permanencia']>0]
            if not df_tmp.empty:
                t1, t2 = st.columns(2)
                with t1:
                    st.write(df_tmp['Tempo_Permanencia'].describe())
                with t2:
                    fig = px.box(df_tmp, y='Tempo_Permanencia', title='Distribuição do Tempo de Permanência')
                    fig.update_layout(yaxis_title="Horas")
                    st.plotly_chart(fig, use_container_width=True)
                if col_armador:
                    st.subheader("Tempo Médio por Armador")
                    tm = df_tmp.groupby(col_armador)['Tempo_Permanencia'].mean().reset_index().sort_values('Tempo_Permanencia', ascending=False)
                    fig = px.bar(tm.head(10), x=col_armador, y='Tempo_Permanencia', title='Top 10 Armadores por Tempo Médio', color='Tempo_Permanencia', color_continuous_scale='Viridis')
                    fig.update_layout(xaxis_title="Armador", yaxis_title="Horas", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Sem dados válidos de tempo de permanência.")
        else:
            st.warning("⚠️ Colunas de tempo não encontradas.")

    # 🔄 Serviço
    with sb2:
        col_serv = 'Serviço' if 'Serviço' in df_cancel.columns else None
        if col_serv:
            cs = df_cancel[col_serv].value_counts().rename_axis('Serviço').reset_index(name='Cancelamentos')
            s1, s2 = st.columns(2)
            with s1:
                st.write(cs.head(10))
            with s2:
                fig = px.pie(cs.head(10), values='Cancelamentos', names='Serviço', title='Top 10 Serviços')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna 'Serviço' não encontrada.")

    # 🌍 País
    with sb3:
        col_pais = 'País' if 'País' in df_cancel.columns else None
        if col_pais:
            cp = df_cancel[col_pais].value_counts().rename_axis('País').reset_index(name='Cancelamentos')
            p1, p2 = st.columns(2)
            with p1:
                st.write(cp.head(10))
            with p2:
                fig = px.bar(cp.head(10), x='País', y='Cancelamentos', title='Top 10 Países', color='Cancelamentos', color_continuous_scale='Viridis')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna 'País' não encontrada.")

    # 📏 Dimensões
    with sb4:
        col_comp = 'Comprimento' if 'Comprimento' in df_cancel.columns else None
        col_larg = 'Largura' if 'Largura' in df_cancel.columns else None
        if col_comp and col_larg:
            df_cancel[col_comp] = pd.to_numeric(df_cancel[col_comp], errors='coerce')
            df_cancel[col_larg] = pd.to_numeric(df_cancel[col_larg], errors='coerce')
            dd = df_cancel.dropna(subset=[col_comp,col_larg])
            if not dd.empty:
                fig = px.scatter(dd, x=col_comp, y=col_larg, title='Comprimento x Largura', color=col_status if col_status else None)
                st.plotly_chart(fig, use_container_width=True)
                st.write(dd[[col_comp,col_larg]].describe())
            else:
                st.warning("⚠️ Sem dados válidos.")
        else:
            st.warning("⚠️ Colunas de dimensões faltando.")

    # 📊 Correlações
    with sb5:
        num_cols = df_cancel.select_dtypes(include=[np.number]).columns
        if len(num_cols)>1:
            corr = df_cancel[num_cols].corr()
            fig = px.imshow(corr, title='Matriz de Correlação', color_continuous_scale='RdBu')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(corr, use_container_width=True)
        else:
            st.warning("⚠️ Poucas colunas numéricas.")

    # ⚓ Berço
    with sb6:
        col_berc = 'Berço' if 'Berço' in df_cancel.columns else None
        if col_berc:
            cb = df_cancel[col_berc].value_counts().rename_axis('Berço').reset_index(name='Cancelamentos')
            b1, b2 = st.columns(2)
            with b1:
                st.write(cb.head(10))
            with b2:
                fig = px.bar(cb.head(10), y='Berço', x='Cancelamentos', orientation='h', title='Top 10 Berços', color='Cancelamentos', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna 'Berço' não encontrada.")

    # 📅 Dia da Semana
    with sb7:
        if col_data:
            df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce')
            df_cancel['Dia_Semana'] = df_cancel[col_data].dt.day_name()
            cd = df_cancel['Dia_Semana'].value_counts().rename_axis('Dia da Semana').reset_index(name='Cancelamentos')
            ordem = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            cd['Dia da Semana'] = pd.Categorical(cd['Dia da Semana'], categories=ordem, ordered=True)
            cd = cd.sort_values('Dia da Semana')
            d1, d2 = st.columns(2)
            with d1:
                st.write(cd)
            with d2:
                fig = px.bar(cd, x='Dia da Semana', y='Cancelamentos', title='Cancelamentos por Dia da Semana', color='Cancelamentos', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna de data não encontrada.")

    # 💰 Custos
    with sb8:
        CUSTOS = {
            "TEU":            1200.0,
            "OPERACAO_PORTO": 1150.0,
            "DOCUMENTACAO":    950.0,
            "ARMAZENAGEM_DIA": 575.0,
            "ARMAZENAGEM_DIAS":2,
            "INSPECAO":        95.0
        }
        def calcular_custos(df, coluna_teu):
            df = df.copy()
            df[coluna_teu] = pd.to_numeric(df[coluna_teu], errors='coerce').fillna(0)
            df["C_TEUS"] = df[coluna_teu]*CUSTOS["TEU"]
            df["C_OPER"] = CUSTOS["OPERACAO_PORTO"]
            df["C_DOC"]  = CUSTOS["DOCUMENTACAO"]
            df["C_ARM"]  = df[coluna_teu]*CUSTOS["ARMAZENAGEM_DIA"]*CUSTOS["ARMAZENAGEM_DIAS"]
            df["C_INSP"]= CUSTOS["INSPECAO"]
            df["CUSTO_TOTAL"] = df[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
            return df

        if col_conteineres:
            df_cancel = calcular_custos(df_cancel, col_conteineres)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Custo Total Perdido", f"R$ {df_cancel['CUSTO_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with c2:
                st.metric("Custo Médio por Cancelamento", f"R$ {df_cancel['CUSTO_TOTAL'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with c3:
                st.metric("Total de TEUs Afetados", f"{df_cancel[col_conteineres].sum():,.0f}".replace(",", "."))

            # Distribuição de custos
            fig = px.box(df_cancel, y="CUSTO_TOTAL", title="Distribuição do Custo por Cancelamento", labels={"CUSTO_TOTAL":"R$"})
            st.plotly_chart(fig, use_container_width=True)

            # Evolução mensal de custos
            if col_data:
                df_cancel["Mes"] = df_cancel[col_data].dt.to_period("M")
                cm = df_cancel.groupby("Mes")["CUSTO_TOTAL"].sum().reset_index()
                cm["Mes"] = cm["Mes"].astype(str)
                fig = px.line(cm, x="Mes", y="CUSTO_TOTAL", markers=True, title="Evolução Mensal dos Custos", labels={"CUSTO_TOTAL":"R$"})
                st.plotly_chart(fig, use_container_width=True)

            # Componentes de custo
            comp = df_cancel[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum().rename(index={
                "C_TEUS":"THC","C_OPER":"Taxa Cancelamento","C_DOC":"Despachante","C_ARM":"Armazenagem","C_INSP":"Scanner"
            }).reset_index().rename(columns={"index":"Tipo","C_TEUS":"Valor"})
            comp["Valor"] = comp["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.subheader("📊 Detalhamento dos Custos")
            cols = st.columns(2)
            cols[0].dataframe(comp, hide_index=True, use_container_width=True)
            cols[1].plotly_chart(px.pie(comp, values="Valor", names="Tipo", title="Distribuição de Custos"), use_container_width=True)

            # Custo por armador
            if col_armador:
                ca = df_cancel.groupby(col_armador)["CUSTO_TOTAL"].agg(['sum','mean','count']).reset_index()
                ca.columns = [col_armador,"Custo Total","Custo Médio","Quantity"]
                ca["Custo Total"] = ca["Custo Total"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                ca["Custo Médio"] = ca["Custo Médio"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.subheader("🔍 Custos por Armador")
                c1, c2 = st.columns(2)
                c1.dataframe(ca.head(10), hide_index=True, use_container_width=True)
                # gráfico
                cg = ca.head(10).copy()
                cg["Custo Total"] = cg["Custo Total"].str.replace("R$ ","").str.replace(".","").str.replace(",",".").astype(float)
                fig = px.bar(cg, x=col_armador, y="Custo Total", title="Top 10 Armadores por Custo Total", color="Custo Total", color_continuous_scale="Viridis")
                c2.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Coluna de contêineres não encontrada. Não é possível calcular custos.")
