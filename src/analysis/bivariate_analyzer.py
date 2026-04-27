import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr, chi2_contingency

class BivariateAnalyzer:
    def __init__(self, dataframe, output_path="../docs/reports/figures/"):
        self.df = dataframe
        self.output_path = output_path
        sns.set_theme(style="whitegrid")

    def plot_scatter_with_correlation(self, x, y):
        """Gráfico de Dispersão com Regressão e Coeficientes (Quant x Quant)"""
        p_corr, _ = pearsonr(self.df[x], self.df[y])
        s_corr, _ = spearmanr(self.df[x], self.df[y])
        
        plt.figure(figsize=(10, 6))
        sns.regplot(data=self.df, x=x, y=y, scatter_kws={'alpha':0.3}, line_kws={'color':'red'})
        plt.title(f"Relação: {x} vs {y}\nPearson: {p_corr:.2f} | Spearman: {s_corr:.2f}")
        
        plt.savefig(f"{self.output_path}bivariada_scatter_{x}_{y}.png")
        plt.show()

    def plot_box_by_category(self, quant_col, cat_col, top_n=10):
        """Comparação de Distribuições (Quali x Quant)"""
        top_cats = self.df[cat_col].value_counts().nlargest(top_n).index
        df_filtered = self.df[self.df[cat_col].isin(top_cats)]
        
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=df_filtered, x=quant_col, y=cat_col, palette="Set2")
        plt.title(f"Distribuição de {quant_col} por {cat_col} (Top {top_n})")
        
        plt.savefig(f"{self.output_path}bivariada_box_{quant_col}_{cat_col}.png")
        plt.show()

    def generate_contingency_table(self, col1, col2):
        """Tabela de Contingência e Teste Qui-Quadrado (Quali x Quali)"""
        ct = pd.crosstab(self.df[col1], self.df[col2])
        chi2, p, dof, ex = chi2_contingency(ct)
        
        print(f"--- Tabela de Contingência: {col1} vs {col2} ---")
        print(f"Teste Qui-Quadrado p-valor: {p:.4f}")
        return ct

    def plot_heatmap_correlation(self, columns):
        """Matriz de Correlação para múltiplas variáveis numéricas"""
        corr = self.df[columns].corr(method='spearman')
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0)
        plt.title("Matriz de Correlação (Spearman)")
        
        plt.savefig(f"{self.output_path}bivariada_heatmap.png")
        plt.show()