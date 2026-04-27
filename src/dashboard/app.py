import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

# Configurações iniciais
st.set_page_config(page_title="SIA/SUS Analytics", layout="wide", page_icon="🏥")

# --- CONEXÃO ---
# Tenta obter dos Secrets (Deploy) ou do ambiente local
if "DB_URL" in st.secrets:
    DB_URL = st.secrets["DB_URL"]
else:
    # Fallback para desenvolvimento local
    DB_URL = os.getenv("DB_URL")

@st.cache_resource
def get_engine():
    if not DB_URL:
        st.error("A variável de conexão DB_URL não foi encontrada.")
        st.stop()
    return create_engine(DB_URL)

@st.cache_data(ttl=3600) # Cache por 1 hora para evitar sobrecarregar o banco do IESB
def load_data():
    try:
        engine = create_engine(DB_URL)
        query = "SELECT * FROM producao_ambulatorial ORDER BY periodo ASC"
        df = pd.read_sql(query, engine)
        if not df.empty:
            df['periodo'] = pd.to_datetime(df['periodo'])
        return df
    except Exception as e:
        # Exibe o erro na tela mas não derruba o app
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

try:
    
    # Execução principal
    df = load_data()

    if df.empty:
        st.warning("⚠️ Não foram encontrados dados. Certifique-se de que o banco de dados está acessível e contém a tabela 'producao_ambulatorial'.")
        st.info("Dica: Verifique se o IP do servidor do Streamlit tem permissão de acesso no seu banco de dados PostgreSQL.")
        st.stop()

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros de Pesquisa")
    
    lista_municipios = sorted(df['municipio_nome'].unique())
    municipios_sel = st.sidebar.multiselect("Municípios", options=lista_municipios)

    lista_subgrupos = sorted(df['subgrupo_procedimento'].unique())
    subgrupos_sel = st.sidebar.multiselect("Subgrupos de Procedimento", options=lista_subgrupos)

    # Filtragem lógica
    df_filtered = df.copy()
    if municipios_sel:
        df_filtered = df_filtered[df_filtered['municipio_nome'].isin(municipios_sel)]
    if subgrupos_sel:
        df_filtered = df_filtered[df_filtered['subgrupo_procedimento'].isin(subgrupos_sel)]

    # --- DASHBOARD PRINCIPAL ---
    st.title("🏥 Análise de Produção Ambulatorial - SIA/SUS")
    st.markdown(f"Análise referente ao período de **{df['periodo'].min().strftime('%m/%Y')}** a **{df['periodo'].max().strftime('%m/%Y')}**")

    # KPIs (Métricas)
    col1, col2, col3 = st.columns(3)
    with col1:
        total_qtd = df_filtered['quantidade_aprovada'].sum()
        st.metric("Total de Procedimentos", f"{total_qtd:,}")
    with col2:
        total_valor = df_filtered['valor_aprovado'].sum()
        st.metric("Valor Total (R$)", f"R$ {total_valor:,.2f}")
    with col3:
        avg_valor = df_filtered['valor_aprovado'].mean() if not df_filtered.empty else 0
        st.metric("Média por Registro", f"R$ {avg_valor:,.2f}")

    st.divider()

    # GRÁFICOS
    tab1, tab2 = st.tabs(["📈 Evolução Temporal", "📊 Rankings e Tabelas"])

    with tab1:
        st.subheader("Evolução Mensal da Produção")
        df_timeline = df_filtered.groupby('periodo')[['quantidade_aprovada', 'valor_aprovado']].sum().reset_index()
        fig_line = px.line(df_timeline, x='periodo', y='quantidade_aprovada', 
                           title="Quantidade de Procedimentos ao Longo do Tempo",
                           labels={'quantidade_aprovada': 'Qtd', 'periodo': 'Mês/Ano'},
                           markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Top Subgrupos por Valor")
            df_top = df_filtered.groupby('subgrupo_procedimento')['valor_aprovado'].sum().nlargest(10).reset_index()
            fig_bar = px.bar(df_top, x='valor_aprovado', y='subgrupo_procedimento', orientation='h',
                             color='valor_aprovado', color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col_b:
            st.subheader("Dados Detalhados (Linhas Zeradas Inclusas)")
            st.dataframe(df_filtered[['municipio_nome', 'subgrupo_procedimento', 'periodo', 'quantidade_aprovada', 'valor_aprovado']], 
                         hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao conectar ou carregar dados: {e}")
    st.info("Verifique se o seu script de 'loader.py' já enviou os dados para o banco do IESB.")