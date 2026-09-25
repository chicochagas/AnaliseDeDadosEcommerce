"""Analisa os CSVs de data/, salva os KPIs em output/kpis/ e gera output/dashboard.html.

Uso: python gerar_dashboard.py
"""
import json
import sys
from pathlib import Path

from src import carga, kpis, render

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / "data"
SAIDA = RAIZ / "output"


def main() -> None:
    dados = carga.carregar(DADOS)
    base = carga.base_analitica(dados)
    qualidade = kpis.validar(dados)
    resumo, tabelas = kpis.calcular(dados, base)

    pasta_kpis = SAIDA / "kpis"
    pasta_kpis.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        df.round(2).to_csv(pasta_kpis / f"{nome}.csv", index=False, encoding="utf-8")
    (pasta_kpis / "kpis.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    render.gerar_relatorio_qualidade(qualidade, SAIDA / "qualidade_dados.md")
    render.gerar_html(resumo, tabelas, qualidade, RAIZ / "templates", SAIDA / "dashboard.html")

    print(f"Receita total: {render.brl(resumo['receita_total'], 2)} | pedidos: {resumo['pedidos']} "
          f"| período: {resumo['periodo_inicio']} a {resumo['periodo_fim']}")
    print(f"Órfãos: {qualidade['orfaos']}")
    print(f"{len(tabelas)} tabelas de KPI em {pasta_kpis.relative_to(RAIZ)}")
    print(f"Dashboard: {(SAIDA / 'dashboard.html').relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
