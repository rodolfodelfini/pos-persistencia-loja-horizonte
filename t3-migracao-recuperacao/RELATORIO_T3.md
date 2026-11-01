# Relatório de Decisão Arquitetural — Trabalho 3 (T3)

**Disciplina:** Persistência de Dados e Bancos Distribuídos  
**Curso:** Pós-Graduação em Arquiteturas de Soluções Escaláveis  
**Autor:** Rodolfo Delfini  
**Caso de Estudo:** Loja Horizonte  

---

## 1. Contexto e Objetivos

O **Trabalho 3 (T3)** aborda os desafios mais críticos da persistência em sistemas distribuídos de alta escala:
1. **Evolução de Schema sem Downtime:** Padrão *Expand-and-Contract* e *Backfill* particionado.
2. **Coordenação Transacional Distribuída:** Orquestração de **Sagas**, ações compensatórias e tratamento de respostas desconhecidas (*timeouts*) com idempotência.
3. **Resiliência e Recuperação de Desastres:** *Point-in-Time Recovery* (PITR) com base backup + WAL, cálculo formal de **RPO / RTO** e reconciliação entre múltiplos bancos desacoplados.

---

## 2. Registro de Decisões de Arquitetura (ADR)

$$\mathbf{Decisão} + \mathbf{Justificativa} + \mathbf{Evidência\ Prática} + \mathbf{Trade\text{-}off}$$

---

### Decisão 1: Migração de Schema via Padrão *Expand-and-Contract* com *Backfill* em Lotes

* **Decisão:** Realizar a alteração de nomes de colunas e modelos (`contact_email` $\rightarrow$ `email`) dividindo a operação em três fases isoladas (*Expandir, Migrar e Contrair*) e executando a atualização do legado via *Backfill* particionado em lotes com cursor por ID.
* **Justificativa:** 
  1. A execução ingênua de `ALTER TABLE cliente RENAME COLUMN contact_email TO email;` quebra imediatamente todas as instâncias em execução da aplicação `v1` que ainda enviam `SELECT contact_email` durante um *rollout* gradual (*canary* / *blue-green*).
  2. Um `UPDATE cliente SET email = contact_email;` sem particionamento adquire *exclusive locks* prolongados sobre toda a tabela de clientes, bloqueando leituras e escritas concorrentes em produção e acumulando atraso (*lag*) catastrófico nas réplicas de leitura.
* **Evidência Prática (`t3-migracao-recuperacao/migracao/`):**
  * **Expansão (`V2__expandir_adicionar_email.sql`):** Adiciona a coluna `email` como nula e estabelece um gatilho transacional síncrono espelhando alterações vindas tanto da aplicação `v1` quanto da `v2`.
  * **Backfill em Lotes (`03_backfill_em_lotes.py`):** Executa o *update* em lotes controlados (`WHERE id > :inicio AND id <= :fim AND (email IS NULL OR email != contact_email)`), com liberação imediata de locks e verificação final de 0 divergências.
  * **Contração (`V3__contrair_remover_legado.sql`):** Aplica a restrição `NOT NULL` e remove a coluna legada `contact_email` somente após a desativação completa de todos os consumidores legados da `v1`.
* **Limite / Trade-off:** Exige coexistência temporária de duas colunas na mesma tabela física, aumentando ligeiramente o espaço em disco e a sobrecarga de I/O enquanto o processo de migração estiver ativo.

---

### Decisão 2: Transações Distribuídas com Padrão Saga Orquestrada (Substituição de 2PC)

* **Decisão:** Rejeitar o protocolo de *Two-Phase Commit* (2PC) e implementar o padrão **Saga Orquestrada** com ações compensatórias explícitas e chave de idempotência para o fluxo de checkout da Loja Horizonte:
  $$\text{Pedido Criado} \longrightarrow \text{Reserva de Estoque} \longrightarrow \text{Cobrança Gateway} \longrightarrow \text{Confirmação}$$
* **Justificativa:**
  1. No 2PC clássico, se os participantes (banco de pedidos e banco de estoque) responderem `PREPARED` e o coordenador ficar inalcançável antes de comunicar o veredito final, os nós participantes ficam permanentemente bloqueados retendo recursos e travas (*locks*), gerando indisponibilidade em cadeia.
  2. A cobrança envolve um gateway financeiro externo que não implementa o protocolo XA/2PC.
  3. A Saga desacopla as etapas em transações locais ACID independentes, liberando os recursos imediatamente e delegando a correção para ações compensatórias de negócio.
* **Evidência Prática (`t3-migracao-recuperacao/saga/orquestrador_saga.py`):**
  * **Cenário de Falha:** Ao simular recusa no cartão de crédito, o orquestrador acionou automaticamente a compensação da reserva de estoque (`compensar_reserva_estoque()`), devolvendo o saldo e marcando o pedido como `CANCELADO`.
  * **Proteção contra Duplicação:** A compensação possui controle idempotente (`compensacoes_executadas`), garantindo que o estoque não seja liberado duas vezes mesmo sob retentativas de mensagens.
* **Limite / Trade-off:** Durante o ciclo de vida da Saga, o sistema exibe estados intermediários visíveis (*eventual consistency*), não oferecendo isolamento atômico global instantâneo (*Dirty Reads* de negócio temporários).

