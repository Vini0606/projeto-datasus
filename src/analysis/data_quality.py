import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# ==============================================================================
# SCRIPT DE AUDITORIA DE QUALIDADE DE DADOS (SIA/SUS)
# Foco: Dimensões de Completude, Consistência e Integridade
# ==============================================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

class DataQualityAuditor:
    
    def __init__(self, db_url, cache_dir="data/processed"):
        
        self.engine = create_engine(db_url)
        self.output_path = "docs/figures/"
        
        # Define o caminho do arquivo de cache local
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(self.cache_dir, "producao_ambulatorial_cache.parquet")
        
        # Garante que os diretórios existam
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_data(self):
        """
        Recupera os dados. Tenta ler do cache local primeiro. 
        Se não existir, consulta o banco e salva o cache.
        """
        if os.path.exists(self.cache_file):
            print(f"[CACHE] Lendo dados localmente de: {self.cache_file}")
            # Usando engine='pyarrow' para máxima performance
            return pd.read_parquet(self.cache_file)
        
        print("[DB] Arquivo local não encontrado. Consultando banco de dados (isso pode demorar)...")
        query = "SELECT * FROM producao_ambulatorial;"
        df = pd.read_sql(query, self.engine)
        
        # Persiste localmente para a próxima chamada
        print(f"[CACHE] Salvando dados localmente em: {self.cache_file}")
        df.to_parquet(self.cache_file, index=False, compression='snappy')
        
        return df
    
    def audit_completeness(self, df):
        """Analisa a Dimensão da Completude (Valores Nulos e Vazios)"""
        total_rows = len(df)
        completeness = df.isnull().sum().reset_index()
        completeness.columns = ['Atributo', 'Nulos']
        completeness['%_Completude'] = 100 * (1 - (completeness['Nulos'] / total_rows))
        
        print("\n[INFO] Matriz de Completude calculada.")
        return completeness

    def audit_consistency(self, df):
        """Verifica inconsistências de negócio (Valores zerados e negativos)"""
        # No SIA/SUS, valores zerados podem indicar 'Vazios Assistenciais'
        zeros_qtd = (df['quantidade_aprovada'] == 0).sum()
        zeros_val = (df['valor_aprovado'] == 0).sum()
        
        # Outliers estatísticos (Z-Score simplificado)
        mean_val = df['valor_aprovado'].mean()
        std_val = df['valor_aprovado'].std()
        outliers = df[df['valor_aprovado'] > (mean_val + 3 * std_val)]

        return {
            "registros_zero_qtd": zeros_qtd,
            "registros_zero_valor": zeros_val,
            "outliers_detectados": len(outliers)
        }

    def generate_pareto_quality(self, df, metrics):
        """Gera o Diagrama de Pareto para priorização de problemas (Aula 05)"""
        erros = {
            'Valores Zerados': metrics['registros_zero_valor'],
            'Nulos Detectados': df.isnull().sum().sum(),
            'Duplicidade Potencial': df.duplicated(subset=['municipio_codigo', 'subgrupo_procedimento', 'periodo']).sum()
        }
        
        pareto_df = pd.DataFrame(list(erros.items()), columns=['Tipo_Erro', 'Frequencia'])
        pareto_df = pareto_df.sort_values(by='Frequencia', ascending=False)
        pareto_df['%_Acumulada'] = (pareto_df['Frequencia'].cumsum() / pareto_df['Frequencia'].sum()) * 100

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(pareto_df['Tipo_Erro'], pareto_df['Frequencia'], color="steelblue")
        ax2 = ax.twinx()
        ax2.plot(pareto_df['Tipo_Erro'], pareto_df['%_Acumulada'], color="red", marker="D", ms=7)
        ax2.set_ylim(0, 110)
        
        plt.title("Diagrama de Pareto: Qualidade da Base SIA/SUS")
        plt.savefig(f"{self.output_path}pareto_qualidade.png")
        print(f"[SUCCESS] Gráfico de Pareto salvo em {self.output_path}")

    def run_full_audit(self):
        """Executa o workflow completo de auditoria"""
        df = self.fetch_data()
        print(f"--- Iniciando Auditoria em {len(df)} registros ---")
        
        # 1. Completude
        comp = self.audit_completeness(df)
        print(comp)
        
        # 2. Consistência
        metrics = self.audit_consistency(df)
        print(f"\nIndicadores de Consistência: {metrics}")
        
        # 3. Visualização (Pareto)
        self.generate_pareto_quality(df, metrics)
        
        # 4. Boxplot de Outliers para o Relatório
        plt.figure(figsize=(8, 4))
        sns.boxplot(x=df['valor_aprovado'], color='lightgreen')
        plt.title("Distribuição de Valores: Detecção de Outliers Monetários")
        plt.savefig(f"{self.output_path}boxplot_outliers.png")

if __name__ == "__main__":
    
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    
    auditor = DataQualityAuditor(DB_URL)
    auditor.run_full_audit()