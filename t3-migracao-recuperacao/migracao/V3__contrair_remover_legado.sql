-- ==============================================================================
-- V3__contrair_remover_legado.sql - Fase de CONTRAÇÃO (Expand and Contract)
-- Disciplina: Persistência de Dados e Bancos Distribuídos - Trabalho 3 (T3)
-- ==============================================================================

-- Pré-condições de segurança operacional:
-- 1. Todas as instâncias da aplicação v1 foram desativadas e apenas v2 está no ar.
-- 2. Backfill atingiu 100% de convergência (zero divergências).

-- 1. Garantir NOT NULL e restrição UNIQUE no novo campo oficial
ALTER TABLE cliente ALTER COLUMN email SET NOT NULL;
ALTER TABLE cliente ADD CONSTRAINT uq_cliente_email UNIQUE (email);

-- 2. Remover o trigger de sincronização transitório
DROP TRIGGER IF EXISTS trg_cliente_sync_email_biu ON cliente;
DROP FUNCTION IF EXISTS trg_sync_cliente_email();

-- 3. Contrair: Remover a coluna legada de forma segura
ALTER TABLE cliente DROP COLUMN IF EXISTS contact_email;

-- Migração de schema concluída com ZERO DOWNTIME e compatibilidade retroativa preservada!
