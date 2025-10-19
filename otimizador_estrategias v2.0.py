# -*- coding: utf-8 -*-
# DASHBOARD OTIMIZADOR DE ESTRATÉGIAS (v3.5 - New Assets & Type Hinting)
#
# OBJETIVO:
# - [NOVO] Adicionar BCH, HBAR, LTC, UNI, MATIC à lista de otimização.
# - [NOVO] Refatorar as anotações de tipo para maior clareza e robustez.
# ----------------------------------------------------------------------------

import warnings
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client
from itertools import product
from typing import List, Dict, Any

warnings.simplefilter(action="ignore", category=FutureWarning)

st.set_page_config(
    layout="wide",
    page_title="Otimizador de Estratégias",
    initial_sidebar_state="expanded",
)
st.title("🚀 Dashboard Otimizador de Estratégias")
st.markdown("Use os controles na barra lateral para configurar e iniciar a otimização.")

CAPITAL_INICIAL, TAXA_CORRETAGEM, ANOS_DE_DADOS_BACKTEST = 1000.0, 0.001, 8


@st.cache_data(ttl=60 * 60 * 6)
def carregar_dados(symbol: str, candle_period: str) -> pd.DataFrame:
    client = Client()
    start_date = (
        datetime.now() - timedelta(days=ANOS_DE_DADOS_BACKTEST * 365)
    ).strftime("%d %b, %Y")
    try:
        klines = client.get_historical_klines(symbol, candle_period, start_date)
        if not klines:
            return pd.DataFrame()
        df = pd.DataFrame(
            klines,
            columns=[
                "tempo_abertura",
                "abertura",
                "maxima",
                "minima",
                "fechamento",
                "volume",
                "tempo_fechamento",
                "volume_quote",
                "num_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )
        for col in ["abertura", "maxima", "minima", "fechamento", "volume"]:
            df[col] = pd.to_numeric(df[col])
        df["tempo_fechamento"] = pd.to_datetime(df["tempo_fechamento"], unit="ms")
        df.set_index("tempo_fechamento", inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados da API da Binance: {e}")
        return pd.DataFrame()


def calcular_indicadores(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy["media_rapida"] = (
        df_copy["fechamento"].rolling(window=params["media_rapida"]).mean()
    )
    df_copy["media_lenta"] = (
        df_copy["fechamento"].rolling(window=params["media_lenta"]).mean()
    )
    df_copy["media_filtro"] = (
        df_copy["fechamento"].rolling(window=params["media_filtro"]).mean()
    )
    ranges = pd.concat(
        [
            df_copy["maxima"] - df_copy["minima"],
            (df_copy["maxima"] - df_copy["fechamento"].shift()).abs(),
            (df_copy["minima"] - df_copy["fechamento"].shift()).abs(),
        ],
        axis=1,
    )
    true_range = ranges.max(axis=1)
    df_copy["atr"] = true_range.rolling(window=params["atr_periodo"]).mean()
    df_copy.dropna(inplace=True)
    return df_copy


def executar_backtest(df: pd.DataFrame, params: Dict[str, Any]) -> float:
    capital, posicionado, quantidade_ativo, stop_loss_price = (
        CAPITAL_INICIAL,
        False,
        0.0,
        0.0,
    )
    for i in range(1, len(df)):
        row, prev_row = df.iloc[i], df.iloc[i - 1]
        sinal_compra = (
            prev_row["media_rapida"] > prev_row["media_lenta"]
            and prev_row["fechamento"] > prev_row["media_filtro"]
        )
        sinal_venda_cruz = prev_row["media_rapida"] < prev_row["media_lenta"]
        if not posicionado and sinal_compra:
            preco_de_compra = row["abertura"]
            if preco_de_compra > 0:
                quantidade_compra = (capital / preco_de_compra) * (1 - TAXA_CORRETAGEM)
                capital, quantidade_ativo, posicionado = 0.0, quantidade_compra, True
                atr_da_compra = row["atr"] if not pd.isna(row["atr"]) else 0.0
                stop_loss_price = preco_de_compra - (
                    atr_da_compra * params["atr_multiplicador"]
                )
        elif posicionado:
            stop_ativado = row["minima"] < stop_loss_price
            if stop_ativado or sinal_venda_cruz:
                preco_saida = stop_loss_price if stop_ativado else row["abertura"]
                if preco_saida > 0:
                    capital = (quantidade_ativo * preco_saida) * (1 - TAXA_CORRETAGEM)
                    quantidade_ativo, posicionado = 0.0, False
    return float(
        capital
        if not posicionado
        else (quantidade_ativo * df.iloc[-1]["fechamento"]) * (1 - TAXA_CORRETAGEM)
    )


def analisar_resultados(
    capital_final: float, retorno_bh_pct_fixo: float
) -> Dict[str, float]:
    retorno_estrategia_pct = (
        (capital_final - CAPITAL_INICIAL) / CAPITAL_INICIAL
    ) * 100.0
    return {
        "retorno_estrategia_pct": retorno_estrategia_pct,
        "retorno_bh_pct": retorno_bh_pct_fixo,
        "supera_bh_pct": retorno_estrategia_pct - retorno_bh_pct_fixo,
    }


st.sidebar.title("⚙️ Controles de Otimização")

ativo_para_otimizar = st.sidebar.selectbox(
    "1. Selecione o Ativo:",
    (
        # Lista Recomendada - Foco em Ativos com Histórico
        "ADAUSDT",
        "ARBUSDT",
        "AVAXUSDT",
        "AXSUSDT",
        "BCHUSDT",
        "BNBUSDT",
        "BTCUSDT",
        "CAKEUSDT",
        "DOGEUSDT",
        "ETHUSDT",
        "FETUSDT",
        "FLOKIUSDT",
        "HBARUSDT",
        "IMXUSDT",  # [NOVO] Adicionado
        "INJUSDT",
        "LDOUSDT",
        "LINKUSDT",
        "MANAUSDT",
        "NEARUSDT",
        "RNDRUSDT",
        "SANDUSDT",
        "SHIBUSDT",
        "SOLUSDT",
        "SUIUSDT",
        "TAOUSDT",
        "TRXUSDT",
        "UNIUSDT",
        "WLDUSDT",
        "XLMUSDT",
        "XRPUSDT",
    ),
)
tempos_graficos = {
    "4 Horas": Client.KLINE_INTERVAL_4HOUR,
    "6 Horas": Client.KLINE_INTERVAL_6HOUR,
    "8 Horas": Client.KLINE_INTERVAL_8HOUR,
    "12 Horas": Client.KLINE_INTERVAL_12HOUR,
    "1 Dia": Client.KLINE_INTERVAL_1DAY,
}
periodo_candle_str = st.sidebar.selectbox(
    "2. Selecione o Tempo Gráfico:", list(tempos_graficos.keys()), index=3
)
periodo_candle = tempos_graficos[periodo_candle_str]

st.sidebar.markdown("---")
st.sidebar.subheader("3. Selecione os Parâmetros para Testar")
opcoes_media_rapida = [5, 9, 12, 15, 21]
opcoes_media_lenta = [40, 60, 80, 100, 120]
opcoes_media_filtro = [150, 200, 250]
opcoes_atr_periodo = [10, 14, 20]
opcoes_atr_multi = [2.0, 2.5, 3.0, 3.5]
params_selecionados = {
    "media_rapida": st.sidebar.multiselect(
        "Média Rápida", opcoes_media_rapida, default=[9, 12]
    ),
    "media_lenta": st.sidebar.multiselect(
        "Média Lenta", opcoes_media_lenta, default=[60, 80]
    ),
    "media_filtro": st.sidebar.multiselect(
        "Média Filtro de Tendência", opcoes_media_filtro, default=[200]
    ),
    "atr_periodo": st.sidebar.multiselect(
        "Período ATR", opcoes_atr_periodo, default=[14]
    ),
    "atr_multiplicador": st.sidebar.multiselect(
        "Multiplicador ATR", opcoes_atr_multi, default=[2.5, 3.0]
    ),
}

st.sidebar.markdown("---")
iniciar_otimizacao = st.sidebar.button("▶️ Iniciar Otimização", use_container_width=True)

if iniciar_otimizacao:
    if any(not v for v in params_selecionados.values()):
        st.error("Erro: Por favor, selecione pelo menos uma opção para cada parâmetro.")
    else:
        chaves = params_selecionados.keys()
        valores = params_selecionados.values()
        combinacoes = [dict(zip(chaves, v)) for v in product(*valores)]
        st.info(
            f"🔬 Encontradas {len(combinacoes)} combinações. Carregando dados para {ativo_para_otimizar}..."
        )
        dados_brutos = carregar_dados(ativo_para_otimizar, periodo_candle)
        if dados_brutos.empty or len(dados_brutos) < 2:
            st.error(
                "Não foi possível carregar dados suficientes para o backtest. Verifique o ativo e a conexão."
            )
        else:
            dados_para_bh = dados_brutos.iloc[1:]
            preco_inicial_bh_fixo = dados_para_bh["abertura"].iloc[0]
            preco_final_bh_fixo = dados_para_bh["fechamento"].iloc[-1]
            retorno_bh_pct_fixo = (
                (
                    (
                        (preco_final_bh_fixo - preco_inicial_bh_fixo)
                        / preco_inicial_bh_fixo
                    )
                    * 100.0
                )
                if preco_inicial_bh_fixo > 0
                else 0.0
            )
            todos_os_resultados: List[Dict[str, Any]] = []
            barra_progresso = st.progress(0)
            with st.spinner("Executando backtests... Isso pode levar vários minutos."):
                for i, params in enumerate(combinacoes):
                    if params["media_lenta"] > params["media_rapida"]:
                        dados_processados = calcular_indicadores(
                            dados_brutos.copy(), params
                        )
                        if not dados_processados.empty:
                            capital_final = executar_backtest(dados_processados, params)
                            resultados = analisar_resultados(
                                capital_final, retorno_bh_pct_fixo
                            )
                            todos_os_resultados.append({**params, **resultados})
                    barra_progresso.progress((i + 1) / len(combinacoes))
            st.success("🎉 Otimização Concluída!")
            st.markdown("---")
            if not todos_os_resultados:
                st.warning("Nenhuma combinação válida foi encontrada ou testada.")
            else:
                df_resultados = pd.DataFrame(todos_os_resultados)
                df_resultados_ordenados = df_resultados.sort_values(
                    by="supera_bh_pct", ascending=False
                )
                st.subheader(
                    f"🏆 TOP 10 Melhores Combinações para {ativo_para_otimizar} ({periodo_candle_str})"
                )
                top_10 = df_resultados_ordenados.head(10).copy()
                top_10["retorno_estrategia_pct"] = top_10["retorno_estrategia_pct"].map(
                    "{:,.2f}%".format
                )
                top_10["retorno_bh_pct"] = top_10["retorno_bh_pct"].map(
                    "{:,.2f}%".format
                )
                top_10["supera_bh_pct"] = top_10["supera_bh_pct"].map("{:,.2f}%".format)
                st.dataframe(top_10)
else:
    st.info("Aguardando configuração para iniciar a otimização.")
