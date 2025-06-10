"""
Análise de Levantamentos de Portos sobre Navios Cancelados

Este notebook contém um trabalho da faculdade feito por:
- Arley do Nascimento Vinagre (12722132338)
- Vinicius Santana (1272221567)
- Tauan Santos Santana (12722216126)

O objetivo deste trabalho é analisar os levantamentos em formato Excel dos portos sobre navios cancelados.
"""

# -----------------------------------------------------------
# 1. Importar bibliotecas necessárias
# -----------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ajustes gerais de exibição
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
plt.rcParams['figure.figsize'] = (10, 6)

# -----------------------------------------------------------
# 2. Carregar o arquivo Excel
# -----------------------------------------------------------
excel_filename = 'ProgramacaoDeNavios (1) (1).xlsx'
df = pd.read_excel(excel_filename)

# -----------------------------------------------------------
# 3. Inspeção inicial: colunas e primeiras linhas
# -----------------------------------------------------------
print("Colunas encontradas na planilha:")
print(df.columns.to_list())
print("\nExibição das 5 primeiras linhas:")
print(df.head())

# -----------------------------------------------------------
# 4. Identificar quais colunas indicam cancelamento, data, navio, motivo, rota, porto
# -----------------------------------------------------------
col_navio = 'Navio / Viagem' if 'Navio / Viagem' in df.columns else None
col_status = 'Situação' if 'Situação' in df.columns else None
col_data = 'Estimativa Chegada ETA' if 'Estimativa Chegada ETA' in df.columns else None
col_motivo = 'MotivoCancelamento' if 'MotivoCancelamento' in df.columns else None
col_rota = 'De / Para' if 'De / Para' in df.columns else None
col_porto_or = None
col_porto_dest = None
col_tipo_navio = 'Tipo' if 'Tipo' in df.columns else None
col_conteineres = 'Movs' if 'Movs' in df.columns else None

print("\nColunas mapeadas (None indica que precisa ajustar):")
print({
    'col_navio': col_navio,
    'col_status': col_status,
    'col_data': col_data,
    'col_motivo': col_motivo,
    'col_rota': col_rota,
    'col_porto_origem': col_porto_or,
    'col_porto_destino': col_porto_dest,
    'col_tipo_navio': col_tipo_navio,
    'col_conteineres': col_conteineres
})

# -----------------------------------------------------------
# 5. Filtrar apenas as linhas de cancelamento
# -----------------------------------------------------------
if col_status is None:
    raise ValueError("Não foi possível identificar a coluna de status. Ajuste 'col_status' manualmente.")

df[col_status] = df[col_status].astype(str).str.strip().str.lower()
valores_cancelados = ['cancelado', 'cancelada', 'rejeitado', 'rej.', 'canceled']
mask_cancel = df[col_status].isin(valores_cancelados)

df_cancel = df.loc[mask_cancel].copy()
print(f"\nTotal de linhas na planilha original: {len(df)}")
print(f"Total de registros de cancelamento identificados: {len(df_cancel)}")

# -----------------------------------------------------------
# 6. Converter coluna de data para datetime e extrair intervalos
# -----------------------------------------------------------
if col_data is None:
    raise ValueError("Não foi possível identificar a coluna de data. Ajuste 'col_data' manualmente.")

df_cancel[col_data] = pd.to_datetime(df_cancel[col_data], dayfirst=True, errors='coerce')
na_dates = df_cancel[col_data].isna().sum()
print(f"\nRegistros de cancelamento com data inválida/nula: {na_dates}")
df_cancel = df_cancel.dropna(subset=[col_data])

df_cancel['Ano'] = df_cancel[col_data].dt.year
df_cancel['Mês'] = df_cancel[col_data].dt.month
df_cancel['Y-M'] = df_cancel[col_data].dt.to_period('M').astype(str)