---

### Decisão 3: Tratamento de Timeout com Indeterminação e Chave de Idempotência Estável

* **Decisão:** Tratar respostas de erro indefinido / *timeout* de gateway de pagamento categorizando o estado como `DESCONHECIDO` e mantendo o pedido em `AGUARDANDO_RECONCILIACAO` consultando com a **mesma chave de idempotência estável** (`Idempotency-Key`).
* **Justificativa:** Conforme o princípio fundamental dos sistemas distribuídos: **ausência de resposta não é evidência de ausência de efeito**. Se houver um *timeout* e a aplicação tentar cobrar novamente com uma nova chave, o cliente sofrerá cobrança em duplicidade. Se a aplicação compensar o estoque imediatamente às cegas, o cliente poderá ter sido cobrado e ficar sem o produto.
* **Evidência Prática (`t3-migracao-recuperacao/saga/orquestrador_saga.py`):**
  No Cenário 3 da demonstração, diante de um erro de rede, o pedido #703 foi mantido suspenso. A consulta automatizada com a mesma chave estável localizou a cobrança confirmada no gateway e finalizou o pedido com integridade, sem duplicar transações bancárias.
* **Limite / Trade-off:** Pedidos sob investigação de timeout ficam retidos em estado transitório por alguns minutos até a resolução do polling/webhook de reconciliação, exigindo interface amigável para o usuário final.

---

### Decisão 4: Estratégia de Continuidade de Negócio via PITR com Base Backup e Arquivamento de WAL

* **Decisão:** Implementar a estratégia de proteção contra corrupção e exclusão acidental através de **Point-in-Time Recovery (PITR)** no PostgreSQL, combinando um *backup físico de base periódico* com fluxo contínuo de arquivamento de arquivos de log (*WAL Archiving*).
* **Justificativa:** Réplicas secundárias síncronas ou assíncronas apenas protegem contra panes físicas de servidor; diante de um `DELETE FROM pedido;` indevido de um operador ou injeção de SQL, a réplica replica a destruição com precisão milimétrica. Um dump lógico diário (SQL dump) não permite restauração granular até o segundo exato anterior à falha.
* **Evidência Prática (`t3-migracao-recuperacao/recuperacao/simular_pitr_wal.py`):**
  * Cenário de simulação de incidente:
    * 10:00:00: Backup físico de base disponível.
    * 10:03:00 e 10:05:00: Pedidos válidos #801 e #802 gravados no WAL.
    * 10:07:00: Exclusão indevida executada por falha operacional.
    * Alvo configurado: `recovery_target_time = '10:06:59'`.
  * **Resultado Comprovado:** A restauração reaplicou com sucesso os pedidos legítimos #801 e #802 e interrompeu o *replay* 1 segundo antes do desastre, resgatando 100% dos dados válidos.
* **Limite / Trade-off:** Requer armazenamento dedicado para reter o volume de WALs arquivados entre os ciclos de backup de base e demanda ambiente isolado para validação antes da devolução definitiva do tráfego.

---

## 3. Resolução e Análise de SLA: Métricas de RPO e RTO da Loja Horizonte

Com base nos dados operacionais do incidente:
* **Incidente:** Ocorrido às **10:00:00**.
* **Ponto Recuperável Mais Recente nos Logs:** **09:55:00**.
* **Serviço Restaurado e Validado:** **10:40:00**.

### Cálculos:
$$\text{RPO Real} = 10:00:00 - 09:55:00 = \mathbf{5\ minutos\ de\ dados\ perdidos}$$
$$\text{RTO Real} = 10:40:00 - 10:00:00 = \mathbf{40\ minutos\ de\ paralisação}$$

| Dimensão | Meta de SLA Estipulada | Resultado Obtido | Parecer Arquitetural |
| :--- | :--- | :--- | :--- |
| **RPO** | Até 5 minutos | **5 minutos** | **ATENDIDO:** A política de arquivamento frequente de WAL garantiu que a perda ficasse dentro do teto tolerado. |
| **RTO** | Até 30 minutos | **40 minutos** | **VIOLADO:** A meta de tempo de recuperação foi estourada em 10 minutos devido ao tempo excessivo gasto na reconstrução e validação manual do ambiente. |

**Plano de Ação Corretivo:** Para cumprir a meta de RTO $\le 30$ minutos, a arquitetura deve evoluir da estratégia pura de *Backup/Restore* para um modelo de **Warm Standby**, mantendo uma instância secundária pré-provisionada em prontidão para absorver a carga via chaveamento de DNS.

---

## 4. Como Executar os Scripts do T3

```bash
# 1. Executar simulação de migração de schema com Backfill em lotes
python t3-migracao-recuperacao/migracao/03_backfill_em_lotes.py

# 2. Executar orquestrador de Saga com fluxos de compensação e idempotência
python t3-migracao-recuperacao/saga/orquestrador_saga.py

# 3. Executar restauração PITR com parada exata anterior ao desastre
python t3-migracao-recuperacao/recuperacao/simular_pitr_wal.py

# 4. Executar cálculo analítico de métricas RPO e RTO e matriz de DR
python t3-migracao-recuperacao/recuperacao/calculo_rpo_rto.py
```
