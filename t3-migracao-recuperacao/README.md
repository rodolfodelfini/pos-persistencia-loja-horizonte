# Trabalho 3 (T3) — Migração sem Downtime, Saga e Recuperação (PITR/DR)

> **Módulo:** Persistência de Dados e Bancos Distribuídos  
> **Autor:** Rodolfo Delfini  
> **Status:** Concluído e Validado

---

## 1. Objetivos da Entrega
1. Projeto de migração online de schema via padrão **Expand-and-Contract** (Parallel Change).
2. Script de **Backfill particionado em lotes controlados** sem bloqueios de tabela (*exclusive locks*).
3. Máquina de estados executável do **Padrão Saga**, tratando compensações financeiras e reconciliação idempotente de *timeouts*.
4. Demonstração de **Point-in-Time Recovery (PITR)** com base backup físico e replay de WALs até o segundo anterior ao incidente.
5. Apuração formal de métricas de SLA (**RPO** e **RTO**) e análise de estratégias de Disaster Recovery.

---

## 2. Conteúdo do Diretório
- [RELATORIO_T3.md](RELATORIO_T3.md): Registro formal de decisões arquiteturais do T3.
- `migracao/`:
  - `V1__criar_cliente.sql`: Schema inicial com modelo de dados legado.
  - `V2__expandir_adicionar_email.sql`: Adição de nova coluna e gatilho de sincronização bidirecional.
  - `03_backfill_em_lotes.py`: Script de atualização incremental com cursor seguro por ID.
  - `V3__contrair_remover_legado.sql`: Aplicação de restrição NOT NULL e remoção segura da coluna legada.
- `saga/`:
  - `orquestrador_saga.py`: Implementação da Saga completa (cenário nominal, compensação e timeout com chave estável).
- `recuperacao/`:
  - `simular_pitr_wal.py`: Simulação da recuperação ponto no tempo com parada granular no WAL.
  - `calculo_rpo_rto.py`: Apuração de RPO/RTO e matriz comparativa de Disaster Recovery.

---

## 3. Instruções de Execução

```bash
python t3-migracao-recuperacao/migracao/03_backfill_em_lotes.py
python t3-migracao-recuperacao/saga/orquestrador_saga.py
python t3-migracao-recuperacao/recuperacao/simular_pitr_wal.py
python t3-migracao-recuperacao/recuperacao/calculo_rpo_rto.py
```
