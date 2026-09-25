# Instruções do projeto (copie este bloco para o CLAUDE.md na raiz do repositório)

## Design system

Este projeto usa o design system do Retiro Tech, na pasta `design-system/`.

- Antes de criar ou alterar qualquer interface, leia `design-system/DESIGN.md` e siga suas regras.
- Importe `design-system/tokens.css` no ponto de entrada e use sempre as variáveis CSS (`var(--primary)`, `var(--space-6)` etc.). Não escreva cores, fontes, espaçamentos ou raios soltos.
- `accent` (laranja) é só para o CTA de inscrição e a meta; nunca como cor de texto.
- Sem sombras, sem emoji, ícones em SVG de traço (Lucide ou Heroicons).
- `design-system/tokens.json` é a fonte original dos valores; se algo mudar lá, atualize `tokens.css` para manter os dois iguais.
