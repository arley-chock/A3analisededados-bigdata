"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Projeto acadêmico por:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana (1272221567)
- Tauan Santos Santana (12722216126)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Referências de custos (valores 2024-25)
REFERENCIAS_CUSTOS = {
    'THC': 1200.00,            # R$ por TEU
    'TAXA_TERMINAL': 1150.00,  # R$ por operação de cancelamento
    'DESPACHANTE': 950.00,     # R$ fixo por operação
    'ARMAZENAGEM': 575.00,     # R$ por TEU/dia
    'DIAS_ARMAZENAGEM': 2,     # dias de armazenagem padrão
    'SCANNER': 95.00,          # R$ por contêiner (scanner/fitossanitária)
    'CAMBIO': 5.10             # R$/US$
}

def ajustar_layout_grafico(fig, altura=500):
    """Aplica estilo uniforme a figuras Plotly."""
    fig.update_layout(
        height=altura,
        margin=dict(l=40, r=40, t=50, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# Configuração da página
st.set_page_config(
    page_title="🚢 Análise de Cancelamentos de Navios",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==== SIDEBAR: Pesquisa e Modelos ====
with st.sidebar:
    st.markdown("### 🔍 Pesquisa e Modelos")
    termo_pesquisa = st.text_input("Pesquisar por navio, armador ou rota")
    modelo_selecionado = st.selectbox(
        "📋 Modelos de Relatório",
        ["Análise Completa", "Análise de Custos", "Análise por Armador", "Análise Temporal"]
    )
    if st.button("Aplicar Modelo"):
        st.session_state['termo_pesquisa'] = termo_pesquisa
        st.session_state['modelo_atual']  = modelo_selecionado

# ==== CSS Personalizado ====
st.markdown("""
<style>
    .main { padding: 2rem; max-width: 1400px; margin: 0 auto; }
    .js-plotly-plot { margin: 1rem 0; padding: 1rem; background: rgba(255,255,255,0.07); border-radius: 12px; }
    .stContainer { margin: 1rem 0; padding: 1rem; }
    [data-testid="column"] { padding: 0 1rem; }
    .stMetric { margin: 1rem 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; margin-bottom: 1.5rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.8rem 1.5rem; margin-right: 0.5rem; }
    .dashboard-card { margin: 1.5rem 0; padding: 1.5rem; }
    @media (max-width: 1200px) {
        .main { padding: 1rem; }
        [data-testid="column"] { padding: 0 0.5rem; }
    }
    @media (max-width: 768px) {
        .main { padding: 0.5rem; }
        .stTabs [data-baseweb="tab"] { padding: 0.6rem 1rem; font-size: 0.9rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==== CABEÇALHO ====
st.markdown("""
<div class='dashboard-card' style='text-align:center;'>
  <h1>🚢 Análise de Cancelamentos de Navios</h1>
  <p>Dashboard interativo para investigar ocorrências de cancelamentos, custos e métricas operacionais.</p>
</div>
""", unsafe_allow_html=True)

# ==== SOBRE O PROJETO ====
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; margin-bottom:1rem;'>
        <img src='https://img.icons8.com/color/96/000000/cruise-ship.png' width='80'/>
        <h3>Sobre o Projeto</h3>
        <p>Dashboard desenvolvido como projeto acadêmico.</p>
        <ul style='list-style:none; padding-left:0; text-align:left;'>
          <li>👤 Arley do Nascimento Vinagre</li>
          <li>👤 Vinicius Santana</li>
          <li>👤 Tauan Santos Santana</li>
        </ul>
    </div>
    <hr/>
    <div style='padding:0.7rem; background:rgba(255,255,255,0.07); border-radius:8px;'>
      <h4>💰 Referências de Custos</h4>
      <ul style='font-size:0.9rem; padding-left:1rem;'>
        <li>THC: R$ 1.200,00 / TEU</li>
        <li>Taxa Terminal: R$ 1.150,00 / op.</li>
        <li>Despachante: R$ 950,00 / op.</li>
        <li>Armazenagem: R$ 575,00 / TEU / dia × 2 dias</li>
        <li>Scanner: R$ 95,00 / contêiner</li>
        <li>Câmbio médio: R$ 5,10 / US$</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

# ==== UPLOAD DO ARQUIVO ====
uploaded_file = st.file_uploader("📁 Faça o upload do arquivo Excel", type=["xlsx"])
if not uploaded_file:
    st.warning("Por favor, faça o upload do arquivo Excel para continuar.")
    st.stop()

# ==== LEITURA DOS DADOS ====
df = pd.read_excel(uploaded_file)
logger.info(f"Colunas encontradas: {df.columns.tolist()}")

# ==== DETECÇÃO DAS COLUNAS PRINCIPAIS ====
# Código vs. nome do navio
col_navio_code = 'Navio / Viagem'    if 'Navio / Viagem'    in df.columns else None
col_navio_name = 'Navio / Viagem.1'  if 'Navio / Viagem.1'  in df.columns else None
col_navio      = col_navio_name or col_navio_code

col_status     = 'Situação'          if 'Situação'          in df.columns else None
col_eta        = 'Estimativa Chegada ETA'   if 'Estimativa Chegada ETA'   in df.columns else None
col_etb        = 'Estimativa Atracação ETB' if 'Estimativa Atracação ETB' in df.columns else None
col_etd        = 'Estimativa Saída ETD'     if 'Estimativa Saída ETD'     in df.columns else None
col_movs       = 'Movs'             if 'Movs'              in df.columns else None
col_rota       = 'De / Para'        if 'De / Para'         in df.columns else None
col_armador    = 'Armador'          if 'Armador'           in df.columns else None
col_berco      = 'Berço'            if 'Berço'             in df.columns else None
col_servico    = 'Serviço'          if 'Serviço'           in df.columns else None
col_pais       = 'País'             if 'País'              in df.columns else None
col_tipo_navio = 'Tipo'             if 'Tipo'              in df.columns else None
col_inicio_op  = 'Início Operação'  if 'Início Operação'   in df.columns else None
col_fim_op     = 'Fim Operação'     if 'Fim Operação'      in df.columns else None

# ==== APLICAÇÃO DO FILTRO DE PESQUISA ====
df_filtered = df.copy()
termo = st.session_state.get('termo_pesquisa', '').strip().lower()
if termo:
    mask = pd.Series(False, index=df.index)
    if col_navio:   mask |= df[col_navio].astype(str).str.lower().str.contains(termo, na=False)
    if col_armador: mask |= df[col_armador].astype(str).str.lower().str.contains(termo, na=False)
    if col_rota:    mask |= df[col_rota].astype(str).str.lower().str.contains(termo, na=False)
    df_filtered = df.loc[mask].copy()

# ==== FILTRAGEM DE REGISTROS CANCELADOS ====
if not col_status:
    st.error("Coluna de status ('Situação') não encontrada no arquivo.")
    st.stop()

df_filtered[col_status] = (
    df_filtered[col_status]
    .astype(str)
    .str.strip()
    .str.lower()
)
mask_cancel = df_filtered[col_status].isin([v.lower() for v in REFERENCIAS_CUSTOS.keys()] + ['cancelado','cancelada','rejeitado','rej.','canceled'])
df_cancel = df_filtered.loc[mask_cancel].copy()

# Conversão de colunas numéricas
if col_movs:
    df_cancel[col_movs] = (
        pd.to_numeric(df_cancel[col_movs], errors='coerce')
        .fillna(0)
        .astype(int)
    )

# Conversão de datas
if col_eta:
    df_cancel[col_eta] = pd.to_datetime(df_cancel[col_eta], dayfirst=True, errors='coerce')

# ==== RESUMO PARA SIDEBAR ====
with st.sidebar:
    st.markdown("### 📊 Resumo dos Resultados")
    total_cancel = len(df_cancel)
    total_reg    = len(df)
    taxa_cancel  = (total_cancel/total_reg*100) if total_reg else 0
    st.markdown(f"- **Total de registros:** {total_reg:,}")
    st.markdown(f"- **Total de cancelamentos:** {total_cancel:,}")
    st.markdown(f"- **Taxa de cancelamento:** {taxa_cancel:.1f}%")
    # Navio mais cancelado
    if col_navio and not df_cancel.empty:
        top_navio = (
            df_cancel[col_navio]
            .value_counts()
            .idxmax()
        )
        cont_navio = df_cancel[col_navio].value_counts().max()
        st.markdown(f"- **Navio mais cancelado:** {top_navio} ({cont_navio} vezes)")
    # Mês com mais cancelamentos
    if col_eta and not df_cancel.empty:
        df_temp = df_cancel.dropna(subset=[col_eta]).copy()
        df_temp['Y-M'] = df_temp[col_eta].dt.to_period('M')
        mes_top = df_temp['Y-M'].value_counts().idxmax()
        qtd_mes = df_temp['Y-M'].value_counts().max()
        st.markdown(f"- **Mês com mais cancelamentos:** {mes_top} ({qtd_mes} cancel.)")

# ==== PREPARAÇÃO DE DADOS PARA ANÁLISE TEMPORAL E POR NAVIO ====
# Contagem por navio
if col_navio:
    contagem_navios = (
        df_cancel[col_navio]
        .value_counts()
        .reset_index()
        .rename(columns={'index': 'Navio', col_navio: 'QuantidadeCancelamentos'})
    )
else:
    contagem_navios = pd.DataFrame(columns=['Navio','QuantidadeCancelamentos'])

# Contagem mensal
if col_eta:
    df_tm = df_cancel.dropna(subset=[col_eta]).copy()
    df_tm['Y-M'] = df_tm[col_eta].dt.to_period('M').astype(str)
    contagem_mensal = (
        df_tm.groupby('Y-M')
        .size()
        .reset_index(name='Cancelamentos')
    )
    contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
    contagem_mensal = contagem_mensal.sort_values('Y-M')
else:
    contagem_mensal = pd.DataFrame(columns=['Y-M','Cancelamentos'])

# ==== TABS PRINCIPAIS ====
tabs = st.tabs([
    "📈 Visão Geral",
    "🚢 Análise de Navios",
    "📅 Análise Temporal",
    "🌍 Análise de Rotas",
    "📊 Outras Análises",
    "💰 Análise de Custos"
])

# --- Visão Geral ---
with tabs[0]:
    st.header("📊 Visão Geral dos Cancelamentos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Registros", f"{total_reg:,}")
    col2.metric("Total Cancelamentos", f"{total_cancel:,}", delta=f"{taxa_cancel:.1f}%")
    avg_diario = (total_cancel/30) if total_cancel else 0
    col3.metric("Média Diária", f"{avg_diario:.1f}")
    # Pizza de cancelados x não cancelados
    fig_pie = px.pie(
        names=['Cancelados','Não Cancelados'],
        values=[total_cancel, total_reg-total_cancel],
        title="Distribuição de Cancelamentos"
    )
    st.plotly_chart(ajustar_layout_grafico(fig_pie, altura=350), use_container_width=True)
    # Mostra os primeiros registros cancelados
    st.subheader("📋 Primeiros Registros de Cancelamento")
    st.dataframe(df_cancel.head().reset_index(drop=True), use_container_width=True)

# --- Análise de Navios ---
with tabs[1]:
    st.header("🚢 Análise de Navios")
    if contagem_navios['QuantidadeCancelamentos'].nunique()==1:
        st.info("Todos os navios cancelados tiveram apenas 1 ocorrência no período.")
        st.dataframe(contagem_navios.head(10), use_container_width=True)
    else:
        st.subheader("Top 10 Navios com Mais Cancelamentos")
        st.dataframe(contagem_navios.head(10), use_container_width=True)
        fig_bar = px.bar(
            contagem_navios.head(5),
            x='QuantidadeCancelamentos',
            y='Navio',
            orientation='h',
            title="Top 5 Navios",
            color='QuantidadeCancelamentos'
        )
        st.plotly_chart(ajustar_layout_grafico(fig_bar, altura=350), use_container_width=True)

# --- Análise Temporal ---
with tabs[2]:
    st.header("📅 Análise Temporal")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cancelamentos por Mês")
        st.dataframe(
            contagem_mensal.assign(**{'Mês':contagem_mensal['Y-M'].dt.strftime('%Y-%m')})
            [['Mês','Cancelamentos']],
            use_container_width=True
        )
    with col2:
        fig_line = px.line(
            contagem_mensal,
            x='Y-M', y='Cancelamentos',
            title="Evolução Mensal de Cancelamentos",
            markers=True
        )
        st.plotly_chart(ajustar_layout_grafico(fig_line), use_container_width=True)

# --- Análise de Rotas ---
with tabs[3]:
    st.header("🌍 Análise de Rotas")
    if col_rota:
        contagem_rotas = (
            df_cancel[col_rota]
            .value_counts()
            .reset_index()
            .rename(columns={'index':'Rota', col_rota:'Cancelamentos'})
        )
        st.subheader("Top 10 Rotas com Mais Cancelamentos")
        st.dataframe(contagem_rotas.head(10), use_container_width=True)
        fig_rt = px.bar(
            contagem_rotas.head(5),
            x='Rota', y='Cancelamentos',
            title="Top 5 Rotas",
            color='Cancelamentos'
        )
        st.plotly_chart(ajustar_layout_grafico(fig_rt), use_container_width=True)
    else:
        st.warning("Coluna 'De / Para' não encontrada.")

# --- Outras Análises ---
with tabs[4]:
    st.header("📊 Outras Análises")
    sub1, sub2, sub3 = st.tabs(["🏢 Por Armador","📦 Contêineres","⏱️ Tempo de Permanência"])
    # Análise por Armador
    with sub1:
        st.subheader("Por Armador")
        if col_armador:
            cnt_arm = (
                df_cancel[col_armador]
                .fillna("Não Informado")
                .value_counts()
                .reset_index()
                .rename(columns={'index':'Armador', col_armador:'Cancelamentos'})
            )
            st.dataframe(cnt_arm.head(10), use_container_width=True)
            fig_arm = px.bar(cnt_arm.head(5), x='Armador', y='Cancelamentos', title="Top 5 Armadores", color='Cancelamentos')
            st.plotly_chart(ajustar_layout_grafico(fig_arm), use_container_width=True)
        else:
            st.warning("Coluna 'Armador' não encontrada.")
    # Análise de Contêineres
    with sub2:
        st.subheader("Distribuição de Contêineres")
        if col_movs:
            stats = df_cancel[col_movs].describe().reset_index().rename(columns={'index':'Estatística', col_movs:'Valor'})
            st.dataframe(stats, use_container_width=True)
            fig_hist = px.histogram(df_cancel, x=col_movs, nbins=20, title="Histograma de Movs")
            st.plotly_chart(ajustar_layout_grafico(fig_hist), use_container_width=True)
        else:
            st.warning("Coluna 'Movs' não encontrada.")
    # Tempo de Permanência
    with sub3:
        st.subheader("Tempo de Permanência (horas)")
        # calcula entre ETA e ETD, ou Início/Fim Operação
        if col_eta and col_etd:
            df_cancel['ETA'] = pd.to_datetime(df_cancel[col_eta], errors='coerce')
            df_cancel['ETD'] = pd.to_datetime(df_cancel[col_etd], errors='coerce')
            df_cancel['Tempo_Permanencia'] = (df_cancel['ETD'] - df_cancel['ETA']).dt.total_seconds() / 3600
        elif col_inicio_op and col_fim_op:
            df_cancel['Início'] = pd.to_datetime(df_cancel[col_inicio_op], errors='coerce')
            df_cancel['Fim']    = pd.to_datetime(df_cancel[col_fim_op],    errors='coerce')
            df_cancel['Tempo_Permanencia'] = (df_cancel['Fim'] - df_cancel['Início']).dt.total_seconds() / 3600
        else:
            st.warning("Colunas de data para cálculo de tempo não encontradas.")
        tp = df_cancel['Tempo_Permanencia'].dropna()
        if not tp.empty:
            st.write(tp.describe())
            fig_box = px.box(df_cancel, y='Tempo_Permanencia', title="Boxplot Tempo de Permanência")
            st.plotly_chart(ajustar_layout_grafico(fig_box), use_container_width=True)

# --- Análise de Custos ---
with tabs[5]:
    st.header("💰 Análise de Custos de Exportação")
    if col_movs:
        # cálculo de custos por registro
        df_cancel['C_TEUS'] = df_cancel[col_movs] * REFERENCIAS_CUSTOS['THC']
        df_cancel['C_OPER'] = REFERENCIAS_CUSTOS['TAXA_TERMINAL']
        df_cancel['C_DOC']  = REFERENCIAS_CUSTOS['DESPACHANTE']
        df_cancel['C_ARM']  = (
            df_cancel[col_movs]
            * REFERENCIAS_CUSTOS['ARMAZENAGEM']
            * REFERENCIAS_CUSTOS['DIAS_ARMAZENAGEM']
        )
        df_cancel['C_INSP'] = REFERENCIAS_CUSTOS['SCANNER']
        df_cancel['CUSTO_TOTAL'] = df_cancel[['C_TEUS','C_OPER','C_DOC','C_ARM','C_INSP']].sum(axis=1)

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Custo Total Perdido", f"R$ {df_cancel['CUSTO_TOTAL'].sum():,.2f}".replace(",","."))
        col2.metric("Custo Médio / Cancelamento", f"R$ {df_cancel['CUSTO_TOTAL'].mean():,.2f}".replace(",","."))
        col3.metric("Total de TEUs Afetados", f"{df_cancel[col_movs].sum():,.0f}".replace(",","."))
        
        # Evolução mensal de custos
        if col_eta:
            df_cancel['Mes'] = df_cancel[col_eta].dt.to_period('M').astype(str)
            custos_mensal = (
                df_cancel.groupby('Mes')['CUSTO_TOTAL']
                .sum()
                .reset_index()
            )
            fig_cust = px.line(custos_mensal, x='Mes', y='CUSTO_TOTAL',
                               title="Evolução Mensal de Custos", markers=True)
            st.plotly_chart(ajustar_layout_grafico(fig_cust), use_container_width=True)

        # Detalhamento por tipo de custo
        componentes = pd.Series({
            "THC": df_cancel['C_TEUS'].sum(),
            "Taxa Terminal": df_cancel['C_OPER'].sum(),
            "Despachante": df_cancel['C_DOC'].sum(),
            "Armazenagem": df_cancel['C_ARM'].sum(),
            "Scanner": df_cancel['C_INSP'].sum()
        }).reset_index()
        componentes.columns = ["Tipo de Custo","Valor Total (R$)"]
        componentes["Valor Total (R$)"] = componentes["Valor Total (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(",","."))
        st.subheader("Detalhamento dos Componentes de Custo")
        st.dataframe(componentes, use_container_width=True)

    else:
        st.warning("Coluna 'Movs' não encontrada — não é possível calcular custos.")
