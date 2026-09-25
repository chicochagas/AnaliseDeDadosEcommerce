"""Monta o dashboard HTML (Jinja2 + Chart.js) e o relatório de qualidade dos dados."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

CANAIS = {"ecommerce": "E-commerce", "loja_fisica": "Loja física"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def brl(valor: float, casas: int = 0) -> str:
    s = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}%".replace(".", ",")


def num(valor: float, casas: int = 0) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(d) -> str:
    d = pd.Timestamp(d)
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def _graficos(r: dict, t: dict) -> dict:
    diaria = t["serie_diaria"]
    cat = t["categorias"]
    cat_canal = t["categoria_canal"].set_index("categoria").loc[cat["categoria"]]
    idx_cat = t["indice_preco_categoria"]
    idx_normal = idx_cat[~idx_cat["categoria"].isin(r["categorias_preco_dobro"])]
    idx_normal = idx_normal.sort_values("indice_preco_medio", ascending=False)
    top = t["produtos"].head(10)
    uf = t["estados"]
    return {
        "diaria": {
            "labels": [d.strftime("%d/%m") for d in diaria["data"]],
            "receita": diaria["receita"].round(2).tolist(),
            "media": diaria["receita_media_movel_7d"].tolist(),
            "destaque": int(diaria["receita"].idxmax()),
        },
        "dia_semana": {
            "labels": t["dia_semana"]["dia"].tolist(),
            "receita": t["dia_semana"]["receita"].round(2).tolist(),
        },
        "categoria_canal": {
            "labels": cat["categoria"].tolist(),
            "series": [
                {"nome": CANAIS[c], "valores": cat_canal[c].round(2).tolist()}
                for c in ("ecommerce", "loja_fisica")
            ],
        },
        "top_produtos": {
            "labels": top["nome_produto"].tolist(),
            "receita": top["receita"].round(2).tolist(),
        },
        "estados": {"labels": uf["estado"].tolist(), "receita": uf["receita"].round(2).tolist()},
        "indice_categoria": {
            "labels": idx_normal["categoria"].tolist(),
            "diferenca": ((idx_normal["indice_preco_medio"] - 1) * 100).round(2).tolist(),
        },
        "concorrentes": {
            "labels": t["concorrentes"]["nome_concorrente"].tolist(),
            "diferenca": t["concorrentes"]["diferenca_media_pct"].tolist(),
        },
    }


def _insights(r: dict, t: dict) -> dict:
    semanal = t["serie_semanal"]
    dow = t["dia_semana"]
    fds = dow.loc[dow["dia_semana"] >= 5, "receita"].mean()
    util = dow.loc[dow["dia_semana"] < 5, "receita"].mean()
    canais = t["canais"].set_index("canal_venda")
    top = t["produtos"].iloc[0]
    top_uf = t["estados"].iloc[0]
    clientes = t["clientes"]
    return {
        "tempo": (
            f"A receita média é de {brl(r['receita_media_dia'])} por dia e fica estável nas semanas "
            f"completas (entre {brl(semanal['receita'].iloc[1:].min())} e "
            f"{brl(semanal['receita'].iloc[1:].max())}). Sábado e domingo faturam "
            f"{pct((fds / util - 1) * 100, 0)} a mais que a média dos dias úteis."
        ),
        "canais": (
            f"O e-commerce responde por {pct(canais.loc['ecommerce', 'participacao_pct'])} da receita, "
            f"com ticket de {brl(canais.loc['ecommerce', 'ticket_medio'], 2)} contra "
            f"{brl(canais.loc['loja_fisica', 'ticket_medio'], 2)} na loja física. "
            + (f"Todos os {r['clientes_ativos']} clientes compraram nos dois canais."
               if (canais["clientes"] == r["clientes_ativos"]).all() else "")
        ),
        "produtos": (
            f"{r['categoria_lider']} lidera com {pct(r['categoria_lider_pct'])} da receita. "
            f"Só o produto {top['nome_produto']} gerou {brl(top['receita'])} "
            f"({pct(top['participacao_pct'])} do total), e os 10 maiores somam "
            f"{pct(t['produtos']['participacao_pct'].head(10).sum(), 0)}. "
            f"{r['produtos_sem_venda']} dos {r['produtos_cadastrados']} produtos não venderam nada no período."
        ),
        "clientes": (
            f"A base é pequena ({r['clientes_ativos']} clientes) e bem distribuída: os 5 maiores somam "
            f"{pct(r['top5_clientes_pct'])} da receita, e {top_uf['estado']} é o estado que mais compra "
            f"({pct(top_uf['participacao_pct'])}). Cada cliente fez, em média, "
            f"{num(clientes['pedidos'].mean(), 0)} pedidos em {r['dias']} dias."
        ),
        "concorrencia": (
            f"Fora a anomalia de {', '.join(r['categorias_preco_dobro'])}, o preço está alinhado ao mercado: "
            f"o índice médio é {num(r['indice_preco_medio_sem_anomalia'], 3)} (1,000 = média dos concorrentes). "
            f"Somos o preço mais baixo em apenas {r['produtos_mais_baratos_que_todos']} produtos."
        ),
    }


def _tabela(df: pd.DataFrame, colunas: dict, formatos: dict) -> dict:
    linhas = []
    for _, row in df.iterrows():
        linhas.append([formatos.get(c, str)(row[c]) for c in colunas])
    return {"cabecalho": list(colunas.values()), "linhas": linhas,
            "numericas": [i for i, c in enumerate(colunas) if c in formatos]}


def gerar_html(r: dict, t: dict, q: dict, templates: Path, destino: Path) -> None:
    env = Environment(loader=FileSystemLoader(templates), autoescape=True)
    canais = t["canais"].assign(canal=lambda d: d["canal_venda"].map(CANAIS))
    tenis = t["indice_preco_produto"]
    tenis = tenis[tenis["categoria"].isin(r["categorias_preco_dobro"])]
    por_produto = t["indice_preco_produto"]["concorrentes"]
    ctx = {
        "r": r,
        "canal_lider": CANAIS.get(r["canal_lider"], r["canal_lider"]),
        "conc": {
            "n": len(t["concorrentes"]),
            "nomes": ", ".join(sorted(t["concorrentes"]["nome_concorrente"])[:-1])
            + " e " + sorted(t["concorrentes"]["nome_concorrente"])[-1],
            "min": int(por_produto.min()), "max": int(por_produto.max()),
        },
        "q": q,
        "periodo": f"{data_br(r['periodo_inicio'])} a {data_br(r['periodo_fim'])}",
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "brl": brl, "pct": pct, "num": num,
        "insights": _insights(r, t),
        "canais": canais.to_dict("records"),
        "graficos_json": json.dumps(_graficos(r, t), ensure_ascii=False),
        "tabela_clientes": _tabela(
            t["clientes"].head(10),
            {"nome_cliente": "Cliente", "estado": "UF", "pedidos": "Pedidos",
             "receita": "Receita", "ticket_medio": "Ticket médio", "recencia_dias": "Dias desde a última compra"},
            {"pedidos": num, "receita": brl, "ticket_medio": lambda v: brl(v, 2), "recencia_dias": num},
        ),
        "tabela_tenis": _tabela(
            tenis.sort_values("preco_atual", ascending=False).head(6),
            {"nome_produto": "Produto", "preco_atual": "Nosso preço",
             "preco_medio_concorrencia": "Concorrência", "receita": "Receita"},
            {"preco_atual": lambda v: brl(v, 2), "preco_medio_concorrencia": lambda v: brl(v, 2), "receita": brl},
        ),
    }
    html = env.get_template("dashboard.html.j2").render(**ctx)
    destino.write_text(html, encoding="utf-8")


def gerar_relatorio_qualidade(q: dict, destino: Path) -> None:
    ini, fim = q["periodo_vendas"]
    linhas = [
        "# Qualidade dos dados", "",
        "## Linhas carregadas", "",
        *[f"- {k}: {v}" for k, v in q["linhas"].items()], "",
        "## Chaves duplicadas", "",
        *[f"- {k}: {v}" for k, v in q["duplicados"].items()], "",
        "## Joins (registros sem correspondência)", "",
        *[f"- {k}: {v}" for k, v in q["orfaos"].items()], "",
        f"As vendas com produto sem cadastro somam {brl(q['receita_orfa'], 2)}. Elas ficam na base "
        f"(left join) com a categoria \"Sem cadastro\". IDs: {', '.join(q['orfaos_produto_ids'])}.", "",
        "## Limpezas aplicadas", "",
        "- Vendas: 4 colunas vazias no fim de cada linha foram descartadas.",
        "- Decimais com vírgula (`preco_unitario`, `preco_concorrente`) foram convertidos para número.",
        f"- preco_competidores: {q['competidores_corrigidos']} linha(s) com o registro inteiro dentro de "
        "`id_produto` foram corrigidas (mantido o primeiro token).",
        "- clientes: prefixos como `Srta, ` foram normalizados para `Srta. `.", "",
        "## Outras verificações", "",
        f"- Valores nulos: {q['nulos']}",
        f"- Quantidade <= 0: {q['quantidade_invalida']}",
        f"- Preço unitário <= 0: {q['preco_invalido']}",
        f"- Produtos com preço de concorrente: {q['produtos_com_concorrente']}",
        f"- Período das vendas: {ini} a {fim}",
        f"- Coleta de preços da concorrência: {q['periodo_coleta'][0]} a {q['periodo_coleta'][1]} (um único dia)",
        "",
    ]
    destino.write_text("\n".join(linhas), encoding="utf-8")
