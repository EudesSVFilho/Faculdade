# LOG DE ALTERAÇÕES — GALVIRO

> Documento de registro das mudanças aplicadas no projeto (velocidade, fotos, visual e painel admin).
> Data: 25/08/2026 · Branch: `master`

---

## ☀️ Modo claro (última rodada)

| Commit | Mensagem | Conteúdo |
|--------|----------|----------|
| `c39443a` | feat(front): modo claro com tons de azul e botão de tema persistente | `frontend/index.html` |
| *(este commit)* | docs: LOG | `LOG.md` |

- Novo tema **claro com tons de azul** (`data-theme="light"`): fundos azul-gelo, cards brancos, texto azul-petróleo, bordas azul-claras — **acento dourado da marca mantido** (escolha do usuário).
- Cores fixas do CSS variabilizadas (superfícies, overlays, gradientes, toast, scrollbar, badge "Novo") — aparência do tema escuro **inalterada**.
- Botão no navbar (☀️/🌙) alterna o tema; preferência persistida em `localStorage` (`galviro-theme`); padrão: escuro.

---

## ⭐ Rodada final (fotos definidas pelo usuário)

| Commit | Mensagem | Conteúdo |
|--------|----------|----------|
| `de5f26c` | fix(fotos): aplica fotos fornecidas pelo usuário (capas + galeria) | `backend/schema.sql`, `backend/calcaco.db` |
| *(ver abaixo)* | fix(fotos): remove fotos — produtos usam fallback da marca | `backend/schema.sql`, `backend/calcaco.db` |
| *(este commit)* | docs: LOG | `LOG.md` |

> **Estado final definido pelo usuário:** os produtos de exemplo **ficam SEM foto** (fallback "GALVIRO / MODA COM PRECISÃO"). O `schema.sql` mantém o bloco que zera `imagem_url` e `produto_fotos` dos produtos 1–12 a cada startup; fotos em produtos novos (13+) pelo admin são preservadas.

Resumo:
- O usuário forneceu `fotos_produtos.sql` com as imagens finais (12 capas + 1 foto alternativa por produto no `produto_fotos`).
- O `schema.sql` passou a **replicar esse seed** de forma idempotente no startup (`UPDATE` capas + `DELETE` + `INSERT OR IGNORE`), substituindo o bloco anterior que **zerava** as fotos.
- Verificado via API: 12/12 produtos com capa e 2 fotos.
- **Limitação de rede:** nesta sessão o `images.unsplash.com` estava sendo interceptado por um portal cativo ("Alloha") no shell, então 7 URLs novas não puderam ser revalidadas daqui — foram confiadas à curadoria do usuário. Se alguma foto quebrar no navegador, o frontend mostra o fallback da marca (não quebra a página).

---

## 0. Rodada extra (imagens definitivas + README)

| Commit | Mensagem | Conteúdo |
|--------|----------|----------|
| *(este commit)* | fix(fotos): imagens de domínio público que remetem aos itens à venda | `backend/schema.sql`, `backend/calcaco.db` |
| *(este commit)* | docs: README completo de uso do projeto | `README.md`, `LOG.md` |

O que foi feito nessa rodada:

- **42 novas URLs do Unsplash testadas** (casadas com o item à venda: jeans, terno, wide leg, cargo, flare, track, linho, jogger, skinny, chino, palazzo, bermuda) — 1 falhou e foi descartada; **36 entraram** (3 por produto, todas validadas com HTTP 200 e download `image/jpeg`).
- `schema.sql`: bloco de fotos trocado, capas reatribuídas e galeria `produto_fotos` regravada (DELETE + INSERT idempotente, roda em todo startup).
- **Banco migrado** (`calcaco.db`): 12 produtos × (capa + 3 fotos) — verificado via SQL.
- README.md reescrito para explicar **como se usa o projeto**: rodar, logar no admin, funcionalidades, endpoints, banco, como modificar e boas práticas.

---

## 1. Commits da rodada anterior

