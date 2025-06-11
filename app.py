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

# Configuração da página
st.set_page_config(
    page_title="Análise de Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide"
)

# Título e descrição
st.title("📊 Análise de Levantamentos de Cancelamentos de Navios")
st.markdown("""
Este aplicativo analisa dados de cancelamentos de navios, fornecendo insights sobre:
- Navios mais cancelados
- Motivos de cancelamento
- Análise temporal
- Rotas mais impactadas
- E muito mais!
""")

# Upload do arquivo
uploaded_file = st.file_uploader("Faça o upload do arquivo Excel", type=["xlsx"])

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
        st.header("Visão Geral dos Cancelamentos")
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros", len(df))
        with col2:
            st.metric("Total de Cancelamentos", len(df_cancel))
        with col3:
            st.metric("Taxa de Cancelamento", f"{(len(df_cancel)/len(df)*100):.1f}%")

        # Exibir primeiros registros
        st.subheader("Primeiros Registros de Cancelamento")
        st.dataframe(df_cancel.head())

    with tab2:
        st.header("Análise de Navios")
        
        # Top 10 navios mais cancelados
        contagem_navios = df_cancel[col_navio].value_counts().reset_index()
        contagem_navios.columns = ['Navio', 'QuantidadeCancelamentos']
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 Navios com Mais Cancelamentos")
            st.dataframe(contagem_navios.head(10))
        
        with col2:
            fig, ax = plt.subplots(figsize=(10, 6))
            top5_navios = contagem_navios.head(5)
            ax.bar(top5_navios['Navio'], top5_navios['QuantidadeCancelamentos'])
            ax.set_title('Top 5 Navios com Mais Cancelamentos')
            ax.set_xlabel('Navio')
            ax.set_ylabel('Quantidade de Cancelamentos')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)

    with tab3:
        st.header("Análise Temporal")
        
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
            st.subheader("Cancelamentos por Mês")
            st.dataframe(contagem_mensal)
        
        with col2:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(contagem_mensal['Y-M'], contagem_mensal['Cancelamentos'], marker='o')
            ax.set_title('Cancelamentos Mensais de Navios')
            ax.set_xlabel('Mês')
            ax.set_ylabel('Número de Cancelamentos')
            plt.xticks(rotation=45)
            ax.grid(True)
            st.pyplot(fig)

    with tab4:
        st.header("Análise de Rotas")
        
        if col_rota is not None:
            contagem_rotas = df_cancel[col_rota].value_counts().reset_index()
            contagem_rotas.columns = ['Rota', 'Cancelamentos']
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 10 Rotas com Mais Cancelamentos")
                st.dataframe(contagem_rotas.head(10))
            
            with col2:
                fig, ax = plt.subplots(figsize=(12, 6))
                top5_rotas = contagem_rotas.head(5)
                ax.bar(top5_rotas['Rota'], top5_rotas['Cancelamentos'])
                ax.set_title('Top 5 Rotas com Mais Cancelamentos')
                ax.set_xlabel('Rota')
                ax.set_ylabel('Quantidade de Cancelamentos')
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)

    with tab5:
        st.header("Análises Adicionais")
        
        # Criar subabas para análises adicionais
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["Tipo de Navio", "Contêineres", "Outros"])
        
        with sub_tab1:
            if col_tipo_navio is not None:
                df_cancel[col_tipo_navio] = df_cancel[col_tipo_navio].astype(str).str.strip().str.capitalize()
                contagem_tipo_navio = df_cancel[col_tipo_navio].value_counts().reset_index()
                contagem_tipo_navio.columns = ['TipoNavio', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Distribuição por Tipo de Navio")
                    st.dataframe(contagem_tipo_navio)
                
                with col2:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    top5_tipo_navio = contagem_tipo_navio.head(5)
                    ax.bar(top5_tipo_navio['TipoNavio'], top5_tipo_navio['Cancelamentos'])
                    ax.set_title('Top 5 Tipos de Navio com Mais Cancelamentos')
                    ax.set_xlabel('Tipo de Navio')
                    ax.set_ylabel('Quantidade de Cancelamentos')
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)
        
        with sub_tab2:
            if col_conteineres is not None:
                df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce')
                df_cancel_conteineres = df_cancel.dropna(subset=[col_conteineres])
                
                if len(df_cancel_conteineres) > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Estatísticas de Contêineres")
                        st.write(df_cancel_conteineres[col_conteineres].describe())
                    
                    with col2:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.hist(df_cancel_conteineres[col_conteineres], bins=20, edgecolor='black')
                        ax.set_title('Distribuição da Quantidade de Contêineres')
                        ax.set_xlabel('Quantidade de Contêineres')
                        ax.set_ylabel('Frequência')
                        st.pyplot(fig)
        
        with sub_tab3:
            # Análise por Armador
            col_armador = 'Armador' if 'Armador' in df_cancel.columns else None
            if col_armador is not None:
                st.subheader("Análise por Armador")
                df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip().str.capitalize()
                contagem_armadores = df_cancel[col_armador].value_counts().reset_index()
                contagem_armadores.columns = ['Armador', 'Cancelamentos']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(contagem_armadores.head(10))
                
                with col2:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    top5_armadores = contagem_armadores.head(5)
                    ax.bar(top5_armadores['Armador'], top5_armadores['Cancelamentos'])
                    ax.set_title('Top 5 Armadores com Mais Cancelamentos')
                    ax.set_xlabel('Armador')
                    ax.set_ylabel('Quantidade de Cancelamentos')
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)

    # Resumo final
    st.sidebar.header("Resumo dos Resultados")
    st.sidebar.write(f"Total de cancelamentos analisados: {len(df_cancel)}")
    if len(contagem_navios) > 0:
        st.sidebar.write(f"Navio mais cancelado: {contagem_navios.iloc[0]['Navio']} ({contagem_navios.iloc[0]['QuantidadeCancelamentos']} vezes)")
    if len(contagem_mensal) > 0:
        max_mes = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        st.sidebar.write(f"Mês com mais cancelamentos: {max_mes['Y-M'].strftime('%Y-%m')} ({int(max_mes['Cancelamentos'])} cancelamentos)")

else:
    st.warning("Por favor, faça o upload do arquivo Excel para começar a análise.") 