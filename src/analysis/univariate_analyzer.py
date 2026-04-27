import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis

class UnivariateAnalyzer:
    
    def __init__(self, dataframe, output_path="../docs/reports/figures/"):
        self.df = dataframe
        self.output_path = output_path
        sns.set_theme(style="whitegrid")

    def get_summary_statistics(self, column):
        """Calcula estatísticas conforme o fluxograma (Tendência Central e Dispersão)"""
        data = self.df[column]
        stats = {
            "Média": data.mean(),
            "Mediana": data.median(),
            "Moda": data.mode()[0] if not data.mode().empty else np.nan,
            "Desvio Padrão": data.std(),
            "Variância": data.var(),
            "Coef. Variação (%)": (data.std() / data.mean()) * 100,
            "Assimetria": skew(data.dropna()),
            "Curtose": kurtosis(data.dropna())
        }
        return pd.Series(stats)

    def plot_distribution(self, column, color="teal"):
        """Gera Histogramas e Densidade (KDE)"""
        plt.figure(figsize=(10, 5))
        sns.histplot(self.df[column], kde=True, color=color)
        plt.title(f"Distribuição Univariada: {column}")
        plt.xlabel(column)
        plt.ylabel("Frequência")
        
        filename = f"univariada_dist_{column}.png"
        plt.savefig(f"{self.output_path}{filename}")
        plt.show()

    def plot_outliers(self, column, color="lightcoral"):
        """Gera Boxplots para identificação de valores extremos"""
        plt.figure(figsize=(10, 4))
        sns.boxplot(x=self.df[column], color=color)
        plt.title(f"Análise de Outliers: {column}")
        
        filename = f"univariada_box_{column}.png"
        plt.savefig(f"{self.output_path}{filename}")
        plt.show()

    def analyze_categorical(self, column, top_n=15):
        """Analisa variáveis qualitativas (Frequência e Pareto)"""
        freq = self.df[column].value_counts().head(top_n)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=freq.values, y=freq.index, palette="viridis")
        plt.title(f"Top {top_n} Categorias: {column}")
        plt.xlabel("Contagem")
        
        filename = f"univariada_cat_{column}.png"
        plt.savefig(f"{self.output_path}{filename}")
        plt.show()
        
        return freq