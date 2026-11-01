# Relatório de Decisão Arquitetural — Trabalho 2 (T2)

**Disciplina:** Persistência de Dados e Bancos Distribuídos  
**Curso:** Pós-Graduação em Arquiteturas de Soluções Escaláveis  
**Autor:** Rodolfo Delfini  
**Caso de Estudo:** Loja Horizonte  

---

## 1. Contexto e Objetivos

O **Trabalho 2 (T2)** evolui a arquitetura da Loja Horizonte da camada lógica (modelagem poliglota do T1) para a camada física de **Topologia Distribuída**. Os desafios centrais abordados são:
1. Particionamento de dados (*Sharding*) e controle de desbalanceamento (*Hotspots*).
2. Estabilidade de nós sob expansão horizontal via **Anel de Hash Consistente**.
3. Replicação Líder-Seguidores, Quorum e tolerância a partições de rede (**Teorema CAP**).
4. Preservação da experiência do usuário sob replicação assíncrona (**Garantias de Sessão**).

---

## 2. Registro de Decisões de Arquitetura (ADR)

$$\mathbf{Decisão} + \mathbf{Justificativa} + \mathbf{Evidência\ Prática} + \mathbf{Trade\text{-}off}$$

---

### Decisão 1: Particionamento por Hash Consistente com Chave Composta e Nós Virtuais

* **Decisão:** Adotar particionamento baseado em anel de **Hash Consistente com Nós Virtuais**, utilizando como chave de partição primária `lojista_id` e, para grandes contas corporativas (*megasellers*), chave composta `lojista_id + bucket_subdivisao`.
* **Justificativa:** 
  1. No particionamento modular ingênuo ($\text{hash} \pmod N$), adicionar ou remover um servidor altera o divisor $N$ e força a migração desnecessária de quase $85\%\text{ a }100\%$ de toda a base de dados.
  2. No Hash Consistente com anel de sucessores, a entrada de um nó $D$ movimenta apenas o intervalo imediato $(C_{antigo}, D]$, preservando todas as demais partições intactas.
  3. O uso de nós virtuais (ex.: 100 *vnodes* por servidor físico) suaviza discrepâncias estatísticas e impede que um lojista concentre 70% de todo o tráfego em uma única máquina (*Hotspot*).
* **Evidência Prática (`t2-distribuicao/scripts/01_anel_hash_consistente.py`):**
  * **Hash Modular ($N=3 \rightarrow N=4$):** 87.5% das chaves foram forçadas a migrar de partição com a entrada de apenas 1 nó.
  * **Anel de Hash Consistente:** Com a entrada de um novo nó de capacidade $D=65$, apenas a chave 60 migrou para $D$; as chaves 70 (no nó $C$) e 90 (no nó $A$) permaneceram estáveis.
  * **Balanceamento com Nós Virtuais:** Em 10.000 requisições simuladas, os três shards dividiram a carga de forma equilibrada: Shard-1 (35.4%), Shard-2 (35.0%) e Shard-3 (29.6%), eliminando o risco do hotspot crítico.
* **Limite / Trade-off:** Consultas analíticas que precisam varrer o faturamento de todos os lojistas simultaneamente deixam de bater em um único nó e tornam-se operações do tipo *scatter-gather* (consultam todos os shards e agregam em memória), aumentando a sobrecarga de rede.

---

### Decisão 2: Replicação Líder-Seguidor com Quorum Majoritário ($N=3, W=2, R=2$)

* **Decisão:** Configurar a topologia de replicação com 1 Líder e 2 Réplicas ($N=3$), adotando quorum de escrita $W=2$ e quorum de leitura $R=2$.
* **Justificativa:** 
  Pela propriedade aritmética de quorum:
  $$R + W > N \implies 2 + 2 = 4 > 3$$
  Garante-se interseção não vazia entre o conjunto de réplicas que confirmaram a escrita e o conjunto consultado pela leitura. Sempre haverá ao menos um nó que contém a versão mais recente. Além disso, se 1 nó sofrer indisponibilidade total, tanto a escrita quanto a leitura continuam operando normalmente sem interrupção ($3 - 1 = 2 \ge W, R$).
* **Evidência Prática (`t2-distribuicao/scripts/02_quorum_e_cap_simulador.py`):**
  * Na configuração $W=3, R=1$, a perda de um único nó travou imediatamente todas as novas confirmações de pedidos.
  * Na configuração $W=2, R=2$, a simulação comprovou que mesmo com 1 réplica desligada, o limiar mínimo de 2 confirmações foi atingido com sucesso.
* **Limite / Trade-off:** A escrita precisa aguardar o retorno em rede da réplica exigida antes de confirmar o `COMMIT` ao cliente, acrescentando latência de *round-trip time* (RTT) em relação a uma escrita puramente assíncrona local ($W=1$).

