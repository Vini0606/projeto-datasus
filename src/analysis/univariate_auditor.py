import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

class UnivariateAuditor:
    
    def __init__(self, df, output_path="../docs/reports/figures/"):
        self.df = df
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)
        sns.set_theme(style="whitegrid")

    def analisar_tudo(self, cols_to_include=None, cols_to_exclude=None):
        """
        Executa a análise com suporte a filtros de colunas.
        
        :param cols_to_include: Lista de colunas para analisar (ignora as outras).
        :param cols_to_exclude: Lista de colunas para pular (como IDs).
        """
        # Define quais colunas serão processadas
        colunas = self.df.columns.tolist()
        
        if cols_to_include:
            colunas = [c for c in colunas if c in cols_to_include]
        
        if cols_to_exclude:
            colunas = [c for c in colunas if c not in cols_to_exclude]

        for coluna in colunas:
            print(f"\n{'='*30}")
            print(f"ANALISANDO COLUNA: {coluna}")
            print(f"{'='*30}")
            
            if self._eh_quantitativa(coluna):
                self._analise_quantitativa(coluna)
            else:
                self._analise_qualitativa(coluna)

    def _eh_quantitativa(self, coluna):
        return pd.api.types.is_numeric_dtype(self.df[coluna]) and self.df[coluna].nunique() > 10

    def _analise_qualitativa(self, coluna):
        """Fluxo: Frequências -> Moda -> Gráfico de Barras."""
        freq_abs = self.df[coluna].value_counts()
        freq_rel = self.df[coluna].value_counts(normalize=True) * 100
        tabela = pd.DataFrame({
            'Frequência Absoluta': freq_abs,
            'Frequência Relativa (%)': freq_rel
        })
        
        print("\n--- Tabela de Frequências ---")
        print(tabela.head(15)) # Limitado para não poluir o console
        print(f"\nModa: {self.df[coluna].mode()[0]}")

        plt.figure(figsize=(10, 5))
        # Seleciona apenas o top 10 para visibilidade no gráfico
        sns.countplot(data=self.df, y=coluna, palette='viridis', 
                      order=self.df[coluna].value_counts().index[:10])
        plt.title(f"Distribuição de Frequências (Top 10): {coluna}")
        plt.savefig(f"{self.output_path}univariada_cat_{coluna}.png")
        plt.show()

    def _analise_quantitativa(self, coluna):
        """Fluxo: Descritivas -> Forma -> Normalidade -> Outliers -> Visualização."""
        dados = self.df[coluna].dropna()
        
        # 1. Medidas de Tendência Central e Dispersão
        stats_desc = dados.describe()
        cv = (dados.std() / dados.mean()) * 100
        erro_padrao = stats.sem(dados)
        
        print("\n--- Estatísticas Descritivas ---")
        print(stats_desc)
        print(f"Coeficiente de Variação: {cv:.2f}%")
        print(f"Erro Padrão da Média: {erro_padrao:.4f}")

        # 2. Medidas de Forma
        print("\n--- Medidas de Forma ---")
        print(f"Assimetria (Skewness): {dados.skew():.4f}")
        print(f"Curtose (Kurtosis): {dados.kurtosis():.4f}")

        # 3. Teste de Normalidade (Shapiro-Wilk)
        # Amostragem para evitar erro em datasets gigantes
        stat_norm, p_valor = stats.shapiro(dados.sample(min(len(dados), 5000)))
        print("\n--- Teste de Normalidade (Shapiro-Wilk) ---")
        print(f"Estatística: {stat_norm:.4f}, p-valor: {p_valor:.4e}")
        resultado_norm = "Normal" if p_valor > 0.05 else "Não segue distribuição Normal"
        print(f"Resultado: {resultado_norm}")

        # 4. Detecção de Outliers (IQR)
        q1, q3 = dados.quantile([0.25, 0.75])
        iqr = q3 - q1
        lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = dados[(dados < lim_inf) | (dados > lim_sup)]
        print(f"\nOutliers Detectados: {len(outliers)} (Limites: {lim_inf:.2f} a {lim_sup:.2f})")

        # 5. Visualizações
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.histplot(dados, kde=True, ax=axes[0], color='skyblue')
        axes[0].set_title(f"Histograma e Densidade: {coluna}")
        sns.boxplot(x=dados, ax=axes[1], color='lightcoral')
        axes[1].set_title(f"Boxplot: {coluna}")
        
        plt.tight_layout()
        plt.savefig(f"{self.output_path}univariada_quant_{coluna}.png")
        plt.show()