# =============================================================
#  GALVIRO — Backend API
#  Python + Flask + SQLite (nativo do Python, sem instalar nada!)
#
#  Instalar dependências (só uma vez):
#    pip install flask flask-cors pyjwt bcrypt
#
#  Rodar:
#    python server.py
# =============================================================

import sqlite3
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory   # ← send_from_directory adicionado
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
DB_PATH      = "./calcaco.db"
JWT_SECRET   = os.getenv("JWT_SECRET", "galviro_rosa_guimaraes_vieira_alves_2025")
PORT         = int(os.getenv("PORT", 3000))
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")  # ← aponta para frontend/

# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(sql)
    conn.close()
    print("[OK] Banco de dados inicializado: calcaco.db")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def rows_to_list(rows):
    return [dict(r) for r in rows]

def make_token(user_id, email, role):
    payload = {
        "id":    user_id,
        "email": email,
        "role":  role,
        "exp":   datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

# ─────────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────────
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Token não fornecido."}), 401
        try:
            g.user = decode_token(header.split(" ")[1])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido."}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        if g.user.get("role") != "admin":
            return jsonify({"error": "Acesso negado."}), 403
        return f(*args, **kwargs)
    return decorated

# =============================================================
# ██  FRONTEND — serve o index.html direto em localhost:3000
# =============================================================

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# =============================================================
# ██  AUTENTICAÇÃO
# =============================================================

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    nome  = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")

    if not nome or not email or not senha:
        return jsonify({"error": "Nome, email e senha são obrigatórios."}), 400

    db = get_db()
    if db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone():
        return jsonify({"error": "Email já cadastrado."}), 409

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, telefone) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, data.get("telefone"))
    )
    db.commit()

    token = make_token(cur.lastrowid, email, "cliente")
    return jsonify({"message": "Usuário criado!", "token": token, "userId": cur.lastrowid}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data  = request.get_json() or {}
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"error": "Email e senha obrigatórios."}), 400

    db   = get_db()
    user = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    if not user or not bcrypt.checkpw(senha.encode(), user["senha_hash"].encode()):
        return jsonify({"error": "Credenciais inválidas."}), 401

    token = make_token(user["id"], user["email"], user["role"])
    return jsonify({
        "token": token,
        "user": {"id": user["id"], "nome": user["nome"], "email": user["email"], "role": user["role"]}
    })


@app.route("/auth/me", methods=["GET"])
@auth_required
def me():
    db   = get_db()
    user = db.execute(
        "SELECT id, nome, email, telefone, role, criado_em FROM usuarios WHERE id = ?",
        (g.user["id"],)
    ).fetchone()
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
    return jsonify(dict(user))


# =============================================================
# ██  PRODUTOS
# =============================================================