---

### Decisão 3: Teorema CAP Bifurcado por Domínio de Negócio (CP no Checkout vs AP no Catálogo)

* **Decisão:** Em caso de partição de rede incontrolável ($P$):
  * **Serviço de Checkout/Estoque:** Opera em modo **CP** (Consistência estrita / Linearizabilidade), rejeitando ou enfileirando pedidos caso o nó perca quorum com a maioria.
  * **Serviço de Catálogo/Busca:** Opera em modo **AP** (Alta Disponibilidade), respondendo com dados locais mesmo que temporariamente defasados (*soft state*).
* **Justificativa:** 
  1. No checkout, uma resposta rápida com dado inconsistente causa venda além do estoque (*overbooking*), gerando quebra de contrato legal e custo operacional de cancelamento.
  2. No catálogo, a visualização de uma foto ou especificação técnica com alguns segundos de atraso não traz prejuízo irreparável à experiência do cliente.
* **Evidência Prática (`t2-distribuicao/scripts/02_quorum_e_cap_simulador.py`):**
  Sob partição forçada entre o Nó A e o Nó B:
  * A tentativa de reserva no Nó B isolado retornou `503 SERVICE UNAVAILABLE`, protegendo o estoque.
  * A consulta de catálogo no mesmo Nó B respondeu `200 OK` com a versão em cache local, garantindo que os usuários continuassem navegando na loja.
* **Limite / Trade-off:** Clientes tentando fechar compras na partição minoritária receberão mensagem de erro temporário durante a falha de rede até que o enlace seja restabelecido.

---

### Decisão 4: Roteamento de Leituras com Token de Progresso de Sessão (*Session Guarantees*)

* **Decisão:** Implementar garantia de sessão do tipo **Read-Your-Writes** e **Monotonic Reads** por meio de um cabeçalho/token de versão mínima observada (`min_version`) repassado pelo cliente ou pelo API Gateway.
* **Justificativa:** Em replicação assíncrona, balancear requisições em round-robin entre réplicas com diferentes atrasos de sincronização (*lag*) produz o efeito de "voltar no tempo" (o cliente lê versão 7, recarrega e vê versão 6), além de fazer o usuário não enxergar o endereço que acabou de atualizar.
* **Evidência Prática (`t2-distribuicao/scripts/03_garantias_sessao_simulador.py`):**
  * **Round-robin ingênuo:** Gerou regressão temporal (leitura 1 = v7, leitura 2 = v6).
  * **Violação de Read-your-writes:** Cliente 42 alterou endereço (v8), recebeu sucesso, mas a tela seguinte na réplica B continuou exibindo o endereço antigo (v7).
  * **Roteador com Token de Sessão:** Ao anexar `min_version=8`, o roteador identificou o atraso das réplicas secundárias e direcionou a leitura com segurança para o nó atualizado, eliminando anomalias visuais.
* **Limite / Trade-off:** Durante períodos de alto volume de escritas de um mesmo usuário, as leituras daquela sessão serão temporariamente afuniladas no Líder, reduzindo o alívio de carga nas réplicas secundárias.

---

## 3. Respostas às Perguntas do Módulo

| Pergunta Técnica | Resposta Arquitetural |
| :--- | :--- |
| *No anel A=20, B=50, D=65, C=80, quem recebe a chave 62?* | **Nó D=65**, pois é o primeiro sucessor no sentido horário cujo valor é $\ge 62$. |
| *Uma consulta sem a chave de shard necessariamente usa apenas um nó?* | **Não.** Consultas sem a chave de partição precisam ser enviadas para **todos os shards** (*scatter-gather*), elevando a sobrecarga de CPU e rede. |
| *Dividir uma tabela em partições no mesmo servidor protege contra perda desse servidor?* | **Não.** Particionamento local organiza dados para ganho de performance e manutenção, mas a máquina física continua sendo um **domínio único de falha**. |
| *CAP permite escolher ignorar falhas de rede em um sistema distribuído?* | **Falso.** Falhas parciais e partições ($P$) são uma inevitabilidade física da rede; o arquiteto pode apenas escolher como o sistema se comporta diante delas ($C$ ou $A$). |

---

## 4. Como Executar as Demonstrações do T2

No terminal, execute os três scripts de validação:
```bash
# 1. Demonstração de Hash Consistente, nós virtuais e eliminação de Hotspots
python t2-distribuicao/scripts/01_anel_hash_consistente.py

# 2. Demonstração de Quorum (R+W > N) e Teorema CAP (CP vs AP)
python t2-distribuicao/scripts/02_quorum_e_cap_simulador.py

# 3. Demonstração de violação de Monotonic Reads / Read-your-writes e correção
python t2-distribuicao/scripts/03_garantias_sessao_simulador.py
```
