import pandas as pd
import os
import glob
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega variáveis do .env

Base = declarative_base()

# Modelo da Tabela (Abstração)
class ProducaoAmbulatorial(Base):
    __tablename__ = 'producao_ambulatorial'
    id = Column(Integer, primary_key=True, autoincrement=True)
    municipio_codigo = Column(String(10), index=True)
    municipio_nome = Column(String(255))
    subgrupo_procedimento = Column(String(255), index=True)
    periodo = Column(Date, index=True)
    quantidade_aprovada = Column(Integer)
    valor_aprovado = Column(Float)

class DataLoader:
    
    def __init__(self, db_url):
        """ db_url ex: 'postgresql://user:pass@localhost:5432/db_faculdade' """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def clean_datasus_csv(self, file_path, value_name):
        # 1. Leitura ignorando aspas para evitar erro de EOF
        df = pd.read_csv(
            file_path, 
            sep=';', 
            encoding='utf-8', 
            engine='c', 
            quoting=3, 
            on_bad_lines='skip'
        )
        
        # 2. LIMPEZA DOS CABEÇALHOS (Resolve o KeyError)
        # Remove aspas de todos os nomes de colunas
        df.columns = [c.replace('"', '').strip() for c in df.columns]
        
        # 3. Identificar a coluna de Município (mesmo se mudar o nome sutilmente)
        col_municipio = None
        for col in df.columns:
            if 'Munic' in col: # Procura por algo que contenha 'Munic'
                col_municipio = col
                break
                
        if not col_municipio:
            raise KeyError(f"Coluna de Município não encontrada. Colunas disponíveis: {df.columns.tolist()}")

        # 4. Limpeza das aspas nos valores das células
        df[col_municipio] = df[col_municipio].astype(str).str.replace('"', '').str.strip()

        # 5. Filtragem Dinâmica (Rodapés e Lixo)
        lixo = ['Total', 'Fonte:', 'Nota:', 'Notas:', 'Período:', 'Página']
        df = df[df[col_municipio].notna()]
        for palavra in lixo:
            df = df[~df[col_municipio].str.contains(palavra, na=False, case=False)]

        # Manter apenas linhas que começam com o código IBGE (6 dígitos)
        df = df[df[col_municipio].str.contains(r'^\d{6}', na=False)]
        
        # 6. Extração de Código e Nome
        df['municipio_codigo'] = df[col_municipio].str.extract(r'^(\d{6})')
        df['municipio_nome'] = df[col_municipio].str.replace(r'^\d{6}\s', '', regex=True)
        
        # 7. Melt (Transformação para formato Long)
        # Removemos colunas indesejadas antes do melt
        if 'Total' in df.columns:
            df = df.drop(columns=['Total'])
        
        cols_to_keep = ['municipio_codigo', 'municipio_nome']
        df_long = df.melt(id_vars=cols_to_keep, 
                        var_name='subgrupo_procedimento', 
                        value_name=value_name)

        # 8. Limpeza Numérica (Remoção de aspas e conversão BRL -> Float)
        df_long[value_name] = df_long[value_name].astype(str).str.replace('"', '').replace('-', '0')
        # Remove ponto de milhar e troca vírgula por ponto
        df_long[value_name] = df_long[value_name].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_long[value_name] = pd.to_numeric(df_long[value_name], errors='coerce').fillna(0)

        return df_long

    def load_period(self, month, year):
        file_suffix = f"{month}_{year}.csv"
        path_qtd = f"data/raw/sia_br_qtd_{file_suffix}"
        path_valor = f"data/raw/sia_br_valor_{file_suffix}"

        # DEBUG 1: Verificar se os caminhos estão corretos
        print(f"🔍 Procurando: {path_qtd}")
        
        if not os.path.exists(path_qtd) or not os.path.exists(path_valor):
            print(f"⚠️ Arquivos não encontrados em: {os.path.abspath('data/raw')}")
            return

        try:
            # DEBUG 2: Verificar o tamanho dos DataFrames após a limpeza
            df_qtd = self.clean_datasus_csv(path_qtd, 'quantidade_aprovada')
            print(f"📊 QTD extraída: {len(df_qtd)} linhas")
            
            df_valor = self.clean_datasus_csv(path_valor, 'valor_aprovado')
            print(f"📊 VALOR extraído: {len(df_valor)} linhas")

            # DEBUG 3: Verificar o merge
            df_final = pd.merge(df_qtd, df_valor, on=['municipio_codigo', 'municipio_nome', 'subgrupo_procedimento'])
            print(f"🔀 Linhas após o merge: {len(df_final)}")

            if df_final.empty:
                print("❌ ERRO: O merge resultou em 0 linhas. Verifique se os nomes dos municípios batem nos dois arquivos.")
                return

            # Adicionar data
            meses_map = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 
                         'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12}
            df_final['periodo'] = pd.to_datetime(f"{year}-{meses_map[month]}-01")

            # CARGA
            print(f"📤 Enviando {len(df_final)} linhas para o PostgreSQL...")
            df_final.to_sql(ProducaoAmbulatorial.__tablename__, self.engine, if_exists='append', index=False)
            print("✅ Carga concluída!")

        except Exception as e:
            print(f"💥 Erro durante a carga: {e}")

if __name__ == "__main__":
    
    import os
    from dotenv import load_dotenv
    
    # 1. Carregar variáveis de ambiente (.env)
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    
    if not DB_URL:
        print("❌ Erro: DB_URL não encontrada no arquivo .env")
    else:
        loader = DataLoader(DB_URL)
        
        # 2. Definir os períodos que o projeto abrange
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
                 "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        anos = [2024, 2025, 2026]
        
        print("🚀 Iniciando processamento em lote (Batch Load)...")
        
        # 3. Loop para percorrer todos os meses necessários
        for ano in anos:
            for mes in meses:
                # Condição de parada: Janeiro de 2026
                if ano == 2026 and mes != "Jan":
                    break
                
                try:
                    # Chama a função que você já adaptou para ler do nome do arquivo
                    loader.load_period(mes, str(ano))
                except Exception as e:
                    print(f"💥 Falha crítica ao processar {mes}/{ano}: {e}")
                    continue # Pula para o próximo mês em caso de erro individual

        print("\n✨ Processamento de todos os períodos finalizado!")