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

# ——— Funções utilitárias ———

def ajustar_layout_grafico(fig, altura=500):
    fig.update_layout(
        height=altura,
        margin=dict(l=50, r=50, t=60, b=60),
        paper_bgcolor='rgba(10,25,40,0)',
        plot_bgcolor='rgba(10,25,40,0)',
        font=dict(size=12, color='#E0E0E0'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_traces(marker_line_width=0)
    return fig

# ——— Configuração da página e CSS tema “mar” ———

st.set_page_config(page_title="⚓ Dashboard Marítimo de Cancelamentos", layout="wide", page_icon="⚓")

st.markdown("""
<style>
/* Fundo escuro azulado */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0a1f2f 0%, #02111e 100%);
    color: #E0E0E0;
}
/* Cartões náuticos */
.dashboard-card {
    background: rgba(255,255,255,0.05);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    border: 1px solid #0f3851;
}
/* Cabeçalhos centralizados */
h1, h2, h3, h4 { text-align: center; }
/* Margem entre gráficos */
.js-plotly-plot { margin-bottom: 3rem !important; }
/* Espaçamento geral */
section.main > div.block-container { padding: 2rem 1rem; }
/* Colunas */
[data-testid="stColumns"] > div { margin-bottom: 2rem; }
/* Inputs e botões */
.stTextInput, .stFileUploader, .stSelectbox, .stButton { margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ——— Cabeçalho principal ———

st.markdown("""
<div class="dashboard-card">
  <h1>⚓ Análise de Cancelamentos de Navios</h1>
  <p>Dashboard Marítimo Interativo</p>
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
    st.markdown("### 🔍 Filtros")
    termo = st.text_input("Buscar navio, armador ou rota")
    st.markdown("---")
    st.markdown("### ⚓ Referências de Custos")
    st.write("""
      - THC (R$/TEU): 1.200,00  
      - Armazenagem (R$/TEU/dia): 575,00  
      - Despachante (R$): 950,00  
      - Scanner (R$/contêiner): 95,00  
      - Câmbio médio: R$ 5,10 / US$ 1
    """)

# ——— Upload de arquivo ———

xls = st.file_uploader("📁 Faça upload do Excel", type="xlsx")
if not xls:
    st.stop()
df = pd.read_excel(xls)

# ——— Detectar colunas ———

col_status      = 'Situação' if 'Situação' in df.columns else None
col_data        = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_conteineres = 'Movs' if 'Movs' in df.columns else None
col_armador     = 'Armador' if 'Armador' in df.columns else None
col_rota        = 'De / Para' if 'De / Para' in df.columns else None
col_tipo_navio  = 'Tipo' if 'Tipo' in df.columns else None
col_navio_raw   = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None

# ——— Filtrar cancelados ———

if col_status:
    df[col_status] = df[col_status].str.strip().str.lower()
    df_cancel = df[df[col_status].isin(['cancelado','cancelada','rejeitado','rej.','canceled'])].copy()
else:
    df_cancel = df.copy()

# ——— Converter tipos ———

if col_conteineres:
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce').fillna(0)
if col_data:
    df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], errors='coerce', dayfirst=True)

# ——— Extrair nome de navio ———

NAV_COL = 'Navio / Viagem.1' if 'Navio / Viagem.1' in df_cancel.columns else col_navio_raw
df_cancel['Navio'] = df_cancel[NAV_COL].astype(str).str.strip().str.title()
cnt_navios = df_cancel['Navio'].value_counts().reset_index()
cnt_navios.columns = ['Navio','Cancelamentos']

# ——— Série temporal mensal ———

if col_data:
    tmp = df_cancel.dropna(subset=[col_data]).copy()
    tmp['Mes'] = tmp[col_data].dt.to_period('M').astype(str)
    cnt_mensal = tmp.groupby('Mes').size().reset_index(name='Cancelamentos')
    cnt_mensal['Mes'] = pd.to_datetime(cnt_mensal['Mes'],format='%Y-%m')
    cnt_mensal = cnt_mensal.sort_values('Mes')
else:
    cnt_mensal = pd.DataFrame(columns=['Mes','Cancelamentos'])

# ——— Resumo na sidebar ———

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Resumo Rápido")
    st.write(f"- Total de cancelamentos: **{len(df_cancel):,}**")
    if not cnt_navios.empty:
        top = cnt_navios.iloc[0]
        st.write(f"- Navio mais cancelado: **{top['Navio']}** ({top['Cancelamentos']}x)")
    if not cnt_mensal.empty:
        pico = cnt_mensal.loc[cnt_mensal['Cancelamentos'].idxmax()]
        st.write(f"- Mês de pico: **{pico['Mes'].strftime('%Y-%m')}** ({int(pico['Cancelamentos'])} cancel.)")

# ——— Abas principais ———

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "📈 Geral","🚢 Navios","📅 Temporal","🌍 Rotas","📊 Adicionais","💰 Custos"
])

# Aba 1: Visão Geral
with tab1:
    st.header("📈 Visão Geral")
    c1,c2,c3 = st.columns(3,gap="large")
    c1.metric("Registros totais",f"{len(df):,}",delta=f"{len(df_cancel):,} cancel.")
    pct = (len(df_cancel)/len(df)*100) if len(df)>0 else 0
    c2.metric("Taxa de cancelamento",f"{pct:.1f}%",delta=f"{pct:.1f}%")
    avg = (len(df_cancel)/30) if len(df_cancel)>0 else 0
    c3.metric("Média diária",f"{avg:.1f}",delta="cancel./dia")

    # Cancelados vs Não
    pie = px.pie(
        names=["Cancelados","Não cancelados"],
        values=[len(df_cancel),len(df)-len(df_cancel)],
        title="Distribuição de Cancelamentos",
        color_discrete_sequence=px.colors.sequential.Blues
    )
    st.plotly_chart(ajustar_layout_grafico(pie,altura=400),use_container_width=True)

