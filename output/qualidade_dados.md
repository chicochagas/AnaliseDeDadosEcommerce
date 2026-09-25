# Qualidade dos dados

## Linhas carregadas

- vendas: 3020
- clientes: 50
- produtos: 215
- competidores: 728

## Chaves duplicadas

- vendas.id_venda: 0
- clientes.id_cliente: 0
- produtos.id_produto: 0

## Joins (registros sem correspondência)

- vendas→clientes: 0
- vendas→produtos: 20
- competidores→produtos: 0

As vendas com produto sem cadastro somam R$ 4.240,01. Elas ficam na base (left join) com a categoria "Sem cadastro". IDs: prd_007af8c5fb0e, prd_0454b1b9fe21, prd_235a85c800bf, prd_2b1b2e2c60e1, prd_3d2453a6e728, prd_59109bac228a, prd_65574e733561, prd_74b8e2ff8f97, prd_7edb1c123c6a, prd_7f61cfa619e3, prd_84adbd000991, prd_8924837a2a70, prd_8dcaa6bdfbb9, prd_91cfa7eada76, prd_931ff6d38056, prd_b161f952f659, prd_b3d5d6aac3ff, prd_c366b8673062, prd_cb9e965f2314, prd_ef1a185da3aa.

## Limpezas aplicadas

- Vendas: 4 colunas vazias no fim de cada linha foram descartadas.
- Decimais com vírgula (`preco_unitario`, `preco_concorrente`) foram convertidos para número.
- preco_competidores: 1 linha(s) com o registro inteiro dentro de `id_produto` foram corrigidas (mantido o primeiro token).
- clientes: prefixos como `Srta, ` foram normalizados para `Srta. `.

## Outras verificações

- Valores nulos: {'vendas': 0, 'clientes': 0, 'produtos': 0, 'competidores': 0}
- Quantidade <= 0: 0
- Preço unitário <= 0: 0
- Produtos com preço de concorrente: 215
- Período das vendas: 2025-12-13 00:26:19 a 2026-01-11 23:58:54
- Coleta de preços da concorrência: 2026-01-11 00:05:16 a 2026-01-11 23:58:02 (um único dia)