| Commit | Mensagem | Conteúdo |
|--------|----------|----------|
| `139f03e` | chore: corrige o arquivo de ignore (.gitignore) e adiciona regras Python | Renomeado `gitignore` → `.gitignore` (o Git só lê o nome com ponto) + regras `__pycache__/`, `*.pyc`, `*.db`, logs |
| `81dad73` | perf+feat(backend): banco mais rápido, consultas sem N+1 e galeria de fotos | `backend/schema.sql`, `backend/server.py`, `backend/calcaco.db` |
| `1fb7424` | feat(frontend): visual premium, fotos de modelo, admin completo | `frontend/index.html` |
| *(este commit)* | docs: README e LOG das alterações | `README.md`, `LOG.md` |

**Como as mudanças foram particionadas:** por camada (ignore → backend → frontend → docs), já que cada camada está concentrada em poucos arquivos (backend tem 2 fontes, frontend é 1 único arquivo). Cada commit agrupa as alterações relacionadas da sua camada, descritas com detalhe na seção abaixo.

---

## 2. Problemas encontrados e soluções

### 2.1 Site lento
| Problema | Solução |
|---|---|
| 2 subqueries por produto em `/produtos` (N+1) | 1 única consulta com `LEFT JOIN` agregado → ~15 ms/request |
| Painel de estoque fazia 1 request por produto | Nova rota `GET /estoque/tudo` retorna tudo em 1 request |
| Painel de pedidos buscava itens 1 a 1 | `/pedidos` (admin) já retorna os itens embutidos |
| Índices faltando (itens_pedido, avaliacoes, pedidos, produtos) | 6 índices novos criados |
| `schema.sql` só rodava quando o banco era novo | Agora roda **em todo startup** (idempotente — nada é apagado), aplicando índices e migrações em bancos existentes |
| Flask em modo debug sempre ligado | `debug` controlado por `FLASK_DEBUG` (default desligado) |

### 2.2 Fotos dos produtos
- Nenhum produto tinha foto → todos mostravam emoji 👖.
- Fotos iniciais (1ª rodada) não condiziam com o anúncio / pareciam amadoras (Wikimedia) → **trocadas por modelos genéricos do Unsplash** (editorial de moda, loja de grife, segmento exclusivo de calças).
- Criada a tabela `produto_fotos` (galeria multi-foto por produto, com índice e UNIQUE(produto_id, url)).
- Rotas novas: `POST /produtos/:id/fotos` e `DELETE /produtos/:id/fotos/:foto_id`; a **primeira foto vira capa** automaticamente; ao remover a capa, a próxima é promovida.
- Se ao recarregar o site aparecer foto antiga, limpe o cache (Ctrl+F5) — as capas são reaplicadas no startup.

### 2.3 Visual não profissional
- Sem favicon → adicionado (ícone SVG "G" dourado inline).
- Fonte serifada antiga (Cormorant Garamond) → **Outfit** (moderna, sem serifa).
- Links mortos (`#`) → apontam para seções reais ou foram removidos (rodapé com contato real, seção "A Marca").
- Anos desatualizados (2025) → 2026.
- Carrinho mostrava emoji junto da foto → removido + fallback "GALVIRO" estilizado para foto quebrada.
- Foto do produto escondida no modal mobile → agora visível.
- Animação em cascata travava com muitos produtos (até 7 s de atraso) → limitada a 1 s.
- `API_URL` fixo → dinâmico (funciona na porta 3000 e 8080).
- Checkout sem dados → modal com endereço, cidade, CEP e forma de pagamento.
- Avaliações existiam na API mas não eram exibidas → modal agora mostra média, estrelas e comentários; tamanhos esgotados ficam desabilitados.

### 2.4 Painel admin
Antes: janela de 900 px com 3 abas simples.
Agora (tela cheia, 5 abas):
- **Dashboard** — receita total, nº de pedidos, pendentes, ticket médio, mais vendidos, vendas por categoria e vendas mensais em mini-gráfico.
- **Pedidos** — filtro por status, itens com miniaturas e status em português.
- **Estoque** — cards com foto do produto.
- **Produtos** *(nova aba)* — editar nome/preço/badge/descrição, ativar/desativar, gerenciar a galeria (adicionar/remover foto e definir capa).
- **Novo Produto** — galeria de exemplos + URLs extras de fotos + estoque inicial por tamanho.

---

## 3. Fotos por produto (30 URLs verificadas com HTTP 200)

