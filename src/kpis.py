"""Validação dos joins e cálculo dos KPIs.

Cada tabela agregada é salva como CSV em output/kpis/ para servir de contexto
compacto em análises posteriores; os números de destaque vão para kpis.json.
"""
import pandas as pd

SEM_CADASTRO = "Sem cadastro"
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def validar(dados: dict) -> dict:
    v, c, p, k = (dados[n] for n in ("vendas", "clientes", "produtos", "competidores"))
    orfas_produto = v[~v["id_produto"].isin(p["id_produto"])]
    return {
        "linhas": {"vendas": len(v), "clientes": len(c), "produtos": len(p), "competidores": len(k)},
        "duplicados": {
            "vendas.id_venda": int(v["id_venda"].duplicated().sum()),
            "clientes.id_cliente": int(c["id_cliente"].duplicated().sum()),
            "produtos.id_produto": int(p["id_produto"].duplicated().sum()),
        },
        "orfaos": {
            "vendas→clientes": int((~v["id_cliente"].isin(c["id_cliente"])).sum()),
            "vendas→produtos": len(orfas_produto),
            "competidores→produtos": int((~k["id_produto"].isin(p["id_produto"])).sum()),
        },
        "orfaos_produto_ids": sorted(orfas_produto["id_produto"].unique()),
        "receita_orfa": float(orfas_produto["receita"].sum()),
        "nulos": {n: int(dados[n].isna().sum().sum()) for n in ("vendas", "clientes", "produtos", "competidores")},
        "quantidade_invalida": int((v["quantidade"] <= 0).sum()),
        "preco_invalido": int((v["preco_unitario"] <= 0).sum()),
        "produtos_com_concorrente": int(k["id_produto"].nunique()),
        "competidores_corrigidos": dados["competidores_corrigidos"],
        "periodo_vendas": (v["data_venda"].min(), v["data_venda"].max()),
        "periodo_coleta": (k["data_coleta"].min(), k["data_coleta"].max()),
    }


def _participacao(df: pd.DataFrame, col: str = "receita") -> pd.DataFrame:
    df["participacao_pct"] = (df[col] / df[col].sum() * 100).round(2)
    return df


