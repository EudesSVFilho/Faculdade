-- =============================================================
--  CALÇA & CO. — Schema SQLite
--  Executado automaticamente pelo server.js na primeira inicialização
--  Use IF NOT EXISTS em tudo para ser idempotente
-- =============================================================

-- =============================================================
-- TABELA: usuarios
-- =============================================================
CREATE TABLE IF NOT EXISTS usuarios (
  id            INTEGER   PRIMARY KEY AUTOINCREMENT,
  nome          TEXT      NOT NULL,
  email         TEXT      NOT NULL UNIQUE,
  senha_hash    TEXT      NOT NULL,
  telefone      TEXT,
  role          TEXT      NOT NULL DEFAULT 'cliente' CHECK(role IN ('cliente','admin')),
  ativo         INTEGER   NOT NULL DEFAULT 1,
  criado_em     TEXT      NOT NULL DEFAULT (datetime('now','localtime'))
);

-- =============================================================
-- TABELA: enderecos
-- =============================================================
CREATE TABLE IF NOT EXISTS enderecos (
  id            INTEGER   PRIMARY KEY AUTOINCREMENT,
  usuario_id    INTEGER   NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  apelido       TEXT      DEFAULT 'Principal',
  cep           TEXT      NOT NULL,
  logradouro    TEXT      NOT NULL,
  numero        TEXT      NOT NULL,
  complemento   TEXT,
  bairro        TEXT      NOT NULL,
  cidade        TEXT      NOT NULL,
  estado        TEXT      NOT NULL,
  principal     INTEGER   NOT NULL DEFAULT 0
);

