# Retiro Tech — design system

Regras de uso para quem (pessoa ou IA) for construir telas, páginas ou materiais do Retiro Tech.
Os valores estão em `tokens.css` (variáveis CSS) e `tokens.json` (fonte original). **Sempre use as variáveis; nunca escreva cores ou tamanhos soltos.**

## O produto

Retiro Tech é uma imersão presencial de um sábado para profissionais de tecnologia que querem empreender: devs, QA e times técnicos, CLT entre R$ 10 e 30 mil ou freelancers travados em R$ 15 a 25 mil por mês.
Promessa: **em um dia você sai com um plano de ação de 90 dias para iniciar o seu faturamento, ou aumentar e bater o recorde.**
Estilo visual: Minimalism & Swiss. Azul de confiança, muito espaço em branco e um laranja que aparece só onde está a ação.

## Voz

- Direta e de quem viveu: fale do que deu certo **e do que falhou** na abertura e no crescimento de uma empresa.
- Concreta: números, prazos e passos ("90 dias", "semana 1", "primeiro contrato"). Nada de "mude sua vida" ou "fórmula secreta".
- De colega para colega: o público é profissional técnico competente que bateu num teto, não iniciante.
- Evite: urgência artificial, excesso de exclamações, emoji, jargão de coach. Escassez ("vagas limitadas") só com número real de vagas.

## Cores

| Variável | Valor | Uso |
| --- | --- | --- |
| `--background` | #F8FAFC | Fundo da página |
| `--card` | #FFFFFF | Superfícies elevadas: cards, formulário, folha do plano de 90 dias |
| `--foreground` | #1E293B | Texto principal em background, card e muted |
| `--muted-foreground` | #475569 | Texto secundário e legendas; também borda de campos de formulário |
| `--primary` | #2563EB | Marca: botão primário, links, eyebrows, marcadores de semana |
| `--on-primary` | #FFFFFF | Texto e ícones sobre primary e primary-strong |
| `--primary-strong` | #1D4ED8 | Hover do primary, texto de marca sobre muted, faixa do CTA final |
| `--muted` | #E9EFF8 | Fundo de seção alternado, destaque suave |
| `--accent` | #EA580C | CTA de inscrição e marcador da meta (semana 13) |
| `--on-accent` | #000000 | Texto sobre accent |
| `--border` | #E2E8F0 | Divisores e bordas de card (decorativo) |
| `--destructive` | #DC2626 | Somente erros de formulário |
| `--ring` | = primary | Anel de foco do teclado |

Regras:
- Página em `background` com texto `foreground`. `card` eleva superfícies, `muted` alterna o fundo das seções, `border` separa.
- Sobre `muted`, texto de marca usa `primary-strong` (não `primary`).
- `accent` é **sempre preenchimento** com texto `on-accent`. **Nunca** use `accent` como cor de texto (3.4:1, reprova contraste).
- Só existe tema claro por enquanto.

## Tipografia

Outfit para títulos e números grandes; Work Sans para leitura e interface. Ambas vêm do Google Fonts (já importadas em `tokens.css`).

| Classe | Fonte | Tamanho / altura | Peso | Uso |
| --- | --- | --- | --- | --- |
| `.text-display` | Outfit | 48 / 52px, -0.02em | 700 | A promessa. Uma vez por página |
| `.text-heading` | Outfit | 28 / 34px, -0.01em | 600 | Títulos de seção |
| `.text-subheading` | Outfit | 20 / 28px | 600 | Subtítulos, títulos de card e de etapa do plano |
| `.text-body` | Work Sans | 16 / 24px | 400 | Texto corrido |
| `.text-caption` | Work Sans | 13 / 18px | 500 | Legendas, metadados, notas |
| `.text-eyebrow` | Work Sans | 12 / 16px, 0.08em, caixa-alta | 600 | Rótulo acima de títulos ("IMERSÃO PRESENCIAL"), em primary (ou primary-strong sobre muted) |

## Espaço e forma

- `--space-2` (8px): entre rótulo e campo, ícone e texto.
- `--space-4` (16px): padding de botões e tags; gutter entre cards.
- `--space-6` (24px): padding de card; distância entre título e texto.
- `--space-12` (48px): respiro entre seções.
- Prefira uma coluna folgada a um grid apertado.
- `--radius-sm` (4px) em tags, campos e marcadores pequenos; `--radius-md` (12px) em cards e botões; `--radius-pill` em chips de data e no CTA de inscrição.
- **Sem sombras.** Separe com `border` ou com a troca `background` → `card` / `muted`.

## Movimento

- Transições de hover entre 150 e 300 ms (`--duration-fast`, `--duration-base`).
- Animação só quando explica algo (ex.: marcadores de semana preenchendo).
- Com `prefers-reduced-motion`, tudo aparece no estado final (já tratado em `tokens.css`).

## Motivo gráfico

O plano de 90 dias tem cerca de 13 semanas. Uma sequência de **13 marcadores** em `primary`, com o último em `accent`, é o elemento recorrente: progresso, linha do tempo, agenda do dia.

## Logo e ícones

- Ainda não há logo. Escreva "Retiro Tech" em Outfit 700, em `primary` ou `foreground`.
- Ícones: SVG de traço (Lucide ou Heroicons). Nunca emoji.

## Acessibilidade

- Todo par de texto listado acima passa 4.5:1. `accent` nunca vira texto.
- Campos de formulário usam borda `muted-foreground` (porque `border` é só decorativo). Foco com anel `ring`.
- Cada campo inválido recebe mensagem própria em `destructive`, logo abaixo, ligada por `aria-describedby`.

## Exemplos rápidos

```html
<section style="background: var(--muted); padding: var(--space-12) var(--space-6);">
  <p class="text-eyebrow" style="color: var(--primary-strong);">Plano de 90 dias</p>
  <h2 class="text-heading">O que deu certo. O que falhou.</h2>
  <p class="text-body" style="color: var(--muted-foreground);">Um sábado inteiro, presencial, com quem já abriu empresa e errou antes de você.</p>
</section>

<a href="#inscricao" style="
  background: var(--accent); color: var(--on-accent);
  border-radius: var(--radius-pill); padding: var(--space-4) var(--space-6);
  font-family: var(--font-sans); font-weight: 600; text-decoration: none;
  transition: filter var(--duration-fast);">Quero minha vaga</a>
```
