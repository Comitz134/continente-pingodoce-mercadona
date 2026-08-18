# Prato da Semana 🍽️

App web (PWA) para gerar uma ementa semanal de receitas com base em:

- **Orçamento** por dose (intervalo de preço);
- **Alergias** (lactose, glúten, ovo, amendoim, frutos secos, peixe, marisco, soja, sésamo);
- **Alimentos a evitar** (texto livre, ex.: "cogumelos");
- **Supermercados** — Continente, Pingo Doce e Mercadona (só aparecem receitas cujos ingredientes encontras nas lojas escolhidas).

Cada dia tem foto, preço estimado, tempo de preparação, alergénios, lojas, dica e lista de compras. Podes **trocar** uma receita individual ou gerar uma **nova ementa**.

Também há um **carrinho de compras** (botão 🛒): adiciona os ingredientes de uma receita (ou um ingrediente individual) e a app mostra o preço de cada item e o **total em cada supermercado** (Continente, Pingo Doce, Mercadona), destacando a loja mais barata 🏆. Tudo fica guardado no telemóvel (localStorage) e a app é **instalável** (Adicionar ao ecrã principal) e funciona **offline** depois do primeiro carregamento.

**Preços reais (opcional)**: com o Supabase configurado (`supabase-config.js`), o carrinho mostra o **produto mais barato por loja** (com link) e o selo "preço real"; sem ele, usa os preços curados. Vê `../DEPLOY.md` para publicar no GitHub Pages com recolha automática de preços.

## Como usar

### Local (computador)
```bash
cd receitas
python -m http.server 8000
```
Abre http://localhost:8000 no navegador.

### No telemóvel
1. Publica a pasta `receitas` num serviço estático gratuito (Netlify, Vercel, GitHub Pages, Cloudflare Pages). Basta arrastar a pasta.
2. Abre o link no telemóvel e escolhe **Adicionar ao ecrã principal** — fica como uma app.

## Dados

- **Receitas e fotos**: curadas manualmente; as imagens vêm do [TheMealDB](https://www.themealdb.com) (fotos reais dos pratos, serviço gratuito e estável).
- **Preços**: estimativa por dose em €, para Portugal (indicativo, não é tempo real).
- **Carrinho**: preços por ingrediente (€/kg, €/L, €/unidade…) em `precos.js` — também uma estimativa curada, para comparação entre lojas.
- **Disponibilidade por loja**: estimativa curada. O Continente, o Pingo Doce e a Mercadona **não disponibilizam APIs públicas de produtos**, por isso a correspondência receita→loja é uma aproximação baseada em ingredientes comuns; produtos especializados (ex.: pecorino, tahini, molho teriyaki) estão marcados apenas nas lojas onde é mais provável encontrá-los.

## Estrutura

```
index.html          UI
styles.css          estilos mobile-first
data.js             receitas, alergénios e lojas
precos.js           preços por ingrediente e por loja (fallback)
supabase-config.js  ligação ao Supabase para preços reais
app.js              filtros + gerador semanal + carrinho + PWA
manifest.webmanifest + sw.js + icons/   instalação e offline
```

## Personalizar

- Adiciona/edita receitas em `data.js` (lista `RECIPES`).
- Alergénios disponíveis em `ALLERGENS`; lojas em `STORES`.
- Para regenerar os ícones: `python icons/gen_icons.py`.
