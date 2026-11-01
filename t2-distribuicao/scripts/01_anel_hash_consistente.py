"""
==============================================================================
Módulo de Distribuição e Sharding - Trabalho 2 (T2)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações:
1. Sharding ingênuo com Hash Modular (hash % N) e o custo de rebalanceamento
2. Topologia em Anel de Hash Consistente e estabilidade sob expansão horizontal
3. Nós Virtuais para distribuição uniforme e mitigação de Hotspots
==============================================================================
"""

import hashlib
import bisect

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

# ==============================================================================
# 1. HASH COM MÓDULO: DEMONSTRAÇÃO DO CUSTO DE EXPANSÃO
# ==============================================================================
def demonstrar_hash_modulo():
    separador("1. Hash com Módulo: Custo de Mudar N de 3 para 4")
    chaves = [8, 9, 10, 11, 25, 33, 47, 52]
    
    print(f"{'Chave':<8} | {'hash mod 3':<12} | {'hash mod 4':<12} | {'Mudou de Shard?'}")
    print("-" * 55)
    mudaram = 0
    for k in chaves:
        s3 = k % 3
        s4 = k % 4
        mudou = s3 != s4
        if mudou:
            mudaram += 1
        print(f"{k:<8} | Shard {s3:<6} | Shard {s4:<6} | {'SIM (Migração forçada)' if mudou else 'Não'}")
        
    taxa = (mudaram / len(chaves)) * 100
    print("-" * 55)
    print(f"Percentual de chaves deslocadas: {taxa:.1f}%!")
    print("[CONCLUSÃO] No hash modular, adicionar 1 servidor força a movimentação de quase toda a base de dados.")

# ==============================================================================
# 2. TOPOLOGIA EM ANEL DE HASH CONSISTENTE
# ==============================================================================
class AnelDidatico:
    def __init__(self, tamanho_anel=100):
        self.tamanho_anel = tamanho_anel
        self.nos = [] # Lista de tuplas (posicao, nome)

    def adicionar_no(self, posicao, nome):
        self.nos.append((posicao, nome))
        self.nos.sort()

    def buscar_destino(self, chave_posicao):
        for ponto, nome in self.nos:
            if chave_posicao <= ponto:
                return nome, ponto
        # Se ultrapassou o último nó, dá a volta no anel (sentido horário) e encontra o primeiro
        return self.nos[0][1], self.nos[0][0]

def demonstrar_anel_didatico():
    separador("2. Anel de Hash Consistente: Topologia com Nós A=20, B=50, C=80")
    
    anel = AnelDidatico()
    anel.adicionar_no(20, "A")
    anel.adicionar_no(50, "B")
    anel.adicionar_no(80, "C")
    
    print("[TOPOLOGIA INICIAL]: Nós posicionados em A=20, B=50, C=80 (Anel de 0 a 99)")
    
    chaves_teste = [60, 70, 90]
    mapa_original = {}
    for c in chaves_teste:
        no, pos = anel.buscar_destino(c)
        mapa_original[c] = no
        print(f"  -> Chave {c:>2}: Sucessor no sentido horário é o Nó {no} (posição {pos})")
        
    print("\n---> [EVENTO DE ESCALA] Entra o Nó D na posição 65...")
    anel.adicionar_no(65, "D")
    
    print("[TOPOLOGIA PÓS-EXPANSÃO]: Nós A=20, B=50, D=65, C=80")
    for c in chaves_teste:
        no, pos = anel.buscar_destino(c)
        status = "REDIRECIONADA" if no != mapa_original[c] else "PERMANECEU INTOCADA"
        print(f"  -> Chave {c:>2}: Agora cai no Nó {no} (posição {pos}) -> Status: {status}")
        
    print("\n[EVIDÊNCIA]: Apenas a chave 60 migrou de C para D (intervalo (50, 65]).")
    print("             As chaves 70 (em C) e 90 (em A) permaneceram estáveis!")

# ==============================================================================
# 3. ANEL COM HASH MD5 E NÓS VIRTUAIS (MITIGAÇÃO DE HOTSPOTS)
# ==============================================================================
class AnelHashRobusto:
    def __init__(self, replicas_virtuais=50):
        self.replicas_virtuais = replicas_virtuais
        self.anel = {} # hash -> id_servidor_real
        self.pontos_ordenados = []

    def _hash(self, chave):
        return int(hashlib.md5(str(chave).encode('utf-8')).hexdigest(), 16)

    def adicionar_servidor(self, servidor):
        for i in range(self.replicas_virtuais):
            virtual_id = f"{servidor}#vnode{i}"
            h = self._hash(virtual_id)
            self.anel[h] = servidor
            self.pontos_ordenados.append(h)
        self.pontos_ordenados.sort()

    def get_servidor(self, chave):
        if not self.pontos_ordenados:
            return None
        h = self._hash(chave)
        idx = bisect.bisect_right(self.pontos_ordenados, h)
        if idx == len(self.pontos_ordenados):
            idx = 0
        return self.anel[self.pontos_ordenados[idx]]

def demonstrar_distribuicao_lojistas():
    separador("3. Mitigação de Hotspots via Nós Virtuais na Loja Horizonte")
    
    anel = AnelHashRobusto(replicas_virtuais=100)
    shards = ["Shard-1", "Shard-2", "Shard-3"]
    for s in shards:
        anel.adicionar_servidor(s)
        
    # Simulação de 10.000 pedidos com chave de particionamento lojista_id
    contagem = {s: 0 for s in shards}
    total_pedidos = 10000
    
    for i in range(total_pedidos):
        # Simula lojistas diversos (lojista_1 até lojista_500)
        lojista_id = f"lojista_{i % 500}"
        destino = anel.get_servidor(lojista_id)
        contagem[destino] += 1
        
    print(f"Distribuição de {total_pedidos} requisições entre {len(shards)} shards com 100 nós virtuais cada:")
    for shard, qtd in contagem.items():
        pct = (qtd / total_pedidos) * 100
        barra = "#" * int(pct // 2)
        print(f"  {shard}: {qtd:>5} reqs ({pct:5.2f}%) | {barra}")
        
    print("\n[EVIDÊNCIA]: O desvio é mínimo (~33% por nó), distribuindo a carga de forma homogênea sem gargalos.")

if __name__ == "__main__":
    print("=" * 75)
    print("  SUÍTE DE SIMULAÇÃO T2 - SHARDING E ANEL DE HASH CONSISTENTE")
    print("=" * 75)
    demonstrar_hash_modulo()
    demonstrar_anel_didatico()
    demonstrar_distribuicao_lojistas()