-- =============================================================
-- TABELA: produtos
-- =============================================================
CREATE TABLE IF NOT EXISTS produtos (
  id             INTEGER  PRIMARY KEY AUTOINCREMENT,
  nome           TEXT     NOT NULL,
  descricao      TEXT,
  preco          REAL     NOT NULL,
  preco_original REAL,
  categoria      TEXT     NOT NULL,
  genero         TEXT     NOT NULL DEFAULT 'unissex' CHECK(genero IN ('masculino','feminino','unissex')),
  badge          TEXT     CHECK(badge IN ('new','sale',NULL)),
  imagem_url     TEXT,
  ativo          INTEGER  NOT NULL DEFAULT 1,
  criado_em      TEXT     NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_prod_categoria ON produtos(categoria);
CREATE INDEX IF NOT EXISTS idx_prod_genero    ON produtos(genero);
CREATE INDEX IF NOT EXISTS idx_prod_ativo     ON produtos(ativo);
CREATE INDEX IF NOT EXISTS idx_prod_badge     ON produtos(badge);
CREATE INDEX IF NOT EXISTS idx_prod_criado    ON produtos(criado_em DESC);

-- =============================================================
-- TABELA: estoque
-- =============================================================
CREATE TABLE IF NOT EXISTS estoque (
  id          INTEGER  PRIMARY KEY AUTOINCREMENT,
  produto_id  INTEGER  NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
  tamanho     TEXT     NOT NULL,
  quantidade  INTEGER  NOT NULL DEFAULT 0,
  UNIQUE(produto_id, tamanho)
);

-- =============================================================
-- TABELA: pedidos
-- =============================================================
CREATE TABLE IF NOT EXISTS pedidos (
  id                INTEGER  PRIMARY KEY AUTOINCREMENT,
  usuario_id        INTEGER  NOT NULL REFERENCES usuarios(id),
  total             REAL     NOT NULL,
  status            TEXT     NOT NULL DEFAULT 'pendente'
                             CHECK(status IN ('pendente','confirmado','em_preparo','enviado','entregue','cancelado')),
  forma_pagamento   TEXT     NOT NULL DEFAULT 'pix'
                             CHECK(forma_pagamento IN ('pix','cartao_credito','cartao_debito','boleto')),
  codigo_rastreio   TEXT,
  endereco_entrega  TEXT     NOT NULL,
  observacoes       TEXT,
  criado_em         TEXT     NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_ped_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ped_status  ON pedidos(status);
CREATE INDEX IF NOT EXISTS idx_ped_criado  ON pedidos(criado_em DESC);

-- =============================================================
-- TABELA: itens_pedido
-- =============================================================
CREATE TABLE IF NOT EXISTS itens_pedido (
  id             INTEGER  PRIMARY KEY AUTOINCREMENT,
  pedido_id      INTEGER  NOT NULL REFERENCES pedidos(id)  ON DELETE CASCADE,
  produto_id     INTEGER  NOT NULL REFERENCES produtos(id),
  tamanho        TEXT     NOT NULL,
  quantidade     INTEGER  NOT NULL DEFAULT 1,
  preco_unitario REAL     NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ip_pedido  ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_ip_produto ON itens_pedido(produto_id);

-- =============================================================
-- TABELA: avaliacoes
-- =============================================================
CREATE TABLE IF NOT EXISTS avaliacoes (
  id          INTEGER  PRIMARY KEY AUTOINCREMENT,
  produto_id  INTEGER  NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
  usuario_id  INTEGER  NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  nota        INTEGER  NOT NULL CHECK(nota BETWEEN 1 AND 5),
  comentario  TEXT,
  criado_em   TEXT     NOT NULL DEFAULT (datetime('now','localtime')),
  UNIQUE(produto_id, usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_aval_produto ON avaliacoes(produto_id);

-- =============================================================
-- TABELA: cupons
-- =============================================================
CREATE TABLE IF NOT EXISTS cupons (
  id          INTEGER  PRIMARY KEY AUTOINCREMENT,
  codigo      TEXT     NOT NULL UNIQUE,
  tipo        TEXT     NOT NULL DEFAULT 'percentual' CHECK(tipo IN ('percentual','fixo')),
  valor       REAL     NOT NULL,
  uso_maximo  INTEGER  NOT NULL DEFAULT 1,
  uso_atual   INTEGER  NOT NULL DEFAULT 0,
  valido_ate  TEXT,
  ativo       INTEGER  NOT NULL DEFAULT 1
);

-- =============================================================
-- TABELA: produto_fotos (galeria multi-foto por produto)
-- =============================================================
CREATE TABLE IF NOT EXISTS produto_fotos (
  id          INTEGER  PRIMARY KEY AUTOINCREMENT,
  produto_id  INTEGER  NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
  url         TEXT     NOT NULL,
  ordem       INTEGER  NOT NULL DEFAULT 0,
  UNIQUE(produto_id, url)
);

CREATE INDEX IF NOT EXISTS idx_pf_produto ON produto_fotos(produto_id);

-- =============================================================
-- DADOS INICIAIS (só insere se tabela estiver vazia)
-- =============================================================

INSERT OR IGNORE INTO usuarios (id, nome, email, senha_hash, role) VALUES
(1, 'Administrador', 'admin@calcaco.com',
 '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'admin');
-- Senha do admin: password

INSERT OR IGNORE INTO produtos (id, nome, descricao, preco, preco_original, categoria, genero, badge) VALUES
(1,  'Slim Azul Índigo',    'Corte slim moderno com denim premium de 14oz. Lavagem índigo atemporal.',            189.90, NULL,   'jeans',     'masculino', 'new'),
(2,  'Alfaiataria Grafite', 'Calça social de alfaiataria com caimento impecável para ambientes corporativos.',    289.90, 349.90, 'social',    'masculino', 'sale'),
(3,  'Wide Leg Bege',       'Silhueta wide leg com tecido de viscose fluido para o dia a dia urbano.',            219.90, NULL,   'casual',    'feminino',  NULL),
(4,  'Cargo Utilitária',    'Design utilitário com múltiplos bolsos funcionais em ripstop resistente.',           239.90, NULL,   'casual',    'masculino', 'new'),
(5,  'Flare Jeans Midi',    'Calça flare cintura alta em denim elastano para liberdade de movimento.',            199.90, 239.90, 'jeans',     'feminino',  'sale'),
(6,  'Track Pant Tech',     'Calça esportiva dry-fit perfeita para treinos e lifestyle ativo.',                   159.90, NULL,   'esportivo', 'masculino', NULL),
(7,  'Pantalona Linho',     'Linho puro com caimento fluido e sofisticado para os dias quentes.',                 259.90, NULL,   'social',    'feminino',  'new'),
(8,  'Jogger Premium',      'Moletom penteado com elástico ajustável. Conforto e estilo.',                        179.90, NULL,   'esportivo', 'masculino', NULL),
(9,  'Skinny Preta',        'Skinny jeans preta com elastano de alta performance que valoriza a silhueta.',       189.90, NULL,   'jeans',     'feminino',  NULL),
(10, 'Chino Caramelo',      'Chino clássico em sarja premium, versátil para casual e semi-formal.',               209.90, NULL,   'casual',    'masculino', 'new'),
(11, 'Palazzo Crepe',       'Palazzo de crepe com amarração na cintura para ocasiões especiais.',                 299.90, 359.90, 'social',    'feminino',  'sale'),
(12, 'Bermuda Surf',        'Quick-dry com proteção UV 50+, ideal para esportes aquáticos e praia.',              129.90, NULL,   'esportivo', 'masculino', NULL);

INSERT OR IGNORE INTO estoque (produto_id, tamanho, quantidade) VALUES
(1,'38',15),(1,'40',20),(1,'42',18),(1,'44',12),(1,'46',8),
(2,'38',10),(2,'40',14),(2,'42',16),(2,'44',9),
(3,'34',12),(3,'36',18),(3,'38',20),(3,'40',15),(3,'42',8),
(4,'38',20),(4,'40',25),(4,'42',22),(4,'44',18),(4,'46',10),(4,'48',5),
(5,'34',14),(5,'36',20),(5,'38',16),(5,'40',11),
(6,'P',20),(6,'M',30),(6,'G',28),(6,'GG',15),(6,'XGG',8),
(7,'34',10),(7,'36',15),(7,'38',18),(7,'40',12),(7,'42',9),(7,'44',5),
(8,'P',18),(8,'M',25),(8,'G',22),(8,'GG',12),
(9,'34',16),(9,'36',22),(9,'38',20),(9,'40',14),(9,'42',9),
(10,'38',18),(10,'40',24),(10,'42',20),(10,'44',16),(10,'46',10),
(11,'34',8),(11,'36',12),(11,'38',15),(11,'40',10),(11,'42',6),
(12,'38',22),(12,'40',28),(12,'42',24),(12,'44',18),(12,'46',12);

INSERT OR IGNORE INTO cupons (codigo, tipo, valor, uso_maximo, valido_ate) VALUES
('BEMVINDO10', 'percentual', 10.00, 100, datetime('now', '+1 year')),
('FRETE20',    'fixo',       20.00, 50,  datetime('now', '+6 months'));

-- =============================================================
-- FOTOS DOS PRODUTOS
-- Produtos de exemplo (1-12) ficam SEM foto de terceiros: o frontend
-- usa o fallback premium da marca ("GALVIRO / MODA COM PRECIS?O").
-- Fotos adicionadas pelo painel admin (Produtos -> Editar) em produtos
-- novos (13+) s?o preservadas; as dos produtos 1-12 s?o reaplicadas
-- pelo seed a cada startup.
-- =============================================================

UPDATE produtos SET imagem_url = NULL WHERE id BETWEEN 1 AND 12;
DELETE FROM produto_fotos WHERE produto_id BETWEEN 1 AND 12;
