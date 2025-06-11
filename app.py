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

# Configuração da página
st.set_page_config(
    page_title="Análise de Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Título e descrição
st.title("🚢 Análise de Levantamentos de Cancelamentos de Navios")
st.markdown("""
    <div style='text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 2rem;'>
        <h3>Dashboard Interativo de Análise de Cancelamentos</h3>
        <p>Este aplicativo fornece insights detalhados sobre cancelamentos de navios, incluindo:</p>
        <ul style='list-style-type: none;'>
            <li>📊 Análise de tendências temporais</li>
            <li>🚢 Identificação de navios mais afetados</li>
            <li>🌍 Análise de rotas e portos</li>
            <li>📈 Métricas e estatísticas detalhadas</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# Sidebar com informações do projeto
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/cruise-ship.png", width=100)
    st.markdown("### 📋 Sobre o Projeto")
    st.markdown("""
        Este dashboard foi desenvolvido como parte de um projeto acadêmico para análise de dados de cancelamentos de navios.
        
        **Integrantes:**
        - Arley do Nascimento Vinagre
        - Vinicius Santana
        - Tauan Santos Santana
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Filtros")
    st.markdown("Faça upload do arquivo Excel para começar a análise.")

# Upload do arquivo
uploaded_file = st.file_uploader("📁 Faça o upload do arquivo Excel", type=["xlsx"])

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

    # Filtrar cancelamentos
    df[col_status] = df[col_status].astype(str).str.strip().str.lower()
    valores_cancelados = ['cancelado', 'cancelada', 'rejeitado', 'rej.', 'canceled']
    mask_cancel = df[col_status].isin(valores_cancelados)
    df_cancel = df.loc[mask_cancel].copy()

    # Criar abas para diferentes análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Visão Geral", 
        "🚢 Análise de Navios", 
        "📅 Análise Temporal",
        "🌍 Análise de Rotas",
        "📊 Análises Adicionais"
    ])

    with tab1:
        st.header("📊 Visão Geral dos Cancelamentos")
        
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

        # Gráfico de pizza com Plotly
        fig = px.pie(
            values=[len(df_cancel), len(df) - len(df_cancel)],
            names=['Cancelados', 'Não Cancelados'],
            title='Distribuição de Cancelamentos',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)

        # Exibir primeiros registros com estilo
        st.subheader("📋 Primeiros Registros de Cancelamento")
        st.dataframe(
            df_cancel.head(),
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.header("🚢 Análise de Navios")
        
        # Top 10 navios mais cancelados
        contagem_navios = df_cancel[col_navio].value_counts().reset_index()
        contagem_navios.columns = ['Navio', 'QuantidadeCancelamentos']
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏆 Top 10 Navios com Mais Cancelamentos")
            st.dataframe(
                contagem_navios.head(10),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            # Gráfico de barras com Plotly
            fig = px.bar(
                contagem_navios.head(5),
                x='Navio',
                y='QuantidadeCancelamentos',
                title='Top 5 Navios com Mais Cancelamentos',
                color='QuantidadeCancelamentos',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                xaxis_title="Navio",
                yaxis_title="Quantidade de Cancelamentos",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.header("📅 Análise Temporal")
        
        # Converter data
        df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
        df_cancel['Ano'] = df_cancel[col_data].dt.year
        df_cancel['Mês'] = df_cancel[col_data].dt.month
        df_cancel['Y-M'] = df_cancel[col_data].dt.to_period('M').astype(str)

        # Análise mensal
        contagem_mensal = df_cancel.groupby('Y-M').size().reset_index(name='Cancelamentos')
        contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
        contagem_mensal = contagem_mensal.sort_values('Y-M')

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Cancelamentos por Mês")
            st.dataframe(
                contagem_mensal,
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            # Gráfico de linha com Plotly
            fig = px.line(
                contagem_mensal,
                x='Y-M',
                y='Cancelamentos',
                title='Evolução Mensal de Cancelamentos',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Mês",
                yaxis_title="Número de Cancelamentos",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.header("🌍 Análise de Rotas")
        
        if col_rota is not None:
            contagem_rotas = df_cancel[col_rota].value_counts().reset_index()
            contagem_rotas.columns = ['Rota', 'Cancelamentos']
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🗺️ Top 10 Rotas com Mais Cancelamentos")
                st.dataframe(
                    contagem_rotas.head(10),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                # Gráfico de barras com Plotly
                fig = px.bar(
                    contagem_rotas.head(5),
                    x='Rota',
                    y='Cancelamentos',
                    title='Top 5 Rotas com Mais Cancelamentos',
                    color='Cancelamentos',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    xaxis_title="Rota",
                    yaxis_title="Quantidade de Cancelamentos",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.header("📊 Análises Adicionais")
        
        # Criar subabas para análises adicionais
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🚢 Tipo de Navio", "📦 Contêineres", "🏢 Outros"])
        
        with sub_tab1:
            if col_tipo_navio is not None:
                df_cancel[col_tipo_navio] = df_cancel[col_tipo_navio].astype(str).str.strip().str.capitalize()
                contagem_tipo_navio = df_cancel[col_tipo_navio].value_counts().reset_index()
                contagem_tipo_navio.columns = ['TipoNavio', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📊 Distribuição por Tipo de Navio")
                    st.dataframe(
                        contagem_tipo_navio,
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de pizza com Plotly
                    fig = px.pie(
                        contagem_tipo_navio,
                        values='Cancelamentos',
                        names='TipoNavio',
                        title='Distribuição de Cancelamentos por Tipo de Navio',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with sub_tab2:
            if col_conteineres is not None:
                df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce')
                df_cancel_conteineres = df_cancel.dropna(subset=[col_conteineres])
                
                if len(df_cancel_conteineres) > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📊 Estatísticas de Contêineres")
                        st.dataframe(
                            df_cancel_conteineres[col_conteineres].describe().reset_index(),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        # Histograma com Plotly
                        fig = px.histogram(
                            df_cancel_conteineres,
                            x=col_conteineres,
                            title='Distribuição da Quantidade de Contêineres',
                            nbins=20,
                            color_discrete_sequence=['#4CAF50']
                        )
                        fig.update_layout(
                            xaxis_title="Quantidade de Contêineres",
                            yaxis_title="Frequência",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with sub_tab3:
            # Análise por Armador
            col_armador = 'Armador' if 'Armador' in df_cancel.columns else None
            if col_armador is not None:
                st.subheader("🏢 Análise por Armador")
                df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip().str.capitalize()
                contagem_armadores = df_cancel[col_armador].value_counts().reset_index()
                contagem_armadores.columns = ['Armador', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(
                        contagem_armadores.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de barras com Plotly
                    fig = px.bar(
                        contagem_armadores.head(5),
                        x='Armador',
                        y='Cancelamentos',
                        title='Top 5 Armadores com Mais Cancelamentos',
                        color='Cancelamentos',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(
                        xaxis_title="Armador",
                        yaxis_title="Quantidade de Cancelamentos",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # Resumo final na sidebar
    with st.sidebar:
        st.markdown("### 📊 Resumo dos Resultados")
        st.markdown(f"""
            - **Total de cancelamentos:** {len(df_cancel):,}
            - **Navio mais cancelado:** {contagem_navios.iloc[0]['Navio']} ({contagem_navios.iloc[0]['QuantidadeCancelamentos']} vezes)
            - **Mês com mais cancelamentos:** {max_mes['Y-M'].strftime('%Y-%m')} ({int(max_mes['Cancelamentos'])} cancelamentos)
        """)

else:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel para começar a análise.") 