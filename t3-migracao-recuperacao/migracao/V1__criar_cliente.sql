-- ==============================================================================
-- V1__criar_cliente.sql - Estado Original do Banco (Loja Horizonte)
-- Disciplina: Persistência de Dados e Bancos Distribuídos - Trabalho 3 (T3)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    contact_email VARCHAR(200) NOT NULL UNIQUE,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dados existentes antes da migração de versão da aplicação (v1 ativa)
INSERT INTO cliente (id, nome, contact_email) VALUES
(1, 'Alice Pereira', 'alice@horizonte.com.br'),
(2, 'Bruno Ramos', 'bruno@horizonte.com.br'),
(3, 'Carla Prado', 'carla@horizonte.com.br')
ON CONFLICT (id) DO NOTHING;