# Aba 2: Top Navios
with tab2:
    st.header("🚢 Top 10 Navios")
    if cnt_navios['Cancelamentos'].nunique()==1:
        st.info("Todos os navios têm 1 cancelamento.")
        st.dataframe(cnt_navios,use_container_width=True)
    else:
        colg, colt = st.columns([1.3,1],gap="large")
        with colg:
            st.subheader("🏆 Ranking")
            bar = px.bar(
                cnt_navios.head(10),y='Navio',x='Cancelamentos',orientation='h',
                color='Cancelamentos',color_continuous_scale='Blues',title=""
            )
            bar.update_layout(yaxis_title=None,xaxis_title="Cancelamentos")
            st.plotly_chart(ajustar_layout_grafico(bar),use_container_width=True)
        with colt:
            st.subheader("📋 Detalhe Top 10")
            st.dataframe(cnt_navios.head(10),use_container_width=True)

# Aba 3: Temporal
with tab3:
    st.header("📅 Evolução Mensal")
    st.dataframe(cnt_mensal.assign(Mes=cnt_mensal['Mes'].dt.strftime('%Y-%m')),
                 hide_index=True,use_container_width=True)
    ln = px.line(cnt_mensal,x='Mes',y='Cancelamentos',markers=True,title="")
    st.plotly_chart(ajustar_layout_grafico(ln),use_container_width=True)

# Aba 4: Rotas
with tab4:
    st.header("🌍 Rotas")
    if col_rota:
        cnt_rotas = df_cancel[col_rota].value_counts().reset_index()
        cnt_rotas.columns=['Rota','Cancelamentos']
        st.dataframe(cnt_rotas.head(10),use_container_width=True,hide_index=True)
        br = px.bar(cnt_rotas.head(5),x='Rota',y='Cancelamentos',
                    color='Cancelamentos',color_continuous_scale='Blues',title="")
        st.plotly_chart(ajustar_layout_grafico(br),use_container_width=True)
    else:
        st.warning("Coluna de rotas não encontrada.")

# Aba 5: Adicionais
with tab5:
    st.header("📊 Adicionais")
    t1,t2,t3 = st.tabs(["Tipo Navio","Contêineres","Armadores"])
    with t1:
        if col_tipo_navio:
            df_cancel[col_tipo_navio]=df_cancel[col_tipo_navio].str.capitalize()
            ct = df_cancel[col_tipo_navio].value_counts().reset_index()
            ct.columns=['Tipo','Cancelamentos']
            st.dataframe(ct,use_container_width=True)
            p = px.pie(ct,values='Cancelamentos',names='Tipo',title="")
            st.plotly_chart(ajustar_layout_grafico(p,altura=350),use_container_width=True)
    with t2:
        if col_conteineres:
            stats = df_cancel[col_conteineres].describe().to_frame().reset_index()
            st.dataframe(stats,use_container_width=True)
            h = px.histogram(df_cancel,x=col_conteineres,nbins=20,title="")
            st.plotly_chart(ajustar_layout_grafico(h),use_container_width=True)
    with t3:
        if col_armador:
            df_cancel[col_armador]=df_cancel[col_armador].fillna("Não Informado")
            ca = df_cancel[col_armador].value_counts().reset_index()
            ca.columns=['Armador','Cancelamentos']
            st.dataframe(ca.head(10),use_container_width=True)
            b = px.bar(ca.head(5),x='Armador',y='Cancelamentos',
                       color='Cancelamentos',color_continuous_scale='Blues',title="")
            st.plotly_chart(ajustar_layout_grafico(b),use_container_width=True)

# Aba 6: Custos
with tab6:
    st.header("💰 Custos")
    C = {"TEU":1200,"OPER":1150,"DOC":950,"ARM_DIA":575,"ARM_DIAS":2,"INSP":95}
    if col_conteineres:
        df_c = df_cancel.copy()
        df_c[col_conteineres]=df_c[col_conteineres].fillna(0)
        df_c["C_TEUS"]=df_c[col_conteineres]*C["TEU"]
        df_c["C_OPER"]=C["OPER"]
        df_c["C_DOC"]=C["DOC"]
        df_c["C_ARM"]=df_c[col_conteineres]*C["ARM_DIA"]*C["ARM_DIAS"]
        df_c["C_INSP"]=C["INSP"]
        df_c["CUSTO"]=df_c[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum(axis=1)

        m1,m2,m3 = st.columns(3,gap="large")
        m1.metric("Total perdido",f"R$ {df_c['CUSTO'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Médio por cancel.",f"R$ {df_c['CUSTO'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m3.metric("TEUs afetados",f"{df_c[col_conteineres].sum():,.0f}".replace(",", "."))

        box = px.box(df_c,y="CUSTO",title="")
        st.plotly_chart(ajustar_layout_grafico(box),use_container_width=True)

        # Componentes
        tot = df_c[["C_TEUS","C_OPER","C_DOC","C_ARM","C_INSP"]].sum()
        comp = pd.DataFrame({
            "Tipo":["THC","Taxa Terminal","Despachante","Armazenagem","Scanner"],
            "Valor":tot.values
        })
        comp["Valor R$"] = comp["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.subheader("Componentes de custo")
        st.dataframe(comp[["Tipo","Valor R$"]],use_container_width=True,hide_index=True)
        pie2 = px.pie(comp,values='Valor',names='Tipo',title="")
        st.plotly_chart(ajustar_layout_grafico(pie2,altura=350),use_container_width=True)
    else:
        st.warning("Não foi possível calcular custos sem coluna 'Movs'.")