@app.route("/produtos", methods=["GET"])
def listar_produtos():
    categoria = request.args.get("categoria")
    genero    = request.args.get("genero")
    busca     = request.args.get("busca")
    ordem     = request.args.get("ordem", "novo")
    pagina    = int(request.args.get("pagina", 1))
    limite    = int(request.args.get("limite", 12))
    offset    = (pagina - 1) * limite

    where  = ["p.ativo = 1"]
    params = []

    if categoria:
        where.append("p.categoria = ?"); params.append(categoria)
    if genero:
        where.append("p.genero = ?");    params.append(genero)
    if busca:
        where.append("(p.nome LIKE ? OR p.descricao LIKE ?)")
        params += [f"%{busca}%", f"%{busca}%"]

    ordenar = {
        "preco_asc":  "p.preco ASC",
        "preco_desc": "p.preco DESC",
        "novo":       "p.criado_em DESC",
        "nome":       "p.nome ASC",
    }.get(ordem, "p.criado_em DESC")

    where_str = " AND ".join(where)
    db = get_db()

    # Agregação do estoque em UM agrupamento (LEFT JOIN), em vez de
    # 2 subqueries correlacionadas por produto (problema N+1).
    sql = f"""
        SELECT p.*,
               COALESCE(e.tamanhos, '')        AS tamanhos,
               COALESCE(e.estoque_total, 0)    AS estoque_total
        FROM produtos p
        LEFT JOIN (
            SELECT produto_id,
                   GROUP_CONCAT(tamanho, ',') AS tamanhos,
                   SUM(quantidade)            AS estoque_total
            FROM estoque
            GROUP BY produto_id
        ) e ON e.produto_id = p.id
        WHERE {where_str}
        ORDER BY {ordenar}
        LIMIT ? OFFSET ?
    """
    rows  = db.execute(sql, params + [limite, offset]).fetchall()
    total = db.execute(f"SELECT COUNT(*) AS total FROM produtos p WHERE {where_str}", params).fetchone()["total"]

    dados = []
    for r in rows:
        d = dict(r)
        d["tamanhos"] = d["tamanhos"].split(",") if d["tamanhos"] else []
        dados.append(d)

    return jsonify({
        "dados": dados,
        "paginacao": {"pagina": pagina, "limite": limite, "total": total, "paginas": -(-total // limite)}
    })


@app.route("/produtos/<int:id>", methods=["GET"])
def detalhe_produto(id):
    db      = get_db()
    produto = db.execute("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (id,)).fetchone()
    if not produto:
        return jsonify({"error": "Produto não encontrado."}), 404

    estoque    = rows_to_list(db.execute("SELECT tamanho, quantidade FROM estoque WHERE produto_id = ?", (id,)).fetchall())
    avaliacoes = rows_to_list(db.execute(
        "SELECT a.nota, a.comentario, u.nome, a.criado_em FROM avaliacoes a JOIN usuarios u ON u.id = a.usuario_id WHERE a.produto_id = ?",
        (id,)
    ).fetchall())
    fotos      = rows_to_list(db.execute(
        "SELECT id, url, ordem FROM produto_fotos WHERE produto_id = ? ORDER BY ordem, id",
        (id,)
    ).fetchall())

    return jsonify({**dict(produto), "estoque": estoque, "avaliacoes": avaliacoes, "fotos": fotos})


@app.route("/produtos/<int:id>/fotos", methods=["POST"])
@admin_required
def adicionar_foto(id):
    url = (request.get_json() or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL da foto é obrigatória."}), 400

    db = get_db()
    if not db.execute("SELECT id FROM produtos WHERE id = ?", (id,)).fetchone():
        return jsonify({"error": "Produto não encontrado."}), 404

    db.execute(
        """INSERT OR IGNORE INTO produto_fotos (produto_id, url, ordem)
           VALUES (?, ?, (SELECT COALESCE(MAX(ordem), -1) + 1 FROM produto_fotos WHERE produto_id = ?))""",
        (id, url, id)
    )
    # primeira foto vira capa se o produto ainda não tem nenhuma
    db.execute("UPDATE produtos SET imagem_url = COALESCE(imagem_url, ?) WHERE id = ?", (url, id))
    db.commit()
    return jsonify({"message": "Foto adicionada."}), 201


@app.route("/produtos/<int:id>/fotos/<int:foto_id>", methods=["DELETE"])
@admin_required
def remover_foto(id, foto_id):
    db = get_db()
    removida = db.execute(
        "DELETE FROM produto_fotos WHERE id = ? AND produto_id = ? RETURNING url",
        (foto_id, id)
    ).fetchone()
    if not removida:
        return jsonify({"error": "Foto não encontrada."}), 404
    # se a capa for removida, promove a próxima foto
    db.execute(
        "UPDATE produtos SET imagem_url = (SELECT url FROM produto_fotos WHERE produto_id = ? ORDER BY ordem, id LIMIT 1) WHERE id = ? AND imagem_url = ?",
        (id, id, removida["url"])
    )
    db.commit()
    return jsonify({"message": "Foto removida."})


@app.route("/produtos", methods=["POST"])
@admin_required
def criar_produto():
    data = request.get_json() or {}
    nome      = data.get("nome")
    preco     = data.get("preco")
    categoria = data.get("categoria")

    if not nome or not preco or not categoria:
        return jsonify({"error": "Nome, preço e categoria são obrigatórios."}), 400

    db  = get_db()
    cur = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, preco_original, categoria, genero, badge) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nome, data.get("descricao"), preco, data.get("preco_original"),
         categoria, data.get("genero", "unissex"), data.get("badge"))
    )
    db.commit()
    return jsonify({"message": "Produto criado.", "id": cur.lastrowid}), 201


@app.route("/produtos/<int:id>", methods=["PUT"])
@admin_required
def atualizar_produto(id):
    data   = request.get_json() or {}
    campos = ["nome", "descricao", "preco", "preco_original", "categoria", "genero", "badge", "ativo"]
    sets, params = [], []

    for c in campos:
        if c in data:
            sets.append(f"{c} = ?"); params.append(data[c])

    if not sets:
        return jsonify({"error": "Nenhum campo para atualizar."}), 400

    db = get_db()
    db.execute(f"UPDATE produtos SET {', '.join(sets)} WHERE id = ?", params + [id])
    db.commit()
    return jsonify({"message": "Produto atualizado."})


@app.route("/produtos/<int:id>", methods=["DELETE"])
@admin_required
def deletar_produto(id):
    db = get_db()
    db.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (id,))
    db.commit()
    return jsonify({"message": "Produto desativado."})