def calcular(dados: dict, base: pd.DataFrame) -> tuple[dict, dict]:
    """Retorna (resumo, tabelas)."""
    base = base.copy()
    base["categoria"] = base["categoria"].fillna(SEM_CADASTRO)
    base["marca"] = base["marca"].fillna(SEM_CADASTRO)
    base["nome_produto"] = base["nome_produto"].fillna(base["id_produto"])
    base["data"] = base["data_venda"].dt.normalize()
    t = {}

    # Série temporal
    diaria = base.groupby("data").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count"), itens=("quantidade", "sum")
    ).reset_index()
    diaria["receita_media_movel_7d"] = diaria["receita"].rolling(7, min_periods=1).mean().round(2)
    t["serie_diaria"] = diaria

    semanal = base.groupby(base["data_venda"].dt.to_period("W-SUN").dt.start_time).agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count")
    ).reset_index(names="semana_inicio")
    semanal["variacao_pct"] = (semanal["receita"].pct_change() * 100).round(2)
    t["serie_semanal"] = semanal

    base["dia_semana"] = base["data_venda"].dt.dayofweek
    base["hora"] = base["data_venda"].dt.hour
    dow = base.groupby("dia_semana").agg(receita=("receita", "sum"), pedidos=("id_venda", "count"))
    dow = dow.reindex(range(7), fill_value=0).reset_index()
    dow["dia"] = dow["dia_semana"].map(dict(enumerate(DIAS_SEMANA)))
    t["dia_semana"] = dow
    t["hora"] = base.groupby("hora").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count")
    ).reindex(range(24), fill_value=0).reset_index()

    # Canais
    canais = base.groupby("canal_venda").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count"),
        itens=("quantidade", "sum"), clientes=("id_cliente", "nunique"),
    ).reset_index()
    canais["ticket_medio"] = (canais["receita"] / canais["pedidos"]).round(2)
    t["canais"] = _participacao(canais).sort_values("receita", ascending=False)

    # Categorias, marcas, produtos
    cat = base.groupby("categoria").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count"), itens=("quantidade", "sum")
    ).reset_index()
    t["categorias"] = _participacao(cat).sort_values("receita", ascending=False)
    t["categoria_canal"] = base.pivot_table(
        index="categoria", columns="canal_venda", values="receita", aggfunc="sum", fill_value=0
    ).reset_index()

    marcas = base.groupby("marca").agg(receita=("receita", "sum"), itens=("quantidade", "sum")).reset_index()
    t["marcas"] = _participacao(marcas).sort_values("receita", ascending=False)

    prod = base.groupby(["id_produto", "nome_produto", "categoria", "marca"]).agg(
        receita=("receita", "sum"), itens=("quantidade", "sum"), pedidos=("id_venda", "count"),
        preco_medio_vendido=("preco_unitario", "mean"),
    ).reset_index()
    t["produtos"] = _participacao(prod).sort_values("receita", ascending=False)

    produtos = dados["produtos"]
    sem_venda = produtos[~produtos["id_produto"].isin(base["id_produto"])]
    t["produtos_sem_venda"] = sem_venda[["id_produto", "nome_produto", "categoria", "marca", "preco_atual"]]

    # Preço praticado x preço de tabela (só produtos cadastrados)
    preco = prod.merge(produtos[["id_produto", "preco_atual"]], on="id_produto")
    preco["desconto_pct"] = ((1 - preco["preco_medio_vendido"] / preco["preco_atual"]) * 100).round(2)
    t["preco_praticado"] = preco[
        ["id_produto", "nome_produto", "categoria", "preco_atual", "preco_medio_vendido", "desconto_pct"]
    ].sort_values("desconto_pct", ascending=False)

    # Clientes e regiões
    clientes = dados["clientes"]
    uf = base.groupby("estado").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count"), clientes=("id_cliente", "nunique")
    ).reset_index()
    t["estados"] = _participacao(uf).sort_values("receita", ascending=False)

    ref = base["data_venda"].max()
    rfm = base.groupby("id_cliente").agg(
        ultima_compra=("data_venda", "max"), primeira_compra=("data_venda", "min"),
        pedidos=("id_venda", "count"), receita=("receita", "sum"),
    ).reset_index().merge(clientes, on="id_cliente", how="left")
    rfm["recencia_dias"] = (ref - rfm["ultima_compra"]).dt.days
    rfm["ticket_medio"] = (rfm["receita"] / rfm["pedidos"]).round(2)
    rfm["dias_cadastro_ate_1a_compra"] = (rfm["primeira_compra"] - rfm["data_cadastro"]).dt.days
    rfm["cliente_novo_no_periodo"] = rfm["data_cadastro"] >= base["data_venda"].min()
    t["clientes"] = rfm[
        ["id_cliente", "nome_cliente", "estado", "pedidos", "receita", "ticket_medio",
         "recencia_dias", "dias_cadastro_ate_1a_compra", "cliente_novo_no_periodo"]
    ].sort_values("receita", ascending=False)

    # Concorrência (coleta de um único dia, comparada ao preco_atual)
    k = dados["competidores"]
    comp = k.merge(produtos[["id_produto", "nome_produto", "categoria", "preco_atual"]], on="id_produto")
    comp["diferenca_pct"] = (comp["preco_atual"] / comp["preco_concorrente"] - 1) * 100
    por_conc = comp.groupby("nome_concorrente").agg(
        produtos=("id_produto", "nunique"),
        diferenca_media_pct=("diferenca_pct", "mean"),
        vezes_mais_barato_que_nos=("diferenca_pct", lambda s: int((s > 0).sum())),
    ).reset_index()
    por_conc["diferenca_media_pct"] = por_conc["diferenca_media_pct"].round(2)
    t["concorrentes"] = por_conc.sort_values("diferenca_media_pct", ascending=False)

    idx = comp.groupby(["id_produto", "nome_produto", "categoria", "preco_atual"]).agg(
        preco_medio_concorrencia=("preco_concorrente", "mean"),
        menor_preco_concorrencia=("preco_concorrente", "min"),
        maior_preco_concorrencia=("preco_concorrente", "max"),
        concorrentes=("nome_concorrente", "nunique"),
    ).reset_index()
    idx["indice_preco"] = (idx["preco_atual"] / idx["preco_medio_concorrencia"]).round(3)
    idx["posicao"] = "Intermediário"
    idx.loc[idx["preco_atual"] < idx["menor_preco_concorrencia"], "posicao"] = "Mais barato que todos"
    idx.loc[idx["preco_atual"] > idx["maior_preco_concorrencia"], "posicao"] = "Mais caro que todos"
    idx = idx.merge(prod[["id_produto", "receita"]], on="id_produto", how="left").fillna({"receita": 0})
    t["indice_preco_produto"] = idx.sort_values("indice_preco", ascending=False)

    idx_cat = idx.groupby("categoria").agg(
        indice_preco_medio=("indice_preco", "mean"), produtos=("id_produto", "count"),
        mais_caro_que_todos=("posicao", lambda s: int((s == "Mais caro que todos").sum())),
    ).reset_index()
    idx_cat["indice_preco_medio"] = idx_cat["indice_preco_medio"].round(3)
    idx_cat = idx_cat.merge(
        idx.groupby("categoria").agg(receita=("receita", "sum"),
                                     produtos_sem_venda=("receita", lambda s: int((s == 0).sum()))),
        on="categoria",
    )
    t["indice_preco_categoria"] = idx_cat.sort_values("indice_preco_medio", ascending=False)
    dobro = idx_cat[idx_cat["indice_preco_medio"] >= 1.9]

    sv = t["produtos_sem_venda"].groupby("categoria").size().rename("produtos_sem_venda").reset_index()
    t["produtos_sem_venda_categoria"] = sv.sort_values("produtos_sem_venda", ascending=False)

    # Resumo
    pedidos = len(base)
    receita = float(base["receita"].sum())
    ini, fim = base["data_venda"].min(), base["data_venda"].max()
    posicoes = idx["posicao"].value_counts()
    top_cat = t["categorias"].iloc[0]
    top_canal = t["canais"].iloc[0]
    melhor_dia = diaria.loc[diaria["receita"].idxmax()]
    top5_clientes = t["clientes"].head(5)["receita"].sum() / receita * 100
    resumo = {
        "periodo_inicio": ini.strftime("%Y-%m-%d"),
        "periodo_fim": fim.strftime("%Y-%m-%d"),
        "dias": int((fim.normalize() - ini.normalize()).days) + 1,
        "receita_total": round(receita, 2),
        "pedidos": pedidos,
        "itens": int(base["quantidade"].sum()),
        "ticket_medio": round(receita / pedidos, 2),
        "itens_por_pedido": round(base["quantidade"].mean(), 2),
        "receita_media_dia": round(float(diaria["receita"].mean()), 2),
        "clientes_ativos": int(base["id_cliente"].nunique()),
        "clientes_cadastrados": len(clientes),
        "produtos_vendidos": int(base.loc[base["categoria"] != SEM_CADASTRO, "id_produto"].nunique()),
        "produtos_cadastrados": len(produtos),
        "produtos_sem_venda": len(sem_venda),
        "canal_lider": top_canal["canal_venda"],
        "canal_lider_pct": float(top_canal["participacao_pct"]),
        "categoria_lider": top_cat["categoria"],
        "categoria_lider_pct": float(top_cat["participacao_pct"]),
        "melhor_dia": melhor_dia["data"].strftime("%Y-%m-%d"),
        "melhor_dia_receita": round(float(melhor_dia["receita"]), 2),
        "top5_clientes_pct": round(float(top5_clientes), 2),
        "desconto_medio_pct": round(float(preco["desconto_pct"].mean()), 2),
        "indice_preco_medio": round(float(idx["indice_preco"].mean()), 3),
        "indice_preco_mediano": round(float(idx["indice_preco"].median()), 3),
        # Categorias precificadas no dobro (ou mais) do mercado distorcem a média
        "categorias_preco_dobro": dobro["categoria"].tolist(),
        "produtos_preco_dobro": int(dobro["produtos"].sum()),
        "receita_preco_dobro": round(float(dobro["receita"].sum()), 2),
        "indice_dobro": round(float(dobro["indice_preco_medio"].mean()), 2) if len(dobro) else None,
        "indice_preco_medio_sem_anomalia": round(
            float(idx.loc[~idx["categoria"].isin(dobro["categoria"]), "indice_preco"].mean()), 3
        ),
        "produtos_mais_caros_que_todos": int(posicoes.get("Mais caro que todos", 0)),
        "produtos_mais_baratos_que_todos": int(posicoes.get("Mais barato que todos", 0)),
        "produtos_intermediarios": int(posicoes.get("Intermediário", 0)),
        "data_coleta_concorrencia": k["data_coleta"].min().strftime("%Y-%m-%d"),
    }
    return resumo, t
