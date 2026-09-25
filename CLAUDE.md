# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project goal

Data-analysis project (Portuguese-language) over e-commerce CSVs in `data/`. The spec lives in [data/.llm/prd.md](data/.llm/prd.md):

1. Analyze all tables together, verify the joins between them, and define the KPIs.
2. Generate **smaller files with pre-computed KPIs** so later analysis fits in LLM context (don't re-load the raw CSVs every time).
3. Produce a final **HTML dashboard/presentation** using the company's default design system **"Retiro Tech"**.

## Commands

```bash
python gerar_dashboard.py                 # full pipeline: data/ -> output/
cd output && python -m http.server 8000   # preview dashboard.html
```

Requires Python 3.12 with pandas and jinja2. No tests, linter or build step.

## Pipeline

`gerar_dashboard.py` runs, in order:

- `src/carga.py` loads the CSVs, one reader per file because formats differ (see quirks below), and builds `base_analitica` (sales left-joined to products and customers).
- `src/kpis.py` covers `validar()` (join/quality checks) and `calcular()`, which returns `(resumo, tabelas)`.
- `src/render.py` writes the HTML and the quality report. It builds chart data, the auto-generated pt-BR insight sentences and the formatters (`brl`, `pct`, `num`).

Outputs, all generated (don't edit by hand):

- `output/kpis/*.csv`: one per table in `tabelas`.
- `output/kpis/kpis.json`: the `resumo` dict. These are the "smaller files" meant as LLM context instead of the raw data.
- `output/qualidade_dados.md`
- `output/dashboard.html`: `templates/dashboard.html.j2`, with chart data injected as JSON and drawn by Chart.js from the CDN.

Adding a chart touches three places: the data in `_graficos()`, a `<canvas>` plus `<details data-tabela>` in the template, and the JS chart and `tabelas` entry in the template's script. Headlines and insights should be computed from `resumo`/`tabelas`, not hardcoded.

## Known data findings

- All 15 products in **Tênis** have `preco_atual` exactly 2× every competitor price and zero sales, likely a price-registration error. `kpis.calcular` detects categories with a price index ≥ 1.9 (`categorias_preco_dobro`) and reports the price index with and without them, because they skew the mean.
- 20 sales reference product IDs missing from `produtos`. They are kept under category "Sem cadastro".

## Design system

The dashboard follows the "Retiro Tech" design system (artifact https://claude.ai/artifact/5fqbmahyCigQUTbhhXiErZ, `project/tokens.json`). The tokens are copied 1:1 as CSS variables into the template's `:root`, with the same names as `../SiteRetiroTech/assets/css/styles.css`. The theme is light only.

- `accent` (orange) is fill only, never text. In charts, use it for at most one highlighted mark.
- Brand text on `muted` sections uses `primary-strong`.
- No shadows, no emoji.
- Chart series: `primary` is the main series. `--chart-secondary` (#64748B) is used only for the second channel, always with a legend.

## Data model

All IDs are prefixed strings. Join keys:

- `Vendas.id_cliente` → `clientes.id_cliente` (`cus_…`)
- `Vendas.id_produto` → `produtos.id_produto` (`prd_…`)
- `preco_competidores.id_produto` → `produtos.id_produto` (many competitor rows per product: Mercado Livre, Amazon, Shopee…)

| File | Rows | Key columns |
|---|---|---|
| `Dados do ecommerce - Vendas.csv` | ~3020 | `id_venda` (`sal_…`), `data_venda`, `canal_venda` (`ecommerce` / `loja_fisica`), `quantidade`, `preco_unitario` |
| `Dados do ecommerce - clientes.csv` | ~50 | `nome_cliente`, `estado` (UF), `pais`, `data_cadastro` |
| `Dados do ecommerce - produtos.csv` | ~215 | `nome_produto`, `categoria`, `marca`, `preco_atual`, `data_criacao` |
| `Dados do ecommerce - preco_competidores.csv` | ~727 | `nome_concorrente`, `preco_concorrente`, `data_coleta` |

Revenue is not stored: compute it as `quantidade * preco_unitario`.

## Data-format quirks (must handle when loading)

The files are inconsistent with each other — don't assume one reader config fits all:

- **Vendas, clientes, produtos**: `;`-separated, UTF-8 **with BOM** (use `encoding="utf-8-sig"`), CRLF line endings.
- **preco_competidores**: `,`-separated, plain ASCII, values quoted.
- **Decimal separators differ**: `Vendas.preco_unitario` and `preco_concorrente` use comma (`64,79`); `produtos.preco_atual` uses dot (`68.90`).
- **Vendas** has 4 trailing empty columns (`;;;;`) — drop them.
- **preco_competidores** row 1 is malformed: the whole record is packed into the `id_produto` field separated by whitespace (`"prd_2293732b7542        Mercado Livre        65,45 …"`). Clean the `id_produto` (take the first token) before joining.
- **clientes** has name noise such as `Srta, Amanda Sousa` (comma inside the name, title prefixes).
- Category names contain accents (`Eletrônicos`, `Áudio`, `Acessórios`) — keep UTF-8 throughout, including in the generated HTML.