# -----------------------------------------------------------
# 7. Análise 1: Navios que mais foram cancelados
# -----------------------------------------------------------
if col_navio is None:
    raise ValueError("Não foi possível identificar a coluna de navio. Ajuste 'col_navio' manualmente.")

contagem_navios = df_cancel[col_navio].value_counts().reset_index()
contagem_navios.columns = ['Navio', 'QuantidadeCancelamentos']
print("\nTop 10 navios com mais cancelamentos:")
print(contagem_navios.head(10))

plt.figure(figsize=(12, 7))
top5_navios = contagem_navios.head(5)
plt.bar(top5_navios['Navio'], top5_navios['QuantidadeCancelamentos'])
plt.title('Top 5 Navios com Mais Cancelamentos')
plt.xlabel('Navio')
plt.ylabel('Quantidade de Cancelamentos')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# -----------------------------------------------------------
# 8. Análise 2: Motivos de cancelamento (frequência)
# -----------------------------------------------------------
if col_motivo is not None and col_motivo in df_cancel.columns:
    df_cancel[col_motivo] = df_cancel[col_motivo].astype(str).str.strip().str.capitalize()
    contagem_motivos = df_cancel[col_motivo].value_counts().reset_index()
    contagem_motivos.columns = ['Motivo', 'Frequência']
    print("\nFrequência de Motivos de Cancelamento:")
    print(contagem_motivos)

    plt.figure(figsize=(12, 7))
    top5_motivos = contagem_motivos.head(5)
    plt.bar(top5_motivos['Motivo'], top5_motivos['Frequência'])
    plt.title('Top 5 Motivos de Cancelamento')
    plt.xlabel('Motivo')
    plt.ylabel('Frequência')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print("\nNenhuma coluna de motivo de cancelamento encontrada ou não informada.")

# -----------------------------------------------------------
# 9. Análise 3: Intervalo de tempo com mais cancelamentos
# -----------------------------------------------------------
contagem_mensal = df_cancel.groupby('Y-M').size().reset_index(name='Cancelamentos')
contagem_mensal['Y-M'] = pd.to_datetime(contagem_mensal['Y-M'], format='%Y-%m')
contagem_mensal = contagem_mensal.sort_values('Y-M')

print("\nQuantidade de cancelamentos por mês:")
print(contagem_mensal)

plt.figure(figsize=(15, 7))
plt.plot(contagem_mensal['Y-M'], contagem_mensal['Cancelamentos'], marker='o')
plt.title('Cancelamentos Mensais de Navios')
plt.xlabel('Mês')
plt.ylabel('Número de Cancelamentos')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()

max_mes = contagem_mensal.loc[contagem_mensal['Cancelamentos'].idxmax()]
print(f"Mês com mais cancelamentos: {max_mes['Y-M'].strftime('%Y-%m')} → {int(max_mes['Cancelamentos'])} cancelamentos")

# -----------------------------------------------------------
# 10. Análise 4: Rotas mais impactadas
# -----------------------------------------------------------
if col_rota is not None and col_rota in df_cancel.columns:
    contagem_rotas = df_cancel[col_rota].value_counts().reset_index()
    contagem_rotas.columns = ['Rota', 'Cancelamentos']
    print("\nTop 10 rotas com mais cancelamentos (coluna 'De / Para'):")
    print(contagem_rotas.head(10))

    plt.figure(figsize=(12, 7))
    top5_rotas = contagem_rotas.head(5)
    plt.bar(top5_rotas['Rota'], top5_rotas['Cancelamentos'])
    plt.title('Top 5 Rotas com Mais Cancelamentos')
    plt.xlabel('Rota')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print("\nNão foi possível identificar colunas de rota nem de porto origem/destino.")

