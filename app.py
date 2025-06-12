import streamlit as st
import pandas as pd
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
        padding: 1.2rem;
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
        termo   = st.text_input("🔍 Pesquisar por navio, armador ou rota")
        modelo  = st.selectbox("📋 Modelo de Relatório", ["Análise Completa","Análise de Custos","Por Armador","Temporal"])
        if st.button("Aplicar"):
            st.session_state.termo  = termo
            st.session_state.modelo = modelo

    with st.expander("📋 Sobre o Projeto", expanded=False):
        st.markdown("""
        - **Arley do Nascimento Vinagre**  
        - **Vinicius Santana**  
        - **Tauan Santos Santana**  

        Projeto acadêmico de análise de cancelamentos de navios.
        """)

    with st.expander("💰 Tabela de Custos", expanded=False):
        st.markdown("""
        - **THC:** R$ 1.200,00 / TEU  
        - **Armazenagem:** R$ 575,00 / TEU / dia × 2 dias  
        - **Despachante:** R$ 950,00  
        - **Scanner:** R$ 95,00 / contêiner  
        - **Câmbio:** R$ 5,10 / US$
        """)

# --- Leitura e Processamento ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Detectar colunas
    col_status  = 'Situação'                 if 'Situação' in df.columns else None
    col_eta     = 'Estimativa Chegada ETA'   if 'Estimativa Chegada ETA' in df.columns else None
    col_navio   = 'Navio / Viagem'           if 'Navio / Viagem' in df.columns else None
    col_movs    = 'Movs'                     if 'Movs' in df.columns else None
    col_armador = 'Armador'                  if 'Armador' in df.columns else None
    col_rota    = 'De / Para'                if 'De / Para' in df.columns else None

    # Filtrar apenas cancelamentos
    valores_cancelados = ['cancelado','cancelada','rejeitado','rej.','canceled']
    if col_status:
        df[col_status] = (df[col_status].astype(str)
                              .str.strip()
                              .str.lower())
        df_cancel = df[df[col_status].isin(valores_cancelados)].copy()
    else:
        df_cancel = pd.DataFrame(columns=df.columns)

    # Converter colunas
    if col_eta:
        df_cancel[col_eta] = pd.to_datetime(df_cancel[col_eta], dayfirst=True, errors='coerce')
    if col_movs:
        df_cancel[col_movs] = pd.to_numeric(df_cancel[col_movs], errors='coerce').fillna(0)

    # Análise temporal mensal
    df_temp = df_cancel.dropna(subset=[col_eta]) if col_eta else df_cancel.copy()
    if col_eta:
        df_temp['Y-M'] = df_temp[col_eta].dt.to_period('M').astype(str)
        contagem_mensal = (
            df_temp.groupby('Y-M').size()
                   .reset_index(name='Cancelamentos')
                   .assign(_dt=lambda d: pd.to_datetime(d['Y-M'], format='%Y-%m'))
                   .sort_values('_dt')
        )
    else:
        contagem_mensal = pd.DataFrame(columns=['Y-M','Cancelamentos'])

    # Rankings
    top_navios = (df_cancel[col_navio]
                  .value_counts()
                  .rename_axis('Navio')
                  .reset_index(name='Quantidade'))
    top_rotas  = (df_cancel[col_rota]
                  .value_counts()
                  .rename_axis('Rota')
                  .reset_index(name='Cancelamentos'))

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4, gap="large")
    k1.metric("Total de Registros", f"{len(df):,}")
    k2.metric("Total Cancelamentos", f"{len(df_cancel):,}", delta=f"{(len(df_cancel)/len(df)*100):.1f}%")
    k3.metric("TEUs Afetados", f"{int(df_cancel[col_movs].sum()):,}" if col_movs else "—")
    if not contagem_mensal.empty:
        best = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
        k4.metric("Mês com Mais Cancel.", best['Y-M'], delta=f"{int(best['Cancelamentos'])} vezes")
    else:
        k4.metric("Mês com Mais Cancel.", "—")

    # --- Abas ---
    tabs = st.tabs([
        "📈 Visão Geral",
        "🚢 Análise de Navios",
        "📅 Análise Temporal",
        "🌍 Análise de Rotas",
        "💰 Análise de Custos"
    ])

    # Visão Geral
    with tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Distribuição de Status")
        fig = px.pie(
            names=["Cancelados","Não Cancelados"],
            values=[len(df_cancel), len(df)-len(df_cancel)],
            title="Cancelamentos vs Não Cancelados"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Navios
    with tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Top Navios com Mais Cancelamentos")
        if top_navios['Quantidade'].nunique() == 1:
            st.info("Todos os navios cancelados registraram apenas 1 ocorrência neste período.")
            st.dataframe(top_navios.head(10), use_container_width=True, hide_index=True)
        else:
            st.dataframe(top_navios.head(10), use_container_width=True, hide_index=True)
            fig = px.bar(
                top_navios.head(5),
                x='Quantidade', y='Navio',
                orientation='h',
                title='Top 5 Navios',
                color='Quantidade'
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise Temporal
    with tabs[2]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Evolução Mensal de Cancelamentos")
        if not contagem_mensal.empty:
            st.dataframe(
                contagem_mensal[['Y-M','Cancelamentos']]
                .rename(columns={'Y-M':'Mês'}),
                use_container_width=True, hide_index=True
            )
            fig = px.line(
                contagem_mensal, x='Y-M', y='Cancelamentos',
                title="Cancelamentos por Mês", markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não há dados de data para análise temporal.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Rotas
    with tabs[3]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Top 10 Rotas com Mais Cancelamentos")
        if not top_rotas.empty:
            st.dataframe(top_rotas.head(10), use_container_width=True, hide_index=True)
            fig = px.bar(
                top_rotas.head(5),
                x='Rota', y='Cancelamentos',
                title='Top 5 Rotas', color='Cancelamentos'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Coluna de rotas não encontrada ou sem dados.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Custos
    with tabs[4]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Custos de Cancelamento")

        # Definir custos
        C = {
            "TEU":            1200.0,
            "OPER":           1150.0,
            "DOC":            950.0,
            "ARM_DIA":        575.0,
            "ARM_DIAS":       2,
            "INSP":           95.0
        }
        def calcular_custos(df, teu_col):
            df = df.copy()
            df[teu_col] = pd.to_numeric(df[teu_col], errors="coerce").fillna(0)
            df["C_TEU"]  = df[teu_col] * C["TEU"]
            df["C_OPER"] = C["OPER"]
            df["C_DOC"]  = C["DOC"]
            df["C_ARM"]  = df[teu_col] * C["ARM_DIA"] * C["ARM_DIAS"]
            df["C_INSP"]= C["INSP"]
            df["C_TOTAL"] = df[["C_TEU","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)
            return df

        if col_movs:
            df_cancel = calcular_custos(df_cancel, col_movs)
            total_cost = df_cancel["C_TOTAL"].sum()
            avg_cost   = df_cancel["C_TOTAL"].mean()
            teus_sum   = df_cancel[col_movs].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Custo Total (R$)", f"{total_cost:,.2f}")
            c2.metric("Custo Médio (R$)", f"{avg_cost:,.2f}")
            c3.metric("TEUs Afetados", f"{int(teus_sum):,}")

            fig_box = px.box(df_cancel, y="C_TOTAL", title="Distribuição de Custos")
            st.plotly_chart(fig_box, use_container_width=True)

            if col_eta:
                df_cancel["Mes"] = df_cancel[col_eta].dt.to_period("M").astype(str)
                monthly = df_cancel.groupby("Mes")["C_TOTAL"].sum().reset_index()
                fig_line = px.line(
                    monthly, x="Mes", y="C_TOTAL",
                    title="Evolução Mensal de Custos", markers=True
                )
                st.plotly_chart(fig_line, use_container_width=True)

        else:
            st.warning("Coluna de TEU (Movs) não encontrada; não é possível calcular custos.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.warning("⚠️ Faça o upload do arquivo Excel para começar a análise.")