# =============================================================
# ██  ESTOQUE
# =============================================================

@app.route("/estoque/<int:produto_id>", methods=["GET"])
def ver_estoque(produto_id):
    rows = get_db().execute(
        "SELECT tamanho, quantidade FROM estoque WHERE produto_id = ? ORDER BY tamanho",
        (produto_id,)
    ).fetchall()
    return jsonify(rows_to_list(rows))


@app.route("/estoque/tudo", methods=["GET"])
def estoque_tudo():
    """Estoque completo de todos os produtos em uma única consulta
    (evita as N requisições do painel de estoque).
    Retorna: { produto_id: [{tamanho, quantidade}, ...], ... }
    """
    rows = get_db().execute(
        "SELECT produto_id, tamanho, quantidade FROM estoque ORDER BY produto_id, tamanho"
    ).fetchall()
    agrupado = {}
    for r in rows:
        agrupado.setdefault(r["produto_id"], []).append(dict(r))
    return jsonify(agrupado)


@app.route("/estoque", methods=["PUT"])
@admin_required
def atualizar_estoque():
    data = request.get_json() or {}
    db   = get_db()
    db.execute(
        """INSERT INTO estoque (produto_id, tamanho, quantidade) VALUES (?, ?, ?)
           ON CONFLICT(produto_id, tamanho) DO UPDATE SET quantidade = excluded.quantidade""",
        (data["produto_id"], data["tamanho"], data["quantidade"])
    )
    db.commit()
    return jsonify({"message": "Estoque atualizado."})


# =============================================================
# ██  PEDIDOS
# =============================================================

@app.route("/pedidos", methods=["GET"])
@auth_required
def listar_pedidos():
    db = get_db()
    if g.user["role"] == "admin":
        status = request.args.get("status")
        sql = ("SELECT p.*, u.nome AS cliente_nome FROM pedidos p "
               "JOIN usuarios u ON u.id = p.usuario_id")
        params = []
        if status:
            sql += " WHERE p.status = ?"
            params.append(status)
        sql += " ORDER BY p.criado_em DESC"
        rows = db.execute(sql, params).fetchall()
        pedidos = rows_to_list(rows)
        # Embutir os itens numa única consulta batched (evita N+1)
        if pedidos:
            ids = [p["id"] for p in pedidos]
            ph  = ",".join("?" * len(ids))
            itens = db.execute(
                f"""SELECT ip.*, pr.nome, pr.imagem_url
                    FROM itens_pedido ip
                    JOIN produtos pr ON pr.id = ip.produto_id
                    WHERE ip.pedido_id IN ({ph})""",
                ids,
            ).fetchall()
            por_pedido = {}
            for it in itens:
                por_pedido.setdefault(it["pedido_id"], []).append(dict(it))
            for p in pedidos:
                p["itens"] = por_pedido.get(p["id"], [])
        return jsonify(pedidos)
    else:
        rows = db.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY criado_em DESC",
            (g.user["id"],)
        ).fetchall()
        return jsonify(rows_to_list(rows))


