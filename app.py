import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚓ Dashboard Marítimo de Cancelamentos",
    page_icon="🚢",
    layout="wide"
)

# ─── CSS tema náutico ──────────────────────────────────────────────────────────
st.markdown("""
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
h1, h2, h3, h4 { text-align: center; margin-bottom: 0.5rem; }
[data-testid="stMarkdownContainer"] p { line-height: 1.6; }
.js-plotly-plot { margin-bottom: 3rem !important; }
section.main > div.block-container { padding: 2rem 1rem; }
[data-testid="stColumns"] > div { margin-bottom: 2rem; }
.stTextInput, .stFileUploader, .stSelectbox, .stButton { margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-card">
  <h1>⚓ Análise de Cancelamentos de Navios</h1>
  <p>Um dashboard interativo com tema náutico — todos os gráficos feitos em Plotly para 100% de interatividade.</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload & Filtros")
    uploaded = st.file_uploader("Faça upload do Excel (.xlsx)", type="xlsx")
    termo = st.text_input("🔍 Filtrar por navio, armador ou rota")
    st.markdown("---")
    st.markdown("""
        <div style='background: rgba(255,255,255,0.10); padding: 0.7rem; border-radius: 10px;'>
            <h3 style='margin-bottom: 0.7rem;'>📊 Filtros</h3>
            <p>Faça upload do arquivo Excel para começar a análise.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Adicionar seção de referências de custos
    st.markdown("---")
    st.markdown("""
        <div style='background: rgba(255,255,255,0.10); padding: 0.7rem; border-radius: 10px;'>
            <h3 style='margin-bottom: 0.7rem;'>💰 Referências de Custos</h3>
            <p style='font-size: 0.9rem; margin-bottom: 0.5rem;'>Valores baseados em tabelas 2024-25:</p>
            <ul style='font-size: 0.85rem; padding-left: 1rem;'>
                <li>THC: Cosco "Brazil Local Charges" <b>(R$ 1.200,00 por TEU)</b></li>
                <li>Armazenagem: Tabela Ecoporto 2024/25 <b>(R$ 575,00/TEU/dia)</b></li>
                <li>Despachante: Tabela Sindaesc 2024 <b>(R$ 950,00)</b></li>
                <li>Scanner: Santos Brasil (reajuste 2024) <b>(R$ 95,00 por contêiner)</b></li>
            </ul>
            <p style='font-size: 0.8rem; margin-top: 0.5rem; color: #4CAF50;'>
                Câmbio médio: <b>R$ 5,10</b>/US$ 1
            </p>
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
                    dados_x = df_cancel['Y-M'].astype(str)
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

        # Exibir primeiros registros com estilo
        st.subheader("📋 Primeiros Registros de Cancelamento")
        st.dataframe(
            df_cancel.head(),
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.header("🚢 Análise de Navios")
        
        # Verificar se todos os navios têm o mesmo número de cancelamentos
        if contagem_navios['QuantidadeCancelamentos'].nunique() == 1:
            st.info("Todos os navios cancelados tiveram apenas 1 ocorrência no período analisado. Não há destaque para navios mais afetados.")
            st.dataframe(
                contagem_navios.head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            col1, col2 = st.columns([1.2, 1])
            with col1:
                st.subheader("🏆 Top 10 Navios com Mais Cancelamentos")
                st.dataframe(
                    contagem_navios.head(10),
                    use_container_width=True,
                    hide_index=True
                )
            with col2:
                # Gráfico de barras horizontal para melhor visualização
                fig = px.bar(
                    contagem_navios.head(5),
                    y='Navio',
                    x='QuantidadeCancelamentos',
                    orientation='h',
                    title='Top 5 Navios com Mais Cancelamentos',
                    color='QuantidadeCancelamentos',
                    color_continuous_scale='Viridis',
                    height=350
                )
                fig.update_layout(
                    xaxis_title="Quantidade de Cancelamentos",
                    yaxis_title="Navio",
                    showlegend=False,
                    margin=dict(l=60, r=20, t=50, b=40)
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
            
            # Parâmetros de custos
            CUSTOS = {
                "TEU":               1200.0,   # R$ / TEU (valor médio armadores Santos)
                "OPERACAO_PORTO":    1150.0,   # R$ fixo (taxa de cancelamento terminal)
                "DOCUMENTACAO":       950.0,   # R$ / operação (honorários despachante)
                "ARMAZENAGEM_DIA":    575.0,   # R$ / TEU / dia (armazenagem média)
                "ARMAZENAGEM_DIAS":      2,    # dias extras
                "INSPECAO":            95.0    # R$ / cont. (scanner/fitossanitária)
            }

            def calcular_custos(df: pd.DataFrame,
                              coluna_teu: str,
                              coluna_data: str | None = None) -> pd.DataFrame:
                """Adiciona colunas de custo e devolve cópia do dataframe."""
                df = df.copy()

                # TEUs numéricos
                df[coluna_teu] = pd.to_numeric(df[coluna_teu], errors="coerce").fillna(0)

                # Custos principais
                df["C_TEUS"]     = df[coluna_teu] * CUSTOS["TEU"]          # THC
                df["C_OPER"]     = CUSTOS["OPERACAO_PORTO"]                 # cancelamento terminal
                df["C_DOC"]      = CUSTOS["DOCUMENTACAO"]                   # despachante

                # Armazenagem (2 dias)
                df["C_ARM"]      = (
                    df[coluna_teu] * CUSTOS["ARMAZENAGEM_DIA"] * CUSTOS["ARMAZENAGEM_DIAS"]
                )

                # Inspeção
                df["C_INSP"]     = CUSTOS["INSPECAO"]                       # scanner/fitossanitária

                # Custo total
                colunas_custos = ["C_TEUS", "C_OPER", "C_DOC", "C_ARM", "C_INSP"]
                df["CUSTO_TOTAL"] = df[colunas_custos].sum(axis=1)

                return df

            if col_conteineres is not None:
                # Calcular custos
                df_cancel = calcular_custos(df_cancel, col_conteineres, col_data)

                # Métricas principais
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Custo Total Perdido",
                            f"R$ {df_cancel['CUSTO_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                with col2:
                    st.metric("Custo Médio por Cancelamento",
                            f"R$ {df_cancel['CUSTO_TOTAL'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                with col3:
                    st.metric("Total de TEUs Afetados",
                            f"{df_cancel[col_conteineres].sum():,.0f}".replace(",", "."))

                # Gráficos de distribuição e evolução temporal
                st.plotly_chart(
                    px.box(df_cancel, y="CUSTO_TOTAL",
                        title="Distribuição do Custo por Cancelamento",
                        labels={"CUSTO_TOTAL": "Custo Total (R$)"}),
                    use_container_width=True
                )

                if col_data is not None:
                    df_cancel["Mes"] = pd.to_datetime(df_cancel[col_data]).dt.to_period("M")
                    custos_mensais = (df_cancel.groupby("Mes")["CUSTO_TOTAL"]
                                    .sum()
                                    .reset_index()
                                    .assign(Mes=lambda d: d["Mes"].astype(str)))

                    custos_mensais["CUSTO_TOTAL"] = custos_mensais["CUSTO_TOTAL"].apply(lambda x: float(f"{x:.2f}"))

                    st.plotly_chart(
                        px.line(custos_mensais, x="Mes", y="CUSTO_TOTAL",
                                title="Evolução Mensal dos Custos", 
                                markers=True,
                                labels={"CUSTO_TOTAL": "Custo Total (R$)"}),
                        use_container_width=True
                    )

                # Detalhamento dos componentes de custo
                componentes = (
                    df_cancel[["C_TEUS", "C_OPER", "C_DOC", "C_ARM", "C_INSP"]]
                    .sum()
                    .rename(index={
                        "C_TEUS": "THC (Terminal Handling Charge)",
                        "C_OPER": "Taxa de Cancelamento",
                        "C_DOC":  "Honorários de Despacho",
                        "C_ARM":  "Armazenagem (2 dias)",
                        "C_INSP": "Scanner/Fitossanitária"
                    })
                    .reset_index()
                    .rename(columns={"index": "Tipo de Custo", 0: "Valor Total (BRL)"})
                )

                # Formatar valores monetários na tabela de componentes (apenas para exibição)
                componentes_formatado = componentes.copy()
                componentes_formatado["Valor Total (BRL)"] = componentes_formatado["Valor Total (BRL)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                # Adicionar detalhes dos custos
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
                    st.dataframe(componentes_formatado, hide_index=True, use_container_width=True)
                with col2:
                    st.plotly_chart(
                        px.pie(componentes, values="Valor Total (BRL)",
                            names="Tipo de Custo",
                            title="Distribuição dos Custos"),
                        use_container_width=True
                    )

                # Análise por armador (se disponível)
                if col_armador is not None:
                    st.subheader("Análise de Custos por Armador")
                    custos_por_armador = (df_cancel.groupby(col_armador)["CUSTO_TOTAL"]
                                        .agg(['sum', 'mean', 'count'])
                                        .reset_index()
                                        .rename(columns={
                                            'sum': 'Custo Total',
                                            'mean': 'Custo Médio',
                                            'count': 'Quantidade'
                                        })
                                        .sort_values('Custo Total', ascending=False))

                    # Formatar valores monetários
                    custos_por_armador['Custo Total'] = custos_por_armador['Custo Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    custos_por_armador['Custo Médio'] = custos_por_armador['Custo Médio'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Top 10 Armadores por Custo Total:")
                        st.dataframe(
                            custos_por_armador.head(10),
                            use_container_width=True,
                            hide_index=True
                        )

                    with col2:
                        # Para o gráfico, remover o R$ e converter para float
                        custos_por_armador_graf = custos_por_armador.head(10).copy()
                        custos_por_armador_graf['Custo Total'] = custos_por_armador_graf['Custo Total'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').astype(float)
                        fig = px.bar(
                            custos_por_armador_graf,
                            x=col_armador,
                            y='Custo Total',
                            title='Top 10 Armadores por Custo Total',
                            color='Custo Total',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(
                            xaxis_title="Armador",
                            yaxis_title="Custo Total (BRL)",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("⚠️ Coluna de contêineres não encontrada nos dados. Não é possível calcular os custos.")

else:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel para começar a análise.") 