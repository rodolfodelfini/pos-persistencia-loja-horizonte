"""
==============================================================================
Script de Backfill em Lotes Controlados - Trabalho 3 (T3)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Engenharia de Migração:
- Executa a migração de registros legados sem travar a tabela inteira (sem locks longos).
- Lotes pequenos particionados por faixas de ID (cursor incremental).
- Cláusula idempotente: AND email IS DISTINCT FROM contact_email.
==============================================================================
"""

import sqlite3
import time

def executar_backfill():
    print("=" * 70)
    print("  INICIANDO BACKFILL PARTICIONADO EM LOTES (ONLINE SCHEMA CHANGE)")
    print("=" * 70)
    
    # Criando banco em memória para simular o processo
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Setup
    cursor.execute("""
    CREATE TABLE cliente (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        contact_email TEXT NOT NULL,
        email TEXT
    )
    """)
    
    # Popula 25 clientes legados para migração
    clientes = [(i, f"Cliente {i}", f"cliente_{i}@horizonte.com.br", None) for i in range(1, 26)]
    cursor.executemany("INSERT INTO cliente VALUES (?, ?, ?, ?)", clientes)
    conn.commit()
    
    print("[INFO] 25 registros legados criados. Coluna 'email' está NULL.")
    
    # Parâmetros de engenharia de migração
    chunk_size = 5
    max_id = 25
    cursor_inicio = 0
    total_migrado = 0
    
    print(f"\n[CONFIGURAÇÃO]: Tamanho do lote = {chunk_size} registros por transação.\n")
    
    while cursor_inicio < max_id:
        cursor_fim = cursor_inicio + chunk_size
        
        # Query particionada com liberação imediata de lock por lote
        query = """
            UPDATE cliente
            SET email = contact_email
            WHERE id > ? AND id <= ?
              AND (email IS NULL OR email != contact_email)
        """
        cursor.execute(query, (cursor_inicio, cursor_fim))
        afetados = cursor.rowcount
        conn.commit()
        
        total_migrado += afetados
        print(f"  -> Lote [{cursor_inicio+1:>2} até {cursor_fim:>2}]: {afetados} registros atualizados com sucesso.")
        
        cursor_inicio = cursor_fim
        # Simula pausa rápida para alívio de I/O e replicação
        time.sleep(0.05)
        
    print("-" * 70)
    print(f"[CONCLUÍDO]: Backfill finalizado! Total de registros migrados: {total_migrado}.")
    
    # Validação de convergência
    cursor.execute("SELECT COUNT(*) FROM cliente WHERE email IS NULL OR email != contact_email")
    divergencias = cursor.fetchone()[0]
    print(f"[VERIFICAÇÃO DE INTEGRIDADE]: Divergências restantes: {divergencias}")
    if divergencias == 0:
        print("[SUCESSO]: Critério de aceite atingido. Seguro avançar para a fase de Contração (V3).")
    conn.close()

if __name__ == "__main__":
    executar_backfill()
