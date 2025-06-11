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
    html, body, [class*="css"] {
        font-family: 'Inter', Arial, sans-serif !important;
    }
    .main {
        padding: 2.5rem 1.5rem 1.5rem 1.5rem;
        background: var(--background-color, #181a1b);
    }
    .stMetric, .stDataFrame, .stMarkdown, .js-plotly-plot, .stFileUploader, .stContainer {
        background: rgba(255,255,255,0.07);
        border-radius: 18px;
        box-shadow: none;
        padding: 1.2rem 1.2rem 1.2rem 1.2rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(200,200,200,0.08);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        background: transparent;
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(240,242,246,0.13);
        border-radius: 10px 10px 0 0;
        color: var(--text-color, #eaeaea);
        font-weight: 500;
        font-size: 1.1rem;
        transition: background 0.2s, color 0.2s;
        padding: 0.7rem 1.5rem;
        margin-right: 0.2rem;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(76,175,80,0.13);
        color: #4CAF50;
    }
    .stTabs [aria-selected="true"] {
        background: #4CAF50;
        color: #fff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color, #fff);
        font-family: 'Inter', Arial, sans-serif;
        font-weight: 700;
        margin-bottom: 0.7rem;
        letter-spacing: -1px;
    }
    h1 { font-size: 2.5rem; margin-bottom: 1.2rem; }
    h2 { font-size: 2rem; margin-bottom: 1rem; }
    h3 { font-size: 1.4rem; margin-bottom: 0.7rem; }
    .stSubheader {
        color: #4CAF50;
        font-weight: 600;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 0.3rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
    }
    .stButton button {
        background: #4CAF50;
        color: #fff;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: background 0.2s;
        font-size: 1rem;
        padding: 0.5rem 1.2rem;
    }
    .stButton button:hover {
        background: #388e3c;
    }
    /* Sidebar adaptativo */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #23272f 70%, #4CAF50 100%) !important;
        color: #fff !important;
        padding: 0.5rem 0.5rem 0.5rem 0.5rem !important;
    }
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li {
        color: #fff !important;
        font-size: 1.05rem;
    }
    section[data-testid="stSidebar"] ul {
        margin-bottom: 0.5rem;
    }
    /* Cards principais */
    .dashboard-card {
        background: rgba(255,255,255,0.10);
        border-radius: 18px;
        box-shadow: none;
        padding: 1.2rem 1.2rem 1.2rem 1.2rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(200,200,200,0.08);
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    /* Responsividade */
    @media (max-width: 900px) {
        .main { padding: 0.5rem; }
        .stContainer, .stMetric, .stDataFrame, .stMarkdown, .dashboard-card { padding: 0.5rem; }
        h1 { font-size: 1.5rem; }
        h2 { font-size: 1.2rem; }
    }
    </style>
""", unsafe_allow_html=True)

# Título e descrição com estilo melhorado e adaptativo
st.markdown("""
    <div class='dashboard-card' style='text-align: center;'>
        <h1 style='margin-bottom: 0.5rem;'>🚢 Análise de Levantamentos de Cancelamentos de Navios</h1>
        <div style='background: rgba(240,242,246,0.13); padding: 1.2rem; border-radius: 12px; margin-bottom: 0.5rem;'>
            <h2 style='color: #4CAF50; margin-bottom: 0.7rem;'>Dashboard Interativo de Análise de Cancelamentos</h2>
            <p style='color: #e0e0e0; margin-bottom: 1.2rem;'>Este aplicativo fornece insights detalhados sobre cancelamentos de navios, incluindo:</p>
            <div style='display: flex; justify-content: center; gap: 1.2rem; flex-wrap: wrap;'>
                <div style='background: rgba(255,255,255,0.10); padding: 0.7rem 1.1rem; border-radius: 8px;'>
                    <span style='font-size: 1.05rem;'>📊 Análise de tendências temporais</span>
                </div>
                <div style='background: rgba(255,255,255,0.10); padding: 0.7rem 1.1rem; border-radius: 8px;'>
                    <span style='font-size: 1.05rem;'>🚢 Identificação de navios mais afetados</span>
                </div>
                <div style='background: rgba(255,255,255,0.10); padding: 0.7rem 1.1rem; border-radius: 8px;'>
                    <span style='font-size: 1.05rem;'>🌍 Análise de rotas e portos</span>
                </div>
                <div style='background: rgba(255,255,255,0.10); padding: 0.7rem 1.1rem; border-radius: 8px;'>
                    <span style='font-size: 1.05rem;'>📈 Métricas e estatísticas detalhadas</span>
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar com estilo melhorado e adaptativo
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; margin-bottom: 1.2rem;'>
            <img src='https://img.icons8.com/color/96/000000/cruise-ship.png' style='width: 90px; margin-bottom: 0.7rem;'>
            <h3 style='margin-bottom: 0.7rem;'>📋 Sobre o Projeto</h3>
            <div style='background: rgba(255,255,255,0.10); padding: 0.7rem; border-radius: 10px;'>
                <p style='margin-bottom: 0.7rem;'>Este dashboard foi desenvolvido como parte de um projeto acadêmico para análise de dados de cancelamentos de navios.</p>
                <h4 style='margin-bottom: 0.3rem;'>Integrantes:</h4>
                <ul style='list-style-type: none; padding: 0; margin: 0;'>
                    <li style='margin-bottom: 0.3rem;'>👤 Arley do Nascimento Vinagre</li>
                    <li style='margin-bottom: 0.3rem;'>👤 Vinicius Santana</li>
                    <li style='margin-bottom: 0.3rem;'>👤 Tauan Santos Santana</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
        <div style='background: rgba(255,255,255,0.10); padding: 0.7rem; border-radius: 10px;'>
            <h3 style='margin-bottom: 0.7rem;'>📊 Filtros</h3>
            <p>Faça upload do arquivo Excel para começar a análise.</p>
        </div>
    """, unsafe_allow_html=True)

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

    # Preparar dados para o resumo
    contagem_navios = df_cancel[col_navio].value_counts().reset_index()
    contagem_navios.columns = ['Navio', 'QuantidadeCancelamentos']
    
    # Converter data e preparar análise temporal
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
    df_cancel['Ano'] = df_cancel[col_data].dt.year
    df_cancel['Mês'] = df_cancel[col_data].dt.month
    df_cancel['Y-M'] = df_cancel[col_data].dt.to_period('M').astype(str)
    
    # Análise mensal
    contagem_mensal = df_cancel.groupby('Y-M').size().reset_index(name='Cancelamentos')
    contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
    contagem_mensal = contagem_mensal.sort_values('Y-M')

    # Resumo final na sidebar
    with st.sidebar:
        st.markdown("### 📊 Resumo dos Resultados")
        
        # Definir max_mes antes de usar
        max_mes = None
        if not contagem_mensal.empty and len(contagem_mensal) > 0:
            max_mes = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        
        resumo_texto = f"""
            - **Total de cancelamentos:** {len(df_cancel):,}
            - **Navio mais cancelado:** {contagem_navios.iloc[0]['Navio']} ({contagem_navios.iloc[0]['QuantidadeCancelamentos']} vezes)
        """
        
        if max_mes is not None:
            resumo_texto += f"""
            - **Mês com mais cancelamentos:** {max_mes['Y-M'].strftime('%Y-%m')} ({int(max_mes['Cancelamentos'])} cancelamentos)
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
                
                # Limpar e preparar dados do armador
                df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip().str.capitalize()
                df_cancel[col_armador] = df_cancel[col_armador].replace('', 'Não Informado')
                df_cancel[col_armador] = df_cancel[col_armador].replace('Nan', 'Não Informado')
                df_cancel[col_armador] = df_cancel[col_armador].replace('None', 'Não Informado')
                
                contagem_armadores = df_cancel[col_armador].value_counts().reset_index()
                contagem_armadores.columns = ['Armador', 'Cancelamentos']
                
                if not contagem_armadores.empty and len(contagem_armadores) > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📊 Top 10 Armadores")
                        st.dataframe(
                            contagem_armadores.head(10),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Métricas adicionais
                        total_armadores = len(contagem_armadores)
                        st.metric(
                            "Total de Armadores",
                            f"{total_armadores:,}",
                            delta=f"{(total_armadores/len(df_cancel)*100):.1f}% do total"
                        )

                    with col2:
                        if len(contagem_armadores) >= 5:
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
                        else:
                            fig = px.bar(
                                contagem_armadores,
                                x='Armador',
                                y='Cancelamentos',
                                title='Armadores com Cancelamentos',
                                color='Cancelamentos',
                                color_continuous_scale='Viridis'
                            )
                            fig.update_layout(
                                xaxis_title="Armador",
                                yaxis_title="Quantidade de Cancelamentos",
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Análise adicional
                    st.subheader("📈 Análise Detalhada")
                    col1, col2 = st.columns(2)
                    with col1:
                        # Estatísticas básicas
                        st.write("Estatísticas dos Cancelamentos por Armador:")
                        st.write(contagem_armadores['Cancelamentos'].describe())
                    
                    with col2:
                        # Gráfico de pizza para distribuição
                        fig = px.pie(
                            contagem_armadores.head(10),
                            values='Cancelamentos',
                            names='Armador',
                            title='Distribuição dos 10 Maiores Armadores',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ Nenhum dado de armador disponível para análise.")
            else:
                st.warning("⚠️ Coluna 'Armador' não encontrada nos dados.")

    with tab6:
        st.header("🔍 Análises Avançadas")
        
        # Criar subabas para análises avançadas
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6, sub_tab7, sub_tab8 = st.tabs([
            "⏱️ Tempo de Permanência",
            "🔄 Análise por Serviço",
            "🌍 Análise por País",
            "📏 Dimensões dos Navios",
            "📊 Correlações",
            "⚓ Análise por Berço",
            "📅 Cancelamentos por Dia",
            "💰 Análise de Custos"
        ])
        
        with sub_tab1:
            st.subheader("⏱️ Tempo de Permanência no Porto")
            
            # Verificar colunas necessárias
            col_eta = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df_cancel.columns else None
            col_etd = 'Estimativa Saída ETD' if 'Estimativa Saída ETD' in df_cancel.columns else None
            col_inicio = 'Início Operação' if 'Início Operação' in df_cancel.columns else None
            col_fim = 'Fim Operação' if 'Fim Operação' in df_cancel.columns else None
            
            if (col_eta and col_etd) or (col_inicio and col_fim):
                # Converter datas
                if col_eta and col_etd:
                    df_cancel[col_eta] = pd.to_datetime(df_cancel[col_eta], errors='coerce')
                    df_cancel[col_etd] = pd.to_datetime(df_cancel[col_etd], errors='coerce')
                    df_cancel['Tempo_Permanencia'] = (df_cancel[col_etd] - df_cancel[col_eta]).dt.total_seconds() / 3600  # em horas
                else:
                    df_cancel[col_inicio] = pd.to_datetime(df_cancel[col_inicio], errors='coerce')
                    df_cancel[col_fim] = pd.to_datetime(df_cancel[col_fim], errors='coerce')
                    df_cancel['Tempo_Permanencia'] = (df_cancel[col_fim] - df_cancel[col_inicio]).dt.total_seconds() / 3600  # em horas
                
                # Remover valores inválidos
                df_tempo = df_cancel.dropna(subset=['Tempo_Permanencia'])
                df_tempo = df_tempo[df_tempo['Tempo_Permanencia'] > 0]
                
                if not df_tempo.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        # Estatísticas básicas
                        st.write("Estatísticas do Tempo de Permanência (horas):")
                        st.write(df_tempo['Tempo_Permanencia'].describe())
                    
                    with col2:
                        # Boxplot
                        fig = px.box(
                            df_tempo,
                            y='Tempo_Permanencia',
                            title='Distribuição do Tempo de Permanência',
                            color_discrete_sequence=['#4CAF50']
                        )
                        fig.update_layout(yaxis_title="Tempo (horas)")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Análise por armador
                    if col_armador is not None:
                        st.subheader("Tempo de Permanência por Armador")
                        tempo_por_armador = df_tempo.groupby(col_armador)['Tempo_Permanencia'].mean().reset_index()
                        tempo_por_armador = tempo_por_armador.sort_values('Tempo_Permanencia', ascending=False)
                        
                        fig = px.bar(
                            tempo_por_armador.head(10),
                            x=col_armador,
                            y='Tempo_Permanencia',
                            title='Top 10 Armadores por Tempo Médio de Permanência',
                            color='Tempo_Permanencia',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(
                            xaxis_title="Armador",
                            yaxis_title="Tempo Médio (horas)",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ Não há dados válidos para análise de tempo de permanência.")
            else:
                st.warning("⚠️ Colunas necessárias para análise de tempo de permanência não encontradas.")
        
        with sub_tab2:
            st.subheader("🔄 Análise por Serviço")
            
            col_servico = 'Serviço' if 'Serviço' in df_cancel.columns else None
            if col_servico is not None:
                contagem_servicos = df_cancel[col_servico].value_counts().reset_index()
                contagem_servicos.columns = ['Serviço', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Top 10 Serviços com Mais Cancelamentos:")
                    st.dataframe(
                        contagem_servicos.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de pizza
                    fig = px.pie(
                        contagem_servicos.head(10),
                        values='Cancelamentos',
                        names='Serviço',
                        title='Distribuição dos 10 Maiores Serviços',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Coluna 'Serviço' não encontrada nos dados.")
        
        with sub_tab3:
            st.subheader("🌍 Análise por País")
            
            col_pais = 'País' if 'País' in df_cancel.columns else None
            if col_pais is not None:
                contagem_paises = df_cancel[col_pais].value_counts().reset_index()
                contagem_paises.columns = ['País', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Top 10 Países com Mais Cancelamentos:")
                    st.dataframe(
                        contagem_paises.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de barras
                    fig = px.bar(
                        contagem_paises.head(10),
                        x='País',
                        y='Cancelamentos',
                        title='Top 10 Países com Mais Cancelamentos',
                        color='Cancelamentos',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(
                        xaxis_title="País",
                        yaxis_title="Quantidade de Cancelamentos",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Coluna 'País' não encontrada nos dados.")
        
        with sub_tab4:
            st.subheader("📏 Análise de Dimensões dos Navios")
            
            col_comprimento = 'Comprimento' if 'Comprimento' in df_cancel.columns else None
            col_largura = 'Largura' if 'Largura' in df_cancel.columns else None
            
            if col_comprimento and col_largura:
                # Converter para numérico
                df_cancel[col_comprimento] = pd.to_numeric(df_cancel[col_comprimento], errors='coerce')
                df_cancel[col_largura] = pd.to_numeric(df_cancel[col_largura], errors='coerce')
                
                # Remover valores inválidos
                df_dimensoes = df_cancel.dropna(subset=[col_comprimento, col_largura])
                
                if not df_dimensoes.empty:
                    # Gráfico de dispersão
                    fig = px.scatter(
                        df_dimensoes,
                        x=col_comprimento,
                        y=col_largura,
                        title='Relação entre Comprimento e Largura dos Navios',
                        color=col_status if col_status else None,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_layout(
                        xaxis_title="Comprimento",
                        yaxis_title="Largura"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estatísticas
                    st.write("Estatísticas das Dimensões:")
                    st.write(df_dimensoes[[col_comprimento, col_largura]].describe())
                else:
                    st.warning("⚠️ Não há dados válidos para análise de dimensões.")
            else:
                st.warning("⚠️ Colunas de dimensões não encontradas nos dados.")
        
        with sub_tab5:
            st.subheader("📊 Correlação entre Variáveis Operacionais")
            
            # Selecionar colunas numéricas
            colunas_numericas = df_cancel.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(colunas_numericas) > 1:
                # Calcular correlação
                corr_matrix = df_cancel[colunas_numericas].corr()
                
                # Heatmap
                fig = px.imshow(
                    corr_matrix,
                    title='Matriz de Correlação',
                    color_continuous_scale='RdBu',
                    aspect='auto'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Exibir valores de correlação
                st.write("Valores de Correlação:")
                st.dataframe(corr_matrix, use_container_width=True)
            else:
                st.warning("⚠️ Não há colunas numéricas suficientes para análise de correlação.")
        
        with sub_tab6:
            st.subheader("⚓ Análise por Berço")
            
            col_berco = 'Berço' if 'Berço' in df_cancel.columns else None
            if col_berco is not None:
                contagem_bercos = df_cancel[col_berco].value_counts().reset_index()
                contagem_bercos.columns = ['Berço', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Top 10 Berços com Mais Cancelamentos:")
                    st.dataframe(
                        contagem_bercos.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de barras horizontais
                    fig = px.bar(
                        contagem_bercos.head(10),
                        y='Berço',
                        x='Cancelamentos',
                        title='Top 10 Berços com Mais Cancelamentos',
                        color='Cancelamentos',
                        color_continuous_scale='Viridis',
                        orientation='h'
                    )
                    fig.update_layout(
                        yaxis_title="Berço",
                        xaxis_title="Quantidade de Cancelamentos",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Coluna 'Berço' não encontrada nos dados.")
        
        with sub_tab7:
            st.subheader("📅 Cancelamentos por Dia da Semana")
            
            if col_data is not None:
                # Converter data e extrair dia da semana
                df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce')
                df_cancel['Dia_Semana'] = df_cancel[col_data].dt.day_name()
                
                # Contagem por dia da semana
                contagem_dias = df_cancel['Dia_Semana'].value_counts().reset_index()
                contagem_dias.columns = ['Dia da Semana', 'Cancelamentos']
                
                # Ordenar dias da semana
                ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                contagem_dias['Dia da Semana'] = pd.Categorical(
                    contagem_dias['Dia da Semana'],
                    categories=ordem_dias,
                    ordered=True
                )
                contagem_dias = contagem_dias.sort_values('Dia da Semana')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Cancelamentos por Dia da Semana:")
                    st.dataframe(
                        contagem_dias,
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    # Gráfico de barras
                    fig = px.bar(
                        contagem_dias,
                        x='Dia da Semana',
                        y='Cancelamentos',
                        title='Cancelamentos por Dia da Semana',
                        color='Cancelamentos',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(
                        xaxis_title="Dia da Semana",
                        yaxis_title="Quantidade de Cancelamentos",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Coluna de data não encontrada nos dados.")

        with sub_tab8:
            st.subheader("💰 Análise de Custos de Exportação")
            
            # Valores médios de custos (em USD)
            custo_medio_teu = 2500  # Custo médio por TEU para exportação
            custo_medio_operacao = 8000  # Custo médio de operação portuária para exportação
            custo_medio_documentacao = 3500  # Custo médio de documentação para exportação
            custo_medio_armazenagem = 200  # Custo médio de armazenagem por TEU/dia
            custo_medio_inspecao = 1500  # Custo médio de inspeção por operação
            
            # Calcular custos
            if col_conteineres is not None:
                # Converter coluna de contêineres para numérico
                df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce')
                
                # Calcular custos básicos
                df_cancel['Custo_Containers'] = df_cancel[col_conteineres] * custo_medio_teu
                df_cancel['Custo_Operacao'] = custo_medio_operacao
                df_cancel['Custo_Documentacao'] = custo_medio_documentacao
                
                # Calcular custos adicionais
                if col_data is not None:
                    # Calcular dias de armazenagem (assumindo média de 5 dias)
                    df_cancel['Custo_Armazenagem'] = df_cancel[col_conteineres] * custo_medio_armazenagem * 5
                else:
                    df_cancel['Custo_Armazenagem'] = 0
                
                df_cancel['Custo_Inspecao'] = custo_medio_inspecao
                
                # Custo total
                df_cancel['Custo_Total'] = (
                    df_cancel['Custo_Containers'] + 
                    df_cancel['Custo_Operacao'] + 
                    df_cancel['Custo_Documentacao'] + 
                    df_cancel['Custo_Armazenagem'] + 
                    df_cancel['Custo_Inspecao']
                )
                
                # Métricas principais
                col1, col2, col3 = st.columns(3)
                with col1:
                    custo_total = df_cancel['Custo_Total'].sum()
                    st.metric(
                        "Custo Total Perdido",
                        f"USD {custo_total:,.2f}",
                        delta=f"{(custo_total/1000000):.2f}M USD"
                    )
                
                with col2:
                    custo_medio = df_cancel['Custo_Total'].mean()
                    st.metric(
                        "Custo Médio por Cancelamento",
                        f"USD {custo_medio:,.2f}",
                        delta="por operação"
                    )
                
                with col3:
                    total_containers = df_cancel[col_conteineres].sum()
                    st.metric(
                        "Total de TEUs Afetados",
                        f"{total_containers:,.0f}",
                        delta="contêineres"
                    )
                
                # Gráfico de distribuição de custos
                fig = px.box(
                    df_cancel,
                    y='Custo_Total',
                    title='Distribuição dos Custos por Cancelamento',
                    color_discrete_sequence=['#4CAF50']
                )
                fig.update_layout(yaxis_title="Custo (USD)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise por armador
                if col_armador is not None:
                    st.subheader("Custos por Armador")
                    custos_por_armador = df_cancel.groupby(col_armador)['Custo_Total'].agg(['sum', 'mean', 'count']).reset_index()
                    custos_por_armador.columns = ['Armador', 'Custo Total', 'Custo Médio', 'Quantidade']
                    custos_por_armador = custos_por_armador.sort_values('Custo Total', ascending=False)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Top 10 Armadores por Custo Total:")
                        st.dataframe(
                            custos_por_armador.head(10),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        fig = px.bar(
                            custos_por_armador.head(10),
                            x='Armador',
                            y='Custo Total',
                            title='Top 10 Armadores por Custo Total',
                            color='Custo Total',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(
                            xaxis_title="Armador",
                            yaxis_title="Custo Total (USD)",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Análise temporal dos custos
                if col_data is not None:
                    st.subheader("Evolução Temporal dos Custos")
                    df_cancel['Mês'] = pd.to_datetime(df_cancel[col_data]).dt.to_period('M')
                    custos_mensais = df_cancel.groupby('Mês')['Custo_Total'].sum().reset_index()
                    custos_mensais['Mês'] = custos_mensais['Mês'].astype(str)
                    
                    fig = px.line(
                        custos_mensais,
                        x='Mês',
                        y='Custo_Total',
                        title='Evolução Mensal dos Custos',
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Mês",
                        yaxis_title="Custo Total (USD)",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detalhamento dos custos
                st.subheader("Detalhamento dos Custos")
                col1, col2 = st.columns(2)
                with col1:
                    custos_detalhados = {
                        'Tipo de Custo': [
                            'Contêineres',
                            'Operação Portuária',
                            'Documentação',
                            'Armazenagem',
                            'Inspeção'
                        ],
                        'Valor Total (USD)': [
                            df_cancel['Custo_Containers'].sum(),
                            df_cancel['Custo_Operacao'].sum(),
                            df_cancel['Custo_Documentacao'].sum(),
                            df_cancel['Custo_Armazenagem'].sum(),
                            df_cancel['Custo_Inspecao'].sum()
                        ]
                    }
                    st.dataframe(
                        pd.DataFrame(custos_detalhados),
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col2:
                    fig = px.pie(
                        values=[
                            df_cancel['Custo_Containers'].sum(),
                            df_cancel['Custo_Operacao'].sum(),
                            df_cancel['Custo_Documentacao'].sum(),
                            df_cancel['Custo_Armazenagem'].sum(),
                            df_cancel['Custo_Inspecao'].sum()
                        ],
                        names=[
                            'Contêineres',
                            'Operação Portuária',
                            'Documentação',
                            'Armazenagem',
                            'Inspeção'
                        ],
                        title='Distribuição dos Custos por Categoria',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Análise de impacto por tipo de navio
                if col_tipo_navio is not None:
                    st.subheader("Análise de Custos por Tipo de Navio")
                    custos_por_tipo = df_cancel.groupby(col_tipo_navio)['Custo_Total'].agg(['sum', 'mean', 'count']).reset_index()
                    custos_por_tipo.columns = ['Tipo de Navio', 'Custo Total', 'Custo Médio', 'Quantidade']
                    custos_por_tipo = custos_por_tipo.sort_values('Custo Total', ascending=False)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Custos por Tipo de Navio:")
                        st.dataframe(
                            custos_por_tipo,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        fig = px.bar(
                            custos_por_tipo,
                            x='Tipo de Navio',
                            y='Custo Total',
                            title='Custos por Tipo de Navio',
                            color='Custo Total',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(
                            xaxis_title="Tipo de Navio",
                            yaxis_title="Custo Total (USD)",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Coluna de contêineres não encontrada nos dados. Não é possível calcular os custos.")

else:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel para começar a análise.") 