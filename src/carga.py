"""Leitura e limpeza dos CSVs de e-commerce em data/.

Os arquivos não seguem um padrão único (separador, BOM, separador decimal),
por isso cada tabela tem seu próprio leitor.
"""
from pathlib import Path

import pandas as pd

PREFIXO = "Dados do ecommerce - "


def _decimal_virgula(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False))


def carregar_vendas(pasta: Path) -> pd.DataFrame:
    df = pd.read_csv(pasta / f"{PREFIXO}Vendas.csv", sep=";", encoding="utf-8-sig")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    df["preco_unitario"] = _decimal_virgula(df["preco_unitario"])
    df["receita"] = df["quantidade"] * df["preco_unitario"]
    return df


def carregar_clientes(pasta: Path) -> pd.DataFrame:
    df = pd.read_csv(pasta / f"{PREFIXO}clientes.csv", sep=";", encoding="utf-8-sig")
    df["data_cadastro"] = pd.to_datetime(df["data_cadastro"])
    # "Srta, Amanda Sousa" -> "Srta. Amanda Sousa"
    df["nome_cliente"] = df["nome_cliente"].str.replace(
        r"^(Sra|Srta|Sr|Dra|Dr),\s*", r"\1. ", regex=True
    )
    return df


def carregar_produtos(pasta: Path) -> pd.DataFrame:
    df = pd.read_csv(pasta / f"{PREFIXO}produtos.csv", sep=";", encoding="utf-8-sig")
    df["data_criacao"] = pd.to_datetime(df["data_criacao"])
    return df


def carregar_competidores(pasta: Path) -> tuple[pd.DataFrame, int]:
    """Retorna o DataFrame limpo e quantas linhas tiveram o id_produto corrigido."""
    df = pd.read_csv(pasta / f"{PREFIXO}preco_competidores.csv", sep=",")
    id_limpo = df["id_produto"].str.split().str[0]
    corrigidas = int((id_limpo != df["id_produto"]).sum())
    df["id_produto"] = id_limpo
    df["preco_concorrente"] = _decimal_virgula(df["preco_concorrente"])
    df["data_coleta"] = pd.to_datetime(df["data_coleta"])
    return df, corrigidas


def carregar(pasta: Path) -> dict:
    competidores, corrigidas = carregar_competidores(pasta)
    return {
        "vendas": carregar_vendas(pasta),
        "clientes": carregar_clientes(pasta),
        "produtos": carregar_produtos(pasta),
        "competidores": competidores,
        "competidores_corrigidos": corrigidas,
    }


def base_analitica(dados: dict) -> pd.DataFrame:
    """Vendas enriquecidas com produto e cliente (left join: órfãos são mantidos)."""
    return dados["vendas"].merge(
        dados["produtos"], on="id_produto", how="left"
    ).merge(dados["clientes"], on="id_cliente", how="left")