@app.route("/pedidos/<int:id>", methods=["GET"])
@auth_required
def detalhe_pedido(id):
    db     = get_db()
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (id,)).fetchone()
    if not pedido:
        return jsonify({"error": "Pedido não encontrado."}), 404
    if g.user["role"] != "admin" and pedido["usuario_id"] != g.user["id"]:
        return jsonify({"error": "Acesso negado."}), 403

    itens = rows_to_list(db.execute(
        "SELECT ip.*, pr.nome, pr.imagem_url FROM itens_pedido ip JOIN produtos pr ON pr.id = ip.produto_id WHERE ip.pedido_id = ?",
        (id,)
    ).fetchall())

    return jsonify({**dict(pedido), "itens": itens})


@app.route("/pedidos", methods=["POST"])
@auth_required
def criar_pedido():
    data             = request.get_json() or {}
    itens            = data.get("itens", [])
    endereco_entrega = data.get("endereco_entrega", "")
    forma_pagamento  = data.get("forma_pagamento", "pix")

    if not itens:
        return jsonify({"error": "Carrinho vazio."}), 400

    db = get_db()
    try:
        db.execute("BEGIN")
        total = 0.0

        for item in itens:
            prod = db.execute(
                "SELECT preco FROM produtos WHERE id = ? AND ativo = 1", (item["produto_id"],)
            ).fetchone()
            if not prod:
                raise ValueError(f"Produto ID {item['produto_id']} não encontrado.")

            est = db.execute(
                "SELECT quantidade FROM estoque WHERE produto_id = ? AND tamanho = ?",
                (item["produto_id"], item["tamanho"])
            ).fetchone()
            if not est or est["quantidade"] < item["quantidade"]:
                raise ValueError(f"Estoque insuficiente: produto {item['produto_id']}, tamanho {item['tamanho']}.")

            item["preco_unitario"] = prod["preco"]
            total += prod["preco"] * item["quantidade"]

        cur = db.execute(
            "INSERT INTO pedidos (usuario_id, total, endereco_entrega, forma_pagamento, status) VALUES (?, ?, ?, ?, 'pendente')",
            (g.user["id"], total, endereco_entrega, forma_pagamento)
        )
        pedido_id = cur.lastrowid

        for item in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, tamanho, quantidade, preco_unitario) VALUES (?, ?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["tamanho"], item["quantidade"], item["preco_unitario"])
            )
            db.execute(
                "UPDATE estoque SET quantidade = quantidade - ? WHERE produto_id = ? AND tamanho = ?",
                (item["quantidade"], item["produto_id"], item["tamanho"])
            )

        db.execute("COMMIT")
        return jsonify({"message": "Pedido criado!", "pedidoId": pedido_id, "total": total}), 201

    except ValueError as e:
        db.execute("ROLLBACK")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({"error": "Erro interno: " + str(e)}), 500


@app.route("/pedidos/<int:id>/status", methods=["PATCH"])
@admin_required
def atualizar_status(id):
    status  = (request.get_json() or {}).get("status")
    validos = ["pendente", "confirmado", "em_preparo", "enviado", "entregue", "cancelado"]
    if status not in validos:
        return jsonify({"error": "Status inválido."}), 400

    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, id))
    db.commit()
    return jsonify({"message": "Status atualizado."})


