"""
==============================================================================
Demonstração Executável - Trabalho 1 (T1)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Este script valida e demonstra os quatro pilares de persistência do T1:
1. Relacional: Transação atômica local com garantia de invariante (Estoque >= 0)
2. Documental: Agregação flexível com atributos variáveis e schema_version
3. Chave-Valor: Localização rápida por chave primária e controle de TTL
4. Vetorial: Busca semântica por vizinho mais próximo (Distância Euclidiana L2)
==============================================================================
"""

import math
import sqlite3
import time
import json

def linha(titulo):
    print("\n" + "=" * 70)
    print(f"  {titulo.upper()}")
    print("=" * 70)

# ==============================================================================
# 1. PILAR RELACIONAL: TRANSAÇÃO ATÔMICA E INVARIANTE DE ESTOQUE
# ==============================================================================
def demonstrar_pilar_relacional():
    linha("1. Pilar Relacional: Reserva Atômica de Estoque (PostgreSQL / ACID)")
    
    # Criando banco relacional em memória para demonstração imediata
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # DDL
    cursor.execute("""
    CREATE TABLE estoque (
        produto_id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        disponivel INTEGER NOT NULL CHECK (disponivel >= 0),
        reservado INTEGER NOT NULL DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE reserva (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL
    )
    """)
    
    # Seed
    cursor.execute("INSERT INTO estoque VALUES (10, 'Mochila de Trilha 25L', 2, 0)")
    conn.commit()
    
    print("[INFO] Estado Inicial do Estoque:")
    for row in cursor.execute("SELECT * FROM estoque"):
        print(f"       Produto {row[0]} ({row[1]}): Disponível={row[2]}, Reservado={row[3]}")

    def tentar_reservar(pedido_id, produto_id, qtd=1):
        print(f"\n---> [Transação] Tentando reservar {qtd} un. do Produto {produto_id} para Pedido {pedido_id}...")
        try:
            # Atomic update condicional com garantia de invariante (disponivel >= qtd)
            cursor.execute("""
                UPDATE estoque
                SET disponivel = disponivel - ?,
                    reservado = reservado + ?
                WHERE produto_id = ? AND disponivel >= ?
            """, (qtd, qtd, produto_id, qtd))
            
            if cursor.rowcount == 0:
                conn.rollback()
                print(f"     [FALHA / ROLLBACK] Invariante violada! Estoque insuficiente para produto {produto_id}.")
                return False
            
            cursor.execute("""
                INSERT INTO reserva (pedido_id, produto_id, quantidade)
                VALUES (?, ?, ?)
            """, (pedido_id, produto_id, qtd))
            
            conn.commit()
            print(f"     [SUCESSO / COMMIT] Reserva confirmada com atomicidade local!")
            return True
        except Exception as e:
            conn.rollback()
            print(f"     [ERRO / ROLLBACK]: {e}")
            return False

    # Cenário A: Reserva com sucesso (tem 2, pede 1)
    tentar_reservar(701, 10, 1)
    
    # Cenário B: Reserva com sucesso (tem 1, pede 1)
    tentar_reservar(702, 10, 1)
    
    # Cenário C: Tentativa de overbooking (tem 0, pede 1) -> Invariante bloqueia
    tentar_reservar(703, 10, 1)

    print("\n[INFO] Estado Final do Estoque pós-concorrência:")
    for row in cursor.execute("SELECT * FROM estoque"):
        print(f"       Produto {row[0]} ({row[1]}): Disponível={row[2]}, Reservado={row[3]}")
    conn.close()

# ==============================================================================
# 2. PILAR DOCUMENTAL: DADOS COM ATRIBUTOS VARIÁVEIS E DINÂMICOS
# ==============================================================================
def demonstrar_pilar_documental():
    linha("2. Pilar Documental: Catálogo com Atributos Heterogêneos (MongoDB)")
    
    catalogo = [
        {
            "produto_id": 10,
            "nome": "Mochila de Trilha",
            "categoria": "Aventura",
            "schema_version": 2,
            "atributos": {
                "capacidade_l": 25,
                "impermeavel": True,
                "compartimento_notebook": True
            }
        },
        {
            "produto_id": 11,
            "nome": "Bota de Trekking",
            "categoria": "Calçados",
            "schema_version": 2,
            "atributos": {
                "tamanho": 41,
                "tipo_solado": "Vibram",
                "impermeavel": True
            }
        }
    ]
    
    print("[INFO] Documentos armazenados sem necessidade de DDL rígido (dados que viajam juntos):")
    for doc in catalogo:
        print(f"\nID: {doc['produto_id']} | Nome: {doc['nome']} (Schema v{doc['schema_version']})")
        print(f"Atributos Dinâmicos: {json.dumps(doc['atributos'], indent=2)}")

# ==============================================================================
# 3. PILAR CHAVE-VALOR: ACESSO RÁPIDO E EXPIRAÇÃO COM TTL
# ==============================================================================
def demonstrar_pilar_chave_valor():
    linha("3. Pilar Chave-Valor: Sessão do Usuário e TTL (Redis)")
    
    class RedisSimulado:
        def __init__(self):
            self.store = {}
            self.expirations = {}
            
        def set(self, key, value, ex_seconds=None):
            self.store[key] = value
            if ex_seconds:
                self.expirations[key] = time.time() + ex_seconds
                
        def get(self, key):
            if key in self.expirations and time.time() > self.expirations[key]:
                del self.store[key]
                del self.expirations[key]
                return None
            return self.store.get(key)
            
        def ttl(self, key):
            if key in self.expirations:
                restante = int(self.expirations[key] - time.time())
                return max(0, restante)
            return -1

    redis = RedisSimulado()
    chave = "sessao:token_abc_123"
    valor = "cliente=42;permissao=comprador"
    
    print(f"[COMANDO] SET {chave} '{valor}' EX 2")
    redis.set(chave, valor, ex_seconds=2)
    
    print(f"[CONSULTA IMEDIATA] GET {chave} -> {redis.get(chave)} (TTL: {redis.ttl(chave)}s)")
    print("[AGUARDANDO EXPIRAÇÃO] Simulando espera de 2.2 segundos pelo TTL...")
    time.sleep(2.2)
    print(f"[CONSULTA APÓS TTL]  GET {chave} -> {redis.get(chave)} (Chave expirou automaticamente!)")

# ==============================================================================
# 4. PILAR VETORIAL: BUSCA SEMÂNTICA POR PROXIMIDADE (PGVECTOR)
# ==============================================================================
def demonstrar_pilar_vetorial():
    linha("4. Pilar Vetorial: Busca por Proximidade e Distância Euclidiana (pgvector)")
    
    # Simulação do motor vetorial da Loja Horizonte:
    # Consulta q = (1, 0) -> "mochila para trilha"
    # Candidato A = (0.9, 0.1)
    # Candidato B = (0.0, 1.0)
    
    consulta_q = (1.0, 0.0)
    candidatos = [
        {"id": "A", "nome": "Mochila de Trilha 25L", "vetor": (0.9, 0.1)},
        {"id": "B", "nome": "Caderno Universitário", "vetor": (0.0, 1.0)}
    ]
    
    def distancia_euclidiana(v1, v2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    print(f"Vetor da Consulta q: {consulta_q} ('equipamento para trilha/caminhada')\n")
    
    resultados = []
    for cand in candidatos:
        dist = distancia_euclidiana(consulta_q, cand["vetor"])
        cand["distancia"] = dist
        resultados.append(cand)
        print(f"Candidato {cand['id']} ({cand['nome']}):")
        print(f"  Vetor: {cand['vetor']}")
        print(f"  Cálculo: sqrt[(1 - {cand['vetor'][0]})^2 + (0 - {cand['vetor'][1]})^2] = {dist:.4f}")
        
    resultados.sort(key=lambda x: x["distancia"])
    
    print("\n[RESULTADO DA ORDENAÇÃO SEMÂNTICA (Menor Distância Primeiro)]:")
    for rank, item in enumerate(resultados, 1):
        print(f"  {rank}º Lugar: Produto {item['id']} - {item['nome']} (Distância: {item['distancia']:.4f})")
    
    print("\nConclusão: O candidato A é muito mais próximo semanticamente de q do que B.")

if __name__ == "__main__":
    print("=" * 70)
    print("  INICIANDO SUÍTE DE TESTES E DEMONSTRAÇÕES - TRABALHO 1 (T1)")
    print("=" * 70)
    demonstrar_pilar_relacional()
    demonstrar_pilar_documental()
    demonstrar_pilar_chave_valor()
    demonstrar_pilar_vetorial()
    print("\n" + "=" * 70)
    print("  TODAS AS VALIDAÇÕES DE T1 FORAM EXECUTADAS COM SUCESSO!")
    print("=" * 70)
