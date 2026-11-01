# Trabalho 1 (T1) — Modelos, Decisões e Consultas

> **Módulo:** Persistência de Dados e Bancos Distribuídos  
> **Autor:** Rodolfo Delfini  
> **Status:** Concluído e Validado

---

## 1. Objetivos da Entrega
1. Estratégia de modelagem poliglota para os domínios de negócio da Loja Horizonte.
2. Garantia de invariante transacional local (`estoque >= 0`) via SQL transacional com cláusula `RETURNING`.
3. Modelagem de catálogo em documentos JSON heterogêneos com versionamento explícito (`schema_version`).
4. Gestão de sessões efêmeras em banco chave-valor com expiração nativa por TTL.
5. Busca semântica vetorial com cálculo de distância euclidiana.
6. Relatório estruturado de decisões de arquitetura com justificativas e trade-offs.

---

## 2. Conteúdo do Diretório
- [RELATORIO_T1.md](RELATORIO_T1.md): Registro formal de decisões arquiteturais do T1.
- [docker-compose.yml](docker-compose.yml): Manifesto de infraestrutura local (PostgreSQL 16 com pgvector, MongoDB 7 e Redis 7).
- `sql/`:
  - `01_schema_relacional.sql`: DDL relacional e ativação da extensão vetorial.
  - `02_seed_pedidos_estoque.sql`: Carga de clientes, estoque, pedidos e embeddings.
  - `03_consulta_reserva_atomica.sql`: Transação de reserva atômica e consultas por similaridade.
- `mongo/seed_catalogo.js`: Carga inicial do catálogo documental com atributos variáveis por categoria.
- `redis/seed_sessoes.redis`: Comandos de gestão de chave-valor e expiração temporal.
- `scripts/t1_demo_completo.py`: Suíte automatizada para validação dos quatro modelos.

---

## 3. Instruções de Execução

Para executar a validação completa do T1:
```bash
python scripts/t1_demo_completo.py
```
*(Executa a validação das invariantes de negócio e cálculos vetoriais em console).*
