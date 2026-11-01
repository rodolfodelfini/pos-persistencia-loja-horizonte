# Relatório de Decisão Arquitetural — Trabalho 1 (T1)

**Disciplina:** Persistência de Dados e Bancos Distribuídos  
**Curso:** Pós-Graduação em Arquiteturas de Soluções Escaláveis  
**Autor:** Rodolfo Delfini  
**Caso de Estudo:** Loja Horizonte  

---

## 1. Introdução e Contexto do Caso

A **Loja Horizonte** é uma plataforma de comércio eletrônico multi-tenant que reúne diferentes perfis de carga e requisitos de consistência:
* Checkout com controle rigoroso de estoque para evitar vendas acima da disponibilidade (*overbooking*).
* Catálogo amplo de produtos fornecidos por múltiplos lojistas, com especificações heterogêneas e voláteis.
* Gestão rápida de autenticação, carrinhos e sessões com expiração automática.
* Motor de busca moderno por aproximação semântica com suporte a inteligência artificial.

Para atender a esses requisitos sem incorrer no anti-padrão de "banco de dados faz-tudo", adotou-se uma estratégia de **Persistência Poliglota**.

---

## 2. Registro de Decisões de Arquitetura (ADR)

Para cada decisão técnica de persistência, documentamos a motivação de negócio, as evidências práticas e os trade-offs assumidos:
$$\mathbf{Decisão} + \mathbf{Justificativa} + \mathbf{Evidência\ Prática} + \mathbf{Trade\text{-}off}$$

---

### Decisão 1: Persistência Relacional para Pedidos e Estoque (PostgreSQL)

* **Decisão:** Utilizar banco de dados Relacional ACID (PostgreSQL) para gerenciar o ciclo de vida dos pedidos, clientes e o saldo físico de estoque.
* **Justificativa:** A operação de reserva exige verificação rigorosa de integridade e garantia da invariante fundamental $\text{estoque\_disponivel} \ge 0$. Em um checkout de alta concorrência, o isolamento transacional impede vendas duplicadas do último item em estoque.
* **Evidência Prática:** Implementação do comando atômico com cláusula condicional e retorno explícito (`sql/03_consulta_reserva_atomica.sql`):
  ```sql
  BEGIN;
  UPDATE estoque 
  SET disponivel = disponivel - 1, reservado = reservado + 1
  WHERE produto_id = 10 AND disponivel >= 1
  RETURNING produto_id;

  INSERT INTO reserva (pedido_id, produto_id, quantidade)
  VALUES (701, 10, 1);
  COMMIT;
  ```
  Na demonstração executável (`scripts/t1_demo_completo.py`), a terceira tentativa concorrente em um estoque de 2 unidades resultou imediatamente em `ROLLBACK`, preservando o saldo zero sem permitir valores negativos.
* **Limite / Trade-off:** Escalar escritas relacionais horizontalmente exige estratégias complexas de particionamento (*sharding*). Transações que envolvem múltiplos *shards* exigem protocolos de coordenação com maior latência (ex.: 2PC ou Sagas).

---

### Decisão 2: Persistência Documental para Catálogo de Produtos (MongoDB)

* **Decisão:** Armazenar o catálogo de produtos em banco orientado a documentos (MongoDB).
* **Justificativa:** Os produtos pertencem a categorias distintas (ex.: mochilas com volume e impermeabilidade vs. botas com numeração e solado). Documentos agregam em uma única unidade de leitura todos os atributos que viajam juntos, eliminando múltiplos *JOINs* lentos e alterações de DDL a cada novo atributo de lojista.
* **Evidência Prática:** Documentos cadastrados com `schema_version` explícito e subestruturas flexíveis (`mongo/seed_catalogo.js`):
  ```json
  {
    "produto_id": 10,
    "nome": "Mochila de Trilha 25L Impermeável",
    "schema_version": 2,
    "atributos": {
      "capacidade_l": 25,
      "compartimento_notebook": true,
      "material": "Cordura Ripstop"
    }
  }
  ```
* **Limite / Trade-off:** A ausência de regras rígidas de integridade referencial exige disciplina da aplicação para validar esquemas e versionamento. Não há transações com garantias distribuídas triviais entre agregados isolados.

---

### Decisão 3: Persistência Chave-Valor para Sessões e Cache (Redis)

