-- ==============================================================================
-- Consultas Canônicas e Transações Atômicas
-- Disciplina: Persistência de Dados e Bancos Distribuídos - Trabalho 1 (T1)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. RESERVA ATÔMICA LOCAL COM GARANTIA DE INVARIANTE (ACID)
-- Invariante: Não vender acima do estoque (disponivel >= 1).
-- O comando UPDATE com RETURNING garante que só reservamos se o decremento ocorreu.
-- ------------------------------------------------------------------------------

BEGIN;
-- Decrementa o estoque disponível de forma atômica
UPDATE estoque 
SET disponivel = disponivel - 1,
    reservado = reservado + 1
WHERE produto_id = 10 AND disponivel >= 1
RETURNING produto_id;

-- Apenas se a linha acima retornou 1 registro a aplicação insere na tabela de reserva
INSERT INTO reserva (pedido_id, produto_id, quantidade)
VALUES (701, 10, 1);

COMMIT;
-- Em caso de falha de conexão, erro ou retorno vazio: ROLLBACK;


-- ------------------------------------------------------------------------------
-- 2. TESTE DE BORDA: TENTATIVA DE RESERVA EM PRODUTO ESGOTADO
-- O produto 12 possui estoque 0. A query abaixo não altera nenhuma linha.
-- ------------------------------------------------------------------------------
BEGIN;
UPDATE estoque 
SET disponivel = disponivel - 1,
    reservado = reservado + 1
WHERE produto_id = 12 AND disponivel >= 1
RETURNING produto_id;
-- RETURNING retorna 0 linhas -> Aplicação aborta e executa ROLLBACK;
ROLLBACK;


-- ------------------------------------------------------------------------------
-- 3. CONSULTA DE BUSCA SEMÂNTICA POR PROXIMIDADE VETORIAL (PGVECTOR)
-- Consulta: "Equipamento para caminhada" mapeado conceitualmente para o vetor [1.0, 0.0, 0.0]
-- Ordenação por menor distância euclidiana (operador <-> do pgvector)
-- ------------------------------------------------------------------------------
SELECT 
    produto_id,
    nome,
    categoria,
    embedding <-> '[1.0, 0.0, 0.0]' AS distancia_euclidiana
FROM produto_embedding
ORDER BY distancia_euclidiana ASC
LIMIT 3;
