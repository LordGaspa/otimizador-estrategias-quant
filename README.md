# Otimizador de Estratégias Quantitativas (Co-criado com IA)

Este é um dashboard web interativo, construído em Python e Streamlit, projetado para otimizar e testar estratégias de trading (Algo-Trading) no mercado de criptoativos.

A aplicação permite ao usuário selecionar um ativo, um tempo gráfico e múltiplos parâmetros de indicadores técnicos (Médias Móveis, ATR). Em seguida, ela executa um backtest completo, testando centenas de combinações contra até 8 anos de dados históricos da API da Binance.

**Nota de Desenvolvimento:** Este projeto foi arquitetado, desenvolvido e depurado usando Engenharia de Prompts Avançada, com o Google Gemini servindo como um parceiro de co-criação de código.

---

## 🚀 Funcionalidades Principais

* **Otimização Multi-Parâmetro:** Testa centenas de combinações de indicadores (`itertools.product`) para encontrar a estratégia mais lucrativa.
* **Backtesting Robusto:** Simula trades incluindo gestão de risco (Stop Loss baseado em ATR) e taxas de corretagem.
* **Integração de API:** Conecta-se à API da Binance para buscar até 8 anos de dados de velas (K-lines) para +30 ativos.
* **Dashboard Interativo:** Uma interface limpa (Streamlit) que permite ao usuário configurar a otimização e ver os 10 melhores resultados em um dataframe.
* **Caching de Performance:** Usa `@st.cache_data` para armazenar os dados da API, permitindo re-testes rápidos sem sobrecarregar a API.

---

## 🛠️ Stack de Tecnologia

* **Python**
* **Streamlit:** Para o dashboard web interativo.
* **Pandas:** Para manipulação de séries temporais e dados dos candles.
* **NumPy:** Para cálculos de indicadores e gestão de risco.
* **Binance API (python-binance):** Para coleta de dados.
* **Engenharia de Prompts (Gemini):** Para co-criação de código e lógica de backtesting.

---

## ⚙️ Como Executar (Instruções)

1.  Instale as dependências:
    `pip install streamlit pandas numpy python-binance`
2.  Execute o dashboard:
    `streamlit run app.py` (ou o nome do seu arquivo principal)
