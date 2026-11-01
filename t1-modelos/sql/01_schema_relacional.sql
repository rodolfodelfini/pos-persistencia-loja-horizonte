-- ==============================================================================
-- DDL - Persistência Relacional & Vetorial (Loja Horizonte)
-- Disciplina: Persistência de Dados e Bancos Distribuídos
-- Trabalho 1 (T1)
-- ==============================================================================

-- 1. Habilitar extensão pgvector para busca semântica por proximidade
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabela de Clientes
CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    contact_email VARCHAR(200) NOT NULL UNIQUE,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Controle de Estoque
-- Invariante crucial: disponivel >= 0
CREATE TABLE IF NOT EXISTS estoque (
    produto_id INT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    disponivel INT NOT NULL DEFAULT 0,
    reservado INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_estoque_disponivel_positivo CHECK (disponivel >= 0),
    CONSTRAINT chk_estoque_reservado_positivo CHECK (reservado >= 0)
);

-- 4. Tabela de Pedidos
CREATE TABLE IF NOT EXISTS pedido (
    id INT PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES cliente(id),
    estado VARCHAR(30) NOT NULL DEFAULT 'CRIADO', -- CRIADO, PAGO, CANCELADO, ENTREGUE
    valor_total NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabela de Reservas Atômicas de Itens
CREATE TABLE IF NOT EXISTS reserva (
    id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL REFERENCES pedido(id),
    produto_id INT NOT NULL REFERENCES estoque(produto_id),
    quantidade INT NOT NULL DEFAULT 1,
    data_reserva TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_reserva_qtd_positiva CHECK (quantidade > 0)
);

-- 6. Tabela de Busca Semântica de Produtos (Vetorial - pgvector)
-- Vetores normalizados para busca por similaridade de cosseno ou euclidiana
CREATE TABLE IF NOT EXISTS produto_embedding (
    produto_id INT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    embedding vector(3) -- Vetor 3D didático (expansível para 768/1536 dimensões)
);

-- Índice vetorial para busca rápida de vizinhos mais próximos (HNSW / IVFFlat)
CREATE INDEX IF NOT EXISTS idx_produto_embedding_l2 
ON produto_embedding USING ivfflat (embedding vector_l2_ops) WITH (lists = 10);
