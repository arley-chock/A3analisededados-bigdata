import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- CSS Base ---
st.markdown("""
<style>
    /* Container principal */
    .main .block-container { padding: 2rem; max-width: 1400px; }
    /* Cards */
    .card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    /* Cabeçalho */
    .header { text-align: center; margin-bottom: 2rem; }
    .header h1 { margin: 0; font-size: 2.5rem; }
    .header p { font-size: 1.1rem; color: #ddd; }
    /* Sidebar Expanders */
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

# --- Sidebar com Expanders ---
with st.sidebar:
    with st.expander("📁 Upload e Filtros", expanded=True):
        uploaded_file = st.file_uploader("Faça o upload do Excel", type=["xlsx"])
        termo = st.text_input("Pesquisar por navio, armador ou rota")
        modelo = st.selectbox("Modelo de Relatório", ["Análise Completa","Análise de Custos","Por Armador","Temporal"])
        if st.button("Aplicar"):
            st.session_state.termo = termo
            st.session_state.modelo = modelo

    with st.expander("📋 Sobre o Projeto", expanded=False):
        st.markdown("""
        - **Arley do Nascimento Vinagre**  
        - **Vinicius Santana**  
        - **Tauan Santos Santana**  

        Projeto acadêmico sobre dados de portos e navios cancelados.
        """)

    with st.expander("💰 Tabela de Custos", expanded=False):
        st.markdown("""
        - **THC:** R$ 1.200,00 / TEU  
        - **Armazenagem:** R$ 575,00 / TEU / dia × 2 dias  
        - **Despachante:** R$ 950,00  
        - **Scanner:** R$ 95,00 / contêiner  
        - **Câmbio:** R$ 5,10 / US$
        """)

# --- Lógica de Leitura e Processamento ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Detectar colunas principais
    col_status  = 'Situação' if 'Situação' in df.columns else None
    col_data    = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
    col_navio   = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None
    col_movs    = 'Movs' if 'Movs' in df.columns else None
    col_armador = 'Armador' if 'Armador' in df.columns else None
    col_rota    = 'De / Para' if 'De / Para' in df.columns else None
    col_tipo    = 'Tipo' if 'Tipo' in df.columns else None

    # Filtrar apenas cancelamentos
    valores_cancelados = ['cancelado','cancelada','rejeitado','rej.','canceled']
    if col_status:
        df[col_status] = (df[col_status].astype(str)
                              .str.strip()
                              .str.lower())
        mask = df[col_status].isin(valores_cancelados)
        df_cancel = df.loc[mask].copy()
    else:
        df_cancel = pd.DataFrame(columns=df.columns)

    # Converter tipos
    if col_data:
        df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
    if col_movs:
        df_cancel[col_movs] = pd.to_numeric(df_cancel[col_movs], errors='coerce').fillna(0)

    # Preparar análise temporal mensal
    df_cancel_valid = df_cancel.dropna(subset=[col_data])
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
            names=["Cancelados", "Não Cancelados"],
            values=[len(df_cancel), len(df) - len(df_cancel)],
            title="Cancelados vs Não Cancelados"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Por Navio
    with tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Top 10 Navios com Mais Cancelamentos")
        st.dataframe(top_navios.head(10), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Temporal
    with tabs[2]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Evolução Mensal de Cancelamentos")
        st.dataframe(
            contagem_mensal[['Y-M','Cancelamentos']].rename(columns={'Y-M':'Mês'}),
            use_container_width=True, hide_index=True
        )
        fig = px.line(
            contagem_mensal,
            x='Y-M', y='Cancelamentos',
            title="Cancelamentos por Mês",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Rotas
    with tabs[3]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Top 10 Rotas com Mais Cancelamentos")
        st.dataframe(top_rotas.head(10), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Custos
    with tabs[4]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Análise de Custos de Cancelamento")

        # Parâmetros de custo
        CUSTOS = {
            "TEU":            1200.0,    # R$ / TEU
            "OPERACAO_PORTO": 1150.0,    # R$ / operação
            "DOCUMENTACAO":   950.0,     # R$ / operação
            "ARMAZENAGEM_DIA":575.0,     # R$ / TEU / dia
            "ARMAZENAGEM_DIAS":2,        # dias
            "INSPECAO":       95.0       # R$ / contêiner
        }

        def calcular_custos(df, coluna_teu):
            df = df.copy()
            df[coluna_teu] = pd.to_numeric(df[coluna_teu], errors="coerce").fillna(0)
            df["C_TEUS"] = df[coluna_teu] * CUSTOS["TEU"]
            df["C_OPER"] = CUSTOS["OPERACAO_PORTO"]
            df["C_DOC"]  = CUSTOS["DOCUMENTACAO"]
            df["C_ARM"]  = df[coluna_teu] * CUSTOS["ARMAZENAGEM_DIA"] * CUSTOS["ARMAZENAGEM_DIAS"]
            df["C_INSP"]= CUSTOS["INSPECAO"]
            df["CUSTO_TOTAL"] = df[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
            return df

        if col_movs:
            df_cancel = calcular_custos(df_cancel, col_movs)

            # Métricas de custo
            total_perdido = df_cancel["CUSTO_TOTAL"].sum()
            medio = df_cancel["CUSTO_TOTAL"].mean()
            total_teus = df_cancel[col_movs].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Custo Total Perdido (R$)", f"{total_perdido:,.2f}")
            c2.metric("Custo Médio por Cancelamento (R$)", f"{medio:,.2f}")
            c3.metric("Total de TEUs Afetados", f"{int(total_teus):,}")

            # Distribuição de custo
            fig_box = px.box(df_cancel, y="CUSTO_TOTAL",
                             title="Distribuição do Custo por Cancelamento")
            st.plotly_chart(fig_box, use_container_width=True)

            # Evolução mensal de custo
            if col_data:
                df_cancel["Mes"] = df_cancel[col_data].dt.to_period("M").astype(str)
                custos_mensais = (
                    df_cancel.groupby("Mes")["CUSTO_TOTAL"]
                    .sum().reset_index()
                )
                fig_line = px.line(
                    custos_mensais, x="Mes", y="CUSTO_TOTAL",
                    title="Evolução Mensal dos Custos",
                    markers=True
                )
                st.plotly_chart(fig_line, use_container_width=True)

            # Detalhamento por componente
            componentes = (
                df_cancel[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]]
                .sum()
                .rename(index={
                    "C_TEUS":"THC (R$ / TEU)",
                    "C_OPER":"Taxa de Operação (R$)",
                    "C_DOC":"Despachante (R$)",
                    "C_ARM":"Armazenagem (R$)",
                    "C_INSP":"Inspeção (R$)"
                })
                .reset_index()
                .rename(columns={"index":"Tipo de Custo", 0:"Valor Total (R$)"})
            )

            # Tabela e pizza
            comp1, comp2 = st.columns(2)
            comp1.dataframe(componentes, use_container_width=True, hide_index=True)
            fig_pie = px.pie(
                componentes, names="Tipo de Custo", values="Valor Total (R$)",
                title="Distribuição dos Componentes de Custo"
            )
            comp2.plotly_chart(fig_pie, use_container_width=True)

            # Custo por armador
            if col_armador:
                st.subheader("Top 10 Armadores por Custo Total")
                custos_arm = (
                    df_cancel.groupby(col_armador)["CUSTO_TOTAL"]
                    .agg(['sum','mean','count'])
                    .reset_index()
                    .rename(columns={'sum':'Custo Total','mean':'Custo Médio','count':'Qtde'})
                    .sort_values('Custo Total', ascending=False)
                )
                custos_arm['Custo Total'] = custos_arm['Custo Total'].map(lambda x: f"{x:,.2f}")
                custos_arm['Custo Médio'] = custos_arm['Custo Médio'].map(lambda x: f"{x:,.2f}")

                arm1, arm2 = st.columns(2)
                arm1.dataframe(custos_arm.head(10), use_container_width=True, hide_index=True)
                # gráfico
                df_plot = custos_arm.head(10).copy()
                df_plot['Custo Total'] = df_plot['Custo Total'].str.replace(',','').astype(float)
                fig_bar = px.bar(
                    df_plot, x=col_armador, y='Custo Total',
                    title="Custo Total por Armador"
                )
                arm2.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.warning("⚠️ Por favor, faça o upload do arquivo Excel para começar a análise.")
