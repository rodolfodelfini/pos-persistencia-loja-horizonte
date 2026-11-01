-- ==============================================================================
-- Carga Inicial (Seed) - Loja Horizonte
-- Disciplina: Persistência de Dados e Bancos Distribuídos
-- Trabalho 1 (T1)
-- ==============================================================================

-- 1. Inserir Clientes para Testes de Concorrência e Sessão
INSERT INTO cliente (id, nome, contact_email) VALUES
(42, 'Ana Silva', 'ana.silva@horizonte.com.br'),
(18, 'Carlos Mendes', 'carlos.mendes@horizonte.com.br'),
(99, 'Mariana Souza', 'mariana.souza@horizonte.com.br')
ON CONFLICT (id) DO NOTHING;

-- 2. Inserir Estoque Inicial com Cenários de Borda
INSERT INTO estoque (produto_id, nome, disponivel, reservado) VALUES
(10, 'Mochila de Trilha 25L', 3, 0),
(11, 'Bota Impermeável para Caminhada', 5, 0),
(12, 'Bastão de Caminhada Retrátil', 0, 0), -- Sem estoque (teste de borda)
(13, 'Fogareiro Portátil para Camping', 10, 0)
ON CONFLICT (produto_id) DO NOTHING;

-- 3. Inserir Pedidos para Teste de Ciclo de Vida
INSERT INTO pedido (id, cliente_id, estado, valor_total) VALUES
(701, 42, 'CRIADO', 289.90),
(702, 18, 'PAGO', 149.00)
ON CONFLICT (id) DO NOTHING;

-- 4. Inserir Vetores de Busca Semântica (pgvector)
-- Representação dimensional normalizada de temas: [Trilha/Caminhada, Aventura/Camping, Urbano/Escolar]
INSERT INTO produto_embedding (produto_id, nome, categoria, embedding) VALUES
(10, 'Mochila de Trilha 25L', 'Equipamento Aventura', '[0.90, 0.10, 0.05]'),
(11, 'Bota Impermeável para Caminhada', 'Calçados', '[0.95, 0.05, 0.00]'),
(12, 'Bastão de Caminhada Retrátil', 'Acessórios Trekking', '[0.88, 0.12, 0.00]'),
(13, 'Fogareiro Portátil para Camping', 'Cozinha Outdoor', '[0.10, 0.90, 0.00]'),
(14, 'Caderno Universitário 200 Fls', 'Papelaria', '[0.00, 0.05, 0.95]')
ON CONFLICT (produto_id) DO NOTHING;