# -----------------------------------------------------------
# 11. Análise 5: Distribuição de cancelamentos por tipo de navio
# -----------------------------------------------------------
if col_tipo_navio is not None and col_tipo_navio in df_cancel.columns:
    df_cancel[col_tipo_navio] = df_cancel[col_tipo_navio].astype(str).str.strip().str.capitalize()
    contagem_tipo_navio = df_cancel[col_tipo_navio].value_counts().reset_index()
    contagem_tipo_navio.columns = ['TipoNavio', 'Cancelamentos']

    print(f"\nDistribuição de cancelamentos por tipo de navio:")
    print(contagem_tipo_navio)

    plt.figure(figsize=(12, 7))
    top5_tipo_navio = contagem_tipo_navio.head(5)
    plt.bar(top5_tipo_navio['TipoNavio'], top5_tipo_navio['Cancelamentos'])
    plt.title('Top 5 Tipos de Navio com Mais Cancelamentos')
    plt.xlabel('Tipo de Navio')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print(f"\nColuna '{col_tipo_navio}' não encontrada para analisar distribuição por tipo de navio.")

# -----------------------------------------------------------
# 12. Análise 6: Análise da coluna de contêineres
# -----------------------------------------------------------
if col_conteineres is not None and col_conteineres in df_cancel.columns:
    print(f"\nAnálise da coluna '{col_conteineres}' nos registros cancelados:")
    df_cancel[col_conteineres] = pd.to_numeric(df_cancel[col_conteineres], errors='coerce')
    df_cancel_conteineres = df_cancel.dropna(subset=[col_conteineres])

    if len(df_cancel_conteineres) > 0:
        print(df_cancel_conteineres[col_conteineres].describe())

        plt.figure(figsize=(10, 6))
        plt.hist(df_cancel_conteineres[col_conteineres], bins=20, edgecolor='black')
        plt.title(f'Distribuição da Quantidade de Contêineres em Cancelamentos')
        plt.xlabel('Quantidade de Contêineres')
        plt.ylabel('Frequência')
        plt.tight_layout()
        plt.show()
    else:
        print(f"Nenhum registro válido na coluna '{col_conteineres}' após limpeza.")
else:
    print(f"\nColuna '{col_conteineres}' não encontrada para análise adicional.")

# -----------------------------------------------------------
# 13. Análise 7: Distribuição de cancelamentos por Armador
# -----------------------------------------------------------
col_armador = 'Armador' if 'Armador' in df_cancel.columns else None

if col_armador is not None:
    df_cancel[col_armador] = df_cancel[col_armador].astype(str).str.strip().str.capitalize()
    contagem_armadores = df_cancel[col_armador].value_counts().reset_index()
    contagem_armadores.columns = ['Armador', 'Cancelamentos']

    print(f"\nDistribuição de cancelamentos por Armador:")
    print(contagem_armadores.head(10))

    plt.figure(figsize=(12, 7))
    top5_armadores = contagem_armadores.head(5)
    plt.bar(top5_armadores['Armador'], top5_armadores['Cancelamentos'])
    plt.title('Top 5 Armadores com Mais Cancelamentos')
    plt.xlabel('Armador')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print(f"\nColuna '{col_armador}' não encontrada para analisar distribuição por armador.")

# -----------------------------------------------------------
# 14. Análise 8: Distribuição de cancelamentos por Berço
# -----------------------------------------------------------
col_berco = 'Berço' if 'Berço' in df_cancel.columns else None

if col_berco is not None:
    df_cancel[col_berco] = df_cancel[col_berco].astype(str).str.strip().str.capitalize()
    contagem_bercos = df_cancel[col_berco].value_counts().reset_index()
    contagem_bercos.columns = ['Berço', 'Cancelamentos']

    print(f"\nDistribuição de cancelamentos por Berço:")
    print(contagem_bercos.head(10))

    plt.figure(figsize=(12, 7))
    top5_bercos = contagem_bercos.head(5)
    plt.bar(top5_bercos['Berço'], top5_bercos['Cancelamentos'])
    plt.title('Top 5 Berços com Mais Cancelamentos')
    plt.xlabel('Berço')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print(f"\nColuna '{col_berco}' não encontrada para analisar distribuição por berço.")