# =============================================================
# ██  AVALIAÇÕES
# =============================================================

@app.route("/avaliacoes", methods=["POST"])
@auth_required
def avaliar():
    data       = request.get_json() or {}
    produto_id = data.get("produto_id")
    nota       = data.get("nota")

    if not produto_id or not nota:
        return jsonify({"error": "produto_id e nota são obrigatórios."}), 400
    if not (1 <= int(nota) <= 5):
        return jsonify({"error": "Nota deve ser entre 1 e 5."}), 400

    db = get_db()
    db.execute(
        """INSERT INTO avaliacoes (produto_id, usuario_id, nota, comentario) VALUES (?, ?, ?, ?)
           ON CONFLICT(produto_id, usuario_id) DO UPDATE SET nota = excluded.nota, comentario = excluded.comentario""",
        (produto_id, g.user["id"], nota, data.get("comentario"))
    )
    db.commit()
    return jsonify({"message": "Avaliação salva!"}), 201


# =============================================================
# ██  RELATÓRIOS (admin)
# =============================================================

@app.route("/relatorios/vendas", methods=["GET"])
@admin_required
def relatorio_vendas():
    db = get_db()

    totais = dict(db.execute("""
        SELECT COUNT(*) AS total_pedidos,
               ROUND(SUM(CASE WHEN status != 'cancelado' THEN total ELSE 0 END), 2) AS receita_total,
               ROUND(AVG(CASE WHEN status != 'cancelado' THEN total ELSE NULL END), 2) AS ticket_medio
        FROM pedidos
    """).fetchone())

    por_categoria = rows_to_list(db.execute("""
        SELECT pr.categoria, COUNT(*) AS qtd,
               ROUND(SUM(ip.preco_unitario * ip.quantidade), 2) AS receita
        FROM itens_pedido ip
        JOIN produtos pr ON pr.id = ip.produto_id
        JOIN pedidos pe ON pe.id = ip.pedido_id AND pe.status != 'cancelado'
        GROUP BY pr.categoria ORDER BY receita DESC
    """).fetchall())

    mais_vendidos = rows_to_list(db.execute("""
        SELECT pr.nome, pr.categoria, SUM(ip.quantidade) AS unidades_vendidas
        FROM itens_pedido ip
        JOIN produtos pr ON pr.id = ip.produto_id
        JOIN pedidos pe ON pe.id = ip.pedido_id AND pe.status != 'cancelado'
        GROUP BY pr.id ORDER BY unidades_vendidas DESC LIMIT 10
    """).fetchall())

    vendas_mensais = rows_to_list(db.execute("""
        SELECT strftime('%Y-%m', criado_em) AS mes,
               COUNT(*) AS total_pedidos,
               ROUND(SUM(total), 2) AS receita
        FROM pedidos WHERE status != 'cancelado'
        GROUP BY mes ORDER BY mes DESC
    """).fetchall())

    return jsonify({"totais": totais, "porCategoria": por_categoria,
                    "maisVendidos": mais_vendidos, "vendasMensais": vendas_mensais})


# =============================================================
# HEALTH CHECK
# =============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": DB_PATH, "timestamp": datetime.now().isoformat()})


# =============================================================
# INICIALIZAÇÃO
# =============================================================

if __name__ == "__main__":
    # Roda SEMPRE (não só na primeira vez): o schema.sql é idempotente
    # (CREATE IF NOT EXISTS + INSERT OR IGNORE) e aplica índices novos
    # e migrações de imagem em bancos existentes sem apagar nada.
    print(f"[OK] Banco de dados: {DB_PATH}")
    init_db()

    print("\n[OK] GALVIRO API rodando em http://localhost:{PORT}")
    print("   Banco: calcaco.db (SQLite nativo do Python)")
    print("   Para parar: Ctrl + C\n")
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )