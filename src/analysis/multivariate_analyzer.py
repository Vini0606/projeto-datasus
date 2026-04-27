import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

class MultivariateAnalyzer:
    def __init__(self, dataframe, output_path="../docs/reports/figures/"):
        self.df = dataframe
        self.output_path = output_path
        self.scaler = StandardScaler()
        sns.set_theme(style="whitegrid")

    def prepare_cluster_data(self, group_col, metrics):
        """Agrupa e normaliza os dados para clusterização"""
        grouped = self.df.groupby(group_col)[metrics].sum().reset_index()
        # Escalonamento: média 0 e variância 1
        scaled_data = self.scaler.fit_transform(grouped[metrics])
        return grouped, scaled_data

    def plot_pca_variance(self, scaled_data):
        """Análise de Variância Explicada pelo PCA"""
        pca = PCA()
        pca.fit(scaled_data)
        
        plt.figure(figsize=(8, 5))
        plt.plot(range(1, len(pca.explained_variance_ratio_) + 1), 
                 pca.explained_variance_ratio_.cumsum(), marker='o', linestyle='--')
        plt.title("Variância Acumulada pelo PCA")
        plt.xlabel("Número de Componentes")
        plt.ylabel("Variância Explicada")
        
        plt.savefig(f"{self.output_path}multivariada_pca_variance.png")
        plt.show()

    def run_kmeans(self, grouped_df, scaled_data, n_clusters=3):
        """Executa K-Means e adiciona labels ao dataframe original"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        grouped_df['cluster'] = kmeans.fit_predict(scaled_data)
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=grouped_df, x=grouped_df.columns[1], y=grouped_df.columns[2], 
                        hue='cluster', palette='viridis', s=100)
        plt.title(f"Segmentação por Cluster (K={n_clusters})")
        
        plt.savefig(f"{self.output_path}multivariada_clusters.png")
        plt.show()
        return grouped_df