# -----------------------------------------------------------
# 15. Análise 9: Distribuição de cancelamentos por Serviço
# -----------------------------------------------------------
col_servico = 'Serviço' if 'Serviço' in df_cancel.columns else None

if col_servico is not None:
    df_cancel[col_servico] = df_cancel[col_servico].astype(str).str.strip().str.capitalize()
    contagem_servicos = df_cancel[col_servico].value_counts().reset_index()
    contagem_servicos.columns = ['Serviço', 'Cancelamentos']

    print(f"\nDistribuição de cancelamentos por Serviço:")
    print(contagem_servicos.head(10))

    plt.figure(figsize=(12, 7))
    top5_servicos = contagem_servicos.head(5)
    plt.bar(top5_servicos['Serviço'], top5_servicos['Cancelamentos'])
    plt.title('Top 5 Serviços com Mais Cancelamentos')
    plt.xlabel('Serviço')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print(f"\nColuna '{col_servico}' não encontrada para analisar distribuição por serviço.")

# -----------------------------------------------------------
# 16. Análise 10: Distribuição de cancelamentos por País
# -----------------------------------------------------------
col_pais = 'País' if 'País' in df_cancel.columns else None

if col_pais is not None:
    df_cancel[col_pais] = df_cancel[col_pais].astype(str).str.strip().str.capitalize()
    contagem_paises = df_cancel[col_pais].value_counts().reset_index()
    contagem_paises.columns = ['País', 'Cancelamentos']

    print(f"\nDistribuição de cancelamentos por País:")
    print(contagem_paises.head(10))

    plt.figure(figsize=(12, 7))
    top5_paises = contagem_paises.head(5)
    plt.bar(top5_paises['País'], top5_paises['Cancelamentos'])
    plt.title('Top 5 Países com Mais Cancelamentos')
    plt.xlabel('País')
    plt.ylabel('Quantidade de Cancelamentos')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print(f"\nColuna '{col_pais}' não encontrada para analisar distribuição por país.")

# -----------------------------------------------------------
# 17. Conclusão final
# -----------------------------------------------------------
print("\n--- RESUMO FINAL DOS RESULTADOS ---")
print(f"- Total de cancelamentos analisados: {len(df_cancel)}")
if len(contagem_navios) > 0:
    print(f"- Navio mais cancelado: {contagem_navios.iloc[0]['Navio']} ({contagem_navios.iloc[0]['QuantidadeCancelamentos']} vezes)")
if col_motivo is not None and col_motivo in df_cancel.columns and len(contagem_motivos) > 0:
    print(f"- Motivo mais comum: {contagem_motivos.iloc[0]['Motivo']} ({contagem_motivos.iloc[0]['Frequência']} vezes)")
if len(contagem_mensal) > 0:
    print(f"- Mês com maior incidência de cancelamentos: {max_mes['Y-M'].strftime('%Y-%m')} ({int(max_mes['Cancelamentos'])} cancelamentos)")
if col_rota is not None and col_rota in df_cancel.columns and len(contagem_rotas) > 0:
    print(f"- Rota mais afetada: {contagem_rotas.iloc[0]['Rota']} ({contagem_rotas.iloc[0]['Cancelamentos']} cancelamentos)")

if 'contagem_tipo_navio' in locals() and len(contagem_tipo_navio) > 0:
    print(f"- Tipo de navio mais cancelado: {contagem_tipo_navio.iloc[0]['TipoNavio']} ({contagem_tipo_navio.iloc[0]['Cancelamentos']} vezes)")

if col_conteineres is not None and col_conteineres in df_cancel.columns and len(df_cancel_conteineres) > 0:
    print(f"- Média de contêineres em cancelamentos: {df_cancel_conteineres[col_conteineres].mean():.2f}")

print("--- FIM DO RESUMO FINAL ---") 