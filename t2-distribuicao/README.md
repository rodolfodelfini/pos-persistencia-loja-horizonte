# Trabalho 2 (T2) — Replicação e Análise de Distribuição

> **Módulo:** Persistência de Dados e Bancos Distribuídos  
> **Autor:** Rodolfo Delfini  
> **Status:** Concluído e Validado

---

## 1. Objetivos da Entrega
1. Estratégia de particionamento de dados (*Sharding*) e controle de desbalanceamento (*Hotspots*).
2. Prova matemática de estabilidade do **Anel de Hash Consistente com Nós Virtuais**.
3. Dimensionamento de Quórum Majoritário ($R + W > N$) sob tolerância à queda de instâncias.
4. Análise de compromissos do **Teorema CAP** na Loja Horizonte (CP no Checkout vs AP no Catálogo).
5. Demonstração de anomalias de replicação assíncrona (*Monotonic Reads* e *Read-Your-Writes*) e mitigação via token de sessão.

---

## 2. Conteúdo do Diretório
- [RELATORIO_T2.md](RELATORIO_T2.md): Registro formal de decisões arquiteturais do T2.
- `scripts/`:
  - `01_anel_hash_consistente.py`: Comparativo de churn entre Hash Modular e Anel Consistente com nós virtuais.
  - `02_quorum_e_cap_simulador.py`: Simulação de quórum aritmético e comportamento sob partição de rede.
  - `03_garantias_sessao_simulador.py`: Anomalias de atraso de replicação e roteador com garantia de sessão.

---

## 3. Instruções de Execução

```bash
python t2-distribuicao/scripts/01_anel_hash_consistente.py
python t2-distribuicao/scripts/02_quorum_e_cap_simulador.py
python t2-distribuicao/scripts/03_garantias_sessao_simulador.py
```