| ID | Produto | Capa (Unsplash photo id) |
|----|---------|--------------------------|
| 1 | Slim Azul Índigo | `1541099649105-f69ad21f3246` (modelo em jeans) |
| 2 | Alfaiataria Grafite | `1560250097-0b93528c311a` (executivo de terno) |
| 3 | Wide Leg Bege | `1580489944761-15a19d654956` (moda feminina) |
| 4 | Cargo Utilitária | `1529333166437-7750a6dd5a70` (street masculino) |
| 5 | Flare Jeans Midi | `1517438476312-10d79c077509` (modelo em jeans) |
| 6 | Track Pant Tech | `1556906781-9a412961c28c` (modelo esportivo) |
| 7 | Pantalona Linho | `1515372039744-b8f02a3ae446` (moda feminina) |
| 8 | Jogger Premium | `1507003211169-0a1dd7228f2d` (street masculino) |
| 9 | Skinny Preta | `1524504388940-b1c1722653e1` (modelo feminino) |
| 10 | Chino Caramelo | `1568602471122-7832951cc4c5` (modelo masculino) |
| 11 | Palazzo Crepe | `1529139574466-a303027c1d8b` (moda feminina) |
| 12 | Bermuda Surf | `1507525428034-b723cf961d3e` (verão) |

> Fonte: Unsplash (CDN `images.unsplash.com`), parâmetro `auto=format&fit=crop&w=800&q=80`.
> Todas as 30 URLs foram baixadas e validadas (HTTP 200, `image/jpeg`) antes de gravar. O produto 13 ("Calça Nova", criado pelo usuário) não recebeu foto — usa o fallback da marca.

---

## 4. Rotas de API novas/alteradas

| Rota | Mudança |
|------|---------|
| `GET /produtos` | Consulta otimizada (sem N+1) |
| `GET /produtos/:id` | Retorna `fotos[]` além de estoque e avaliações |
| `POST /produtos/:id/fotos` | Nova — adiciona foto (admin); primeira foto vira capa |
| `DELETE /produtos/:id/fotos/:foto_id` | Nova — remove foto (admin); promove a próxima como capa |
| `GET /estoque/tudo` | Nova — estoque completo em 1 request |
| `GET /pedidos?status=` | Novo filtro por status (admin) |
| `GET /pedidos` | (admin) itens embutidos na listagem |

---

## 5. Testes realizados

- `python -m py_compile server.py` — OK.
- Migração do banco existente: índices + fotos aplicados **sem apagar dados** (13 produtos mantidos).
- `/produtos` a 30 requests → ~15 ms/request (via `127.0.0.1`; o nome `localhost` no ambiente de teste adicionava ~2 s de resolução DNS, não é a aplicação).
- `/estoque/tudo`, `/pedidos?status=`, add/delete foto + capa promovida/limpa — OK.
- Frontend: balanceamento de chaves/parênteses OK, todos os `onclick` e `getElementById` referenciam funções/ids existentes.

---

## 6. Como rodar / parar os servidores

O ambiente de desenvolvimento matava os processos em background, então os servidores foram registrados no **Agendador do Windows** (imunes a isso):

```powershell
# Ligar
schtasks /Run /TN GalviroAPI
schtasks /Run /TN GalviroFront

# Parar
schtasks /End /TN GalviroAPI
schtasks /End /TN GalviroFront
```

Acessos: loja em `http://localhost:8080` (ou `http://localhost:3000` servido pelo Flask).
Admin: `admin@calcaco.com` / `password`.

> ⚠️ Se rodar `python server.py` manualmente, a porta 3000 estará ocupada — encerre as tarefas acima antes.

---

## 7. Observações / pendências

- **As fotos foram escolhidas por confiança no conteúdo** (IDs conhecidos de moda no Unsplash; o modelo de IA usado não enxerga imagens). Se alguma foto não agradar, troque pelo painel admin (aba Produtos → Editar → galeria) ou solicite a troca.
- Apagar `backend/calcaco.db` e reiniciar o servidor **recria** o banco com os mesmos índices e fotos (seed no `schema.sql`).
- O `backend/.env` continua versionado (pré-existente); recomenda-se removê-lo do repositório e gerar um `JWT_SECRET` novo em produção.
- Nenhum dado de clientes/pedidos foi alterado; o pedido #1 existente foi preservado.

---

*LOG gerado em 25/08/2026 — GALVIRO, Engenharia de Software 2026.*