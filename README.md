# Projeto DataSUS-SIA

Análise de dados do Sistema de Informação Ambulatorial (SIA) do DataSUS.

## 📁 Estrutura do Projeto

```
projeto-datasus-sia/
├── data/
│   ├── raw/           # Dados brutos baixados do DataSUS
│   ├── processed/    # Dados processados e limpos
│   └── outputs/      # Resultados das análises
├── database/
│   ├── schema.sql    # Schema do banco de dados
│   └── migrations/   # Migrações do banco
├── docs/
│   ├── presentation/ # Apresentações
│   ├── reports/      # Relatórios LaTeX
│   └── figures/      # Figuras e gráficos
├── notebooks/
│   ├── 01_qualidade_e_limpeza.ipynb
│   ├── 02_analise_univariada.ipynb
│   ├── 03_analise_bivariada.ipynb
│   ├── 04_analise_multivariada.ipynb
│   └── 05_modelos_lineares.ipynb
├── src/
│   ├── analysis/     # Módulos de análise
│   ├── crawler/     # Web crawler para下载 dados
│   ├── dashboard/   # Dashboard interativo
│   └── database_loader/ # Carregador de dados
├── main.py          # Script principal
├── pyproject.toml  # Configuração do projeto
└── Makefile        # Comandos úteis
```

## 🚀 Instalação

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -e .
```

## 📊 Dados

Os dados são provenientes do [DataSUS](http://datasus.saude.gov.br/) e incluem:

- **sia_br_qtd_*.csv**: Quantidades de procedimentos ambulatoriais
- **sia_br_valor_*.csv**: Valores dos procedimentos ambulatoriais

Período disponível: 2024-2026

## 🔧 Comandos

Use o Makefile para comandos rápidos:

```bash
make help     # Ver comandos disponíveis
make install # Instalar dependências
make clean   # Limpar arquivos temporários
```

## 📝 Licença

MIT License