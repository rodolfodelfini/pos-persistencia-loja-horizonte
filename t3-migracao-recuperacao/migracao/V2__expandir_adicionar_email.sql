-- ==============================================================================
-- V2__expandir_adicionar_email.sql - Fase de EXPANSÃO (Expand and Contract)
-- Disciplina: Persistência de Dados e Bancos Distribuídos - Trabalho 3 (T3)
-- ==============================================================================

-- 1. Adicionar nova coluna permitindo NULL temporariamente para não travar a tabela
ALTER TABLE cliente ADD COLUMN IF NOT EXISTS email VARCHAR(200);

-- 2. Função e Trigger para sincronizar escritas na mesma transação
-- Enquanto houver instâncias v1 no ar, a escrita canônica permanece em contact_email.
-- O trigger garante que qualquer INSERT ou UPDATE vindo da v1 reflita em email.
CREATE OR REPLACE FUNCTION trg_sync_cliente_email()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.contact_email IS NOT NULL AND (NEW.email IS NULL OR NEW.email <> NEW.contact_email) THEN
        NEW.email := NEW.contact_email;
    ELSIF NEW.email IS NOT NULL AND NEW.contact_email IS NULL THEN
        NEW.contact_email := NEW.email;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cliente_sync_email_biu ON cliente;
CREATE TRIGGER trg_cliente_sync_email_biu
BEFORE INSERT OR UPDATE ON cliente
FOR EACH ROW
EXECUTE FUNCTION trg_sync_cliente_email();
