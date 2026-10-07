=# 👖 GALVIRO — Sistema de Vendas

> Rosa · Guimarães · Vieira · Alves — Engenharia de Software 2026

Sistema completo de e-commerce para loja de calças (jeans, social, casual e esportivo), com visual de grife em tema escuro, carrinho, login, checkout, baixa automática de estoque e painel administrativo.

| Camada        | Tecnologia                              |
|---------------|-----------------------------------------|
| Frontend      | HTML + CSS + JS puro (arquivo único)    |
| Backend       | Python + Flask (API REST)               |
| Banco de dados| SQLite (`calcaco.db`)                   |
| Autenticação  | JWT (PyJWT) + bcrypt                    |
| Imagens       | Unsplash (CDN, domínio público)         |

---

## ▶️ Como rodar (passo a passo)

### 1. Instalar as bibliotecas (só na primeira vez)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Iniciar o servidor

```bash
cd backend
python server.py
```

Saída esperada:

```
[OK] Banco de dados: ./calcaco.db
[OK] Banco de dados inicializado: calcaco.db
[OK] GALVIRO API rodando em http://localhost:3000
```

### 3. Abrir o site

- **Opção A (recomendada):** abra `http://localhost:3000` — o Flask serve a loja direto.
- **Opção B:** em outro terminal:

```bash
cd frontend
python -m http.server 8080
```

e abra `http://localhost:8080`.

> O frontend detecta automaticamente a origem: quando servido pela porta 3000 usa a própria API; senão aponta para `http://localhost:3000`.

### 4. Acessar o painel admin

1. Clique em **Entrar** (topo direito).
2. Login: **admin@calcaco.com** — Senha: **password**
3. Clique no botão **Admin** que aparece no menu.

---

## 🛍️ Funcionalidades

### Loja (cliente)
- Catálogo com fotos de modelo, filtros por categoria/gênero, busca e contador de peças
- Modal de produto com **galeria multi-foto** (miniaturas), avaliações com estrelas, estoque por tamanho (tamanhos esgotados desabilitados) e preço com desconto
- Carrinho (sidebar) com quantidade, remoção e subtotal
- Checkout com formulário: endereço, cidade, CEP e forma de pagamento (PIX, cartão, boleto)
- Login/cadastro; pedido **baixa o estoque automaticamente**

### Painel Admin (gestor)
| Aba | O que faz |
|-----|-----------|
| **Dashboard** | Receita total, pedidos, pendentes, ticket médio, mais vendidos, vendas por categoria e vendas mensais em gráfico |
| **Pedidos** | Todos os pedidos com itens, miniaturas, e mudança de status (Pendente → Confirmado → Em preparo → Enviado → Entregue / Cancelado). Filtrável por status |
| **Estoque** | Quantidade por tamanho de cada produto (salva ao clicar fora do campo), com foto do produto |
| **Produtos** | Editar nome/preço/badge/descrição, ativar/desativar e **gerenciar a galeria** (adicionar/remover foto, definir a capa clicando na foto) |
| **Novo Produto** | Cadastro com galeria de exemplos, URLs extras de fotos e estoque inicial por tamanho (`40:10, 42:8`) |

---

## 🗂️ Estrutura

```
galviro/
│
├── backend/
│   ├── server.py          ← API Flask (rotas, JWT, estoque, pedidos, fotos)
│   ├── schema.sql         ← Estrutura + índices + fotos (idempotente, roda em todo startup)
│   ├── requirements.txt   ← Bibliotecas
│   ├── .env               ← Variáveis (PORT, JWT_SECRET) — não suba para o Git
│   └── calcaco.db         ← SQLite (gerado automaticamente)
│
├── frontend/
│   └── index.html         ← Loja + painel admin (arquivo único)
│
├── README.md              ← Este arquivo
├── LOG.md                 ← Registro de alterações do projeto
└── .gitignore
```

---

## 📡 Endpoints da API

| Método | Rota                              | Descrição                      | Auth  |
|--------|-----------------------------------|--------------------------------|-------|
| POST   | `/auth/register`                  | Cadastrar usuário              | -     |
| POST   | `/auth/login`                     | Login (retorna token JWT)      | -     |
| GET    | `/auth/me`                        | Meu perfil                     | Sim   |
| GET    | `/produtos`                       | Listar (filtros: `categoria`, `genero`, `busca`, `ordem`, `pagina`, `limite`) | - |
| GET    | `/produtos/:id`                   | Detalhe (estoque, avaliações, `fotos[]`) | - |
| POST   | `/produtos`                       | Criar produto                  | Admin |
| PUT    | `/produtos/:id`                   | Atualizar produto              | Admin |
| DELETE | `/produtos/:id`                   | Desativar produto              | Admin |
| POST   | `/produtos/:id/fotos`             | Adicionar foto (1ª vira capa)  | Admin |
| DELETE | `/produtos/:id/fotos/:foto_id`    | Remover foto (promove a próxima) | Admin |
| GET    | `/estoque/:id`                    | Estoque por produto            | -     |
| GET    | `/estoque/tudo`                   | Estoque completo (1 request)   | -     |
| PUT    | `/estoque`                        | Atualizar estoque              | Admin |
| GET    | `/pedidos`                        | Listar (admin: `?status=`; admins veem itens embutidos) | Sim |
| GET    | `/pedidos/:id`                    | Detalhe do pedido              | Sim   |
| POST   | `/pedidos`                        | Criar pedido (baixa estoque)   | Sim   |
| PATCH  | `/pedidos/:id/status`             | Atualizar status               | Admin |
| POST   | `/avaliacoes`                     | Avaliar produto                | Sim   |
| GET    | `/relatorios/vendas`              | Métricas (dashboard)           | Admin |
| GET    | `/health`                         | Status da API                  | -     |

---

## 🗄️ Banco de dados

- O `schema.sql` roda em **todo startup** e é idempotente (nada é apagado): cria tabelas/índices que faltam, mantém dados existentes e reaplica as fotos dos 12 produtos de exemplo.
- Índices criados em: produtos (categoria, gênero, ativo, badge, criado), pedidos (usuário, status, criado), itens_pedido (pedido, produto), avaliacoes (produto), produto_fotos (produto).
- `produto_fotos` é a galeria multi-foto. A `imagem_url` do produto é a **capa** (primeira foto).
- **Resetar tudo:** apague `backend/calcaco.db` e reinicie o servidor (recria com seed e fotos).

---

## 🎨 Como modificar

- **Cores/tema:** bloco `:root { }` no topo de `frontend/index.html` (`--gold`, `--black`...).
- **Produtos/Fotos:** painel Admin → aba Produtos → Editar (foto/capa, preço, badge) — sem mexer em código. No cadastro há galeria pronta de exemplos.
- **Texto dos banners:** procure `hero-badge`/`showcase-title` no `index.html`.
- **Nova rota na API:** em `backend/server.py`, adicione com o decorator `@app.route(...)`.

---

## ⚠️ Notas e boas práticas

- Ambiente de **produção**: ligue `FLASK_DEBUG=1` só para desenvolver (default: desligado). Troque `JWT_SECRET` do `.env` por uma string longa.
- `.env` já esteve versionado no repositório — recomendado removê-lo e rodar `pip install python-dotenv` se quiser carregá-lo automaticamente.
- Porta 3000 ocupada? Encerre outro processo ou mude `PORT` no `.env`.
- Fotos antigas ao atualizar: `Ctrl+F5` (cache do navegador).

---

## 🔄 Como parar

`Ctrl+C` no terminal do servidor.

---

*GALVIRO — Rosa · Guimarães · Vieira · Alves · 2026*