* **Decisão:** Utilizar banco chave-valor em memória (Redis) para controle de sessões ativas e tokens temporários.
* **Justificativa:** O acesso ocorre invariavelmente por chave exata (`sessao:{token}`). A utilização de TTL (*Time-To-Live*) nativo assegura a limpeza de sessões órfãs sem necessidade de tarefas agendadas (*cron jobs*) no banco relacional.
* **Evidência Prática:** Comando de criação com expiração automática (`redis/seed_sessoes.redis`):
  ```redis
  SET sessao:token_abc_123 "cliente=42;status=ativo" EX 900
  ```
  No script executado, a chave expirou pontualmente após o tempo limite, retornando `None` nas consultas subsequentes.
* **Limite / Trade-off:** Banco operando predominantemente em memória RAM possui maior custo por gigabyte. Não é adequado como fonte autoritativa de dados financeiros que exijam durabilidade garantida contra perda repentina de energia sem políticas estritas de AOF/RDB.

---

### Decisão 4: Persistência Vetorial para Busca Semântica (pgvector)

* **Decisão:** Integrar o índice vetorial `pgvector` ao PostgreSQL para busca de produtos por proximidade semântica.
* **Justificativa:** Consultas textuais tradicionais (*Full-Text Search*) falham quando o usuário pesquisa termos conceituais (ex.: *"equipamento para caminhada"* procurando *"mochila de trilha"* ou *"bota impermeável"*). O embedding captura a semântica em espaço multidimensional.
* **Evidência Prática:** Cálculo formal de distância euclidiana executado na demonstração:
  * Consulta $q = (1.0, 0.0)$
  * Candidato A (Mochila 25L) $= (0.9, 0.1) \rightarrow \text{Distância} = \sqrt{(1 - 0.9)^2 + (0 - 0.1)^2} \approx \mathbf{0.1414}$
  * Candidato B (Caderno) $= (0.0, 1.0) \rightarrow \text{Distância} = \sqrt{(1 - 0.0)^2 + (0 - 1.0)^2} \approx \mathbf{1.4142}$
  * **Resultado:** Ordenação imediata de A antes de B por relevância temática.
* **Limite / Trade-off:** A similaridade matemática reflete proximidade estatística, não equivalência exata de negócio. É indispensável combinar o filtro vetorial com regras relacionais (ex.: filtrar apenas produtos com `estoque > 0` e lojistas ativos).

---

## 3. Resposta às Seis Perguntas de Acesso da Arquitetura

| Modelo | Pergunta Típica de Acesso | Justificativa no Caso Loja Horizonte |
| :--- | :--- | :--- |
| **Relacional** | *Quais itens compõem este pedido?* | Garante integridade referencial estrita e transações atômicas no checkout. |
| **Documento** | *Qual é o produto com todos os seus atributos?* | Agrupa dados heterogêneos de catálogo que são lidos em bloco. |
| **Chave-valor** | *Qual é o estado da sessão desta chave?* | Responde em microssegundos por chave primária com expiração automática. |
| **Grafo** | *Quais contas e cartões se conectam em até dois saltos?* | Permite navegação de relacionamentos para detecção de fraudes. |
| **Série temporal** | *Como variou a latência do checkout na última hora?* | Gravações sequenciais contínuas com políticas de downsampling e retenção. |
| **Vetor** | *Quais produtos do catálogo se parecem com esta consulta?* | Ranqueamento por similaridade semântica em alta dimensionalidade. |

---

## 4. Como Executar as Evidências do T1

### Modo 1: Execução Imediata via Script Python (Sem dependências externas)
```bash
python scripts/t1_demo_completo.py
```

### Modo 2: Execução Completa via Docker Compose
```bash
docker compose up -d
docker compose exec -T postgres psql -U horizonte_user -d horizonte_db -f /docker-entrypoint-initdb.d/01_schema.sql
docker compose exec -T postgres psql -U horizonte_user -d horizonte_db -f /docker-entrypoint-initdb.d/02_seed.sql
```
E testar a consulta atômica de reserva:
```bash
docker compose exec -T postgres psql -U horizonte_user -d horizonte_db -f /sql/03_consulta_reserva_atomica.sql
```

---

## 5. Conclusão do Trabalho 1

O Trabalho 1 comprova que uma arquitetura escalável e resiliente não depende da escolha dogmática de um único motor de persistência, mas sim do mapeamento rigoroso entre **acesso dominante**, **invariante de negócio** e **compromisso operacional**. A base montada no T1 serve como alicerce para as análises de particionamento e replicação do Trabalho 2.
