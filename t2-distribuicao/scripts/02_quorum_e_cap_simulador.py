"""
==============================================================================
Simulador de Quorum e Teorema CAP - Trabalho 2 (T2)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações:
1. Análise aritmética de Quorum (R + W > N) e tolerância a falhas de réplicas
2. Partição de Rede e Teorema CAP: Comportamento CP vs AP em Cenários Críticos
==============================================================================
"""

import sys

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

# ==============================================================================
# 1. ANÁLISE COMPARATIVA DE QUORUM MAJORITÁRIO
# ==============================================================================
def demonstrar_quorum():
    separador("1. Comparação de Configurações de Quorum (N=3 Réplicas)")
    
    configuracoes = [
        {"W": 1, "R": 1, "desc": "Escrita e leitura fracas (Rápido, sem garantia forte)"},
        {"W": 2, "R": 2, "desc": "Quorum majoritário equilibrado (R+W > N)"},
        {"W": 3, "R": 1, "desc": "Escrita estrita em todas as réplicas, leitura em 1"}
    ]
    
    N = 3
    print(f"Cluster com N = {N} réplicas:")
    print(f"{'W':<4} | {'R':<4} | {'R+W > N?':<10} | {'Com 1 nó sem responder':<28} | {'Comportamento'}")
    print("-" * 75)
    
    for c in configuracoes:
        W, R = c["W"], c["R"]
        intersecao = (R + W) > N
        if W > (N - 1):
            impacto_falha = "ESCRITA FALHA (W=3 inacessível)"
        elif R > (N - 1):
            impacto_falha = "LEITURA FALHA (R=3 inacessível)"
        else:
            impacto_falha = "Limiar atingido (Opera normal)"
            
        print(f"{W:<4} | {R:<4} | {str(intersecao):<10} | {impacto_falha:<28} | {c['desc']}")
        
    print("-" * 75)
    print("[EVIDÊNCIA]: Apenas a configuração W=2, R=2 garante interseção (leitura enxerga a escrita)")
    print("             e ao mesmo tempo tolera a queda de 1 nó sem indisponibilizar a escrita.")

# ==============================================================================
# 2. SIMULAÇÃO DE PARTIÇÃO DE REDE: COMPORTAMENTO CP VS AP
# ==============================================================================
class ClusterCAP:
    def __init__(self):
        # Nós A e B
        self.no_A = {"x": 0, "ativo": True}
        self.no_B = {"x": 0, "ativo": True}
        self.rede_particionada = False

    def simular_particao(self):
        self.rede_particionada = True
        print("\n[ALERTA DE INFRAESTRUTURA] PARTIÇÃO DE REDE DETECTADA ENTRE NÓ A E NÓ B!")

    def reestabelecer_rede(self):
        self.rede_particionada = False
        print("\n[RECUPERAÇÃO] Rede restabelecida entre Nós A e B.")

    # Política CP: Prioriza Consistência (Linearizabilidade)
    def operacao_reserva_cp(self, cliente_id, novo_valor):
        print(f"\n[CENÁRIO CP - Checkout / Reserva de Estoque]")
        print(f"  -> Cliente 1 tenta escrever x={novo_valor} no Nó A...")
        self.no_A["x"] = novo_valor
        print(f"     Nó A registrou x={novo_valor}.")
        
        print("  -> Cliente 2 tenta ler x no Nó B...")
        if self.rede_particionada:
            print("     [DECISÃO CP]: Nó B detecta perda de comunicação com quorum/líder.")
            print("     [RESPOSTA]: 503 SERVICE UNAVAILABLE / BLOQUEADO.")
            print("     [MOTIVO]: B recusa retornar dado desatualizado (x=0) para evitar venda acima do estoque!")
            return None
        else:
            self.no_B["x"] = self.no_A["x"]
            print(f"     Nó B responde com linearizabilidade: x={self.no_B['x']}")
            return self.no_B["x"]

    # Política AP: Prioriza Disponibilidade
    def operacao_catalogo_ap(self, cliente_id, nova_descricao):
        print(f"\n[CENÁRIO AP - Catálogo / Descrição de Produto]")
        print(f"  -> Lojista atualiza descrição no Nó A: '{nova_descricao}'...")
        self.no_A["descricao"] = nova_descricao
        
        print("  -> Consumidor consulta produto no Nó B...")
        if self.rede_particionada:
            print("     [DECISÃO AP]: Nó B não consegue sincronizar com Nó A.")
            print(f"     [RESPOSTA]: 200 OK (com versão local legada: '{self.no_B.get('descricao', 'Descricao Antiga')}')")
            print("     [MOTIVO]: Para catálogo, responder dado temporariamente desatualizado é aceitável!")
            return self.no_B.get("descricao", "Descricao Antiga")
        else:
            self.no_B["descricao"] = self.no_A["descricao"]
            print(f"     Nó B sincronizado responde: '{self.no_B['descricao']}'")
            return self.no_B["descricao"]

def demonstrar_teorema_cap():
    separador("2. Teorema CAP na Prática: Decisão CP vs AP na Loja Horizonte")
    cluster = ClusterCAP()
    
    # Operação sob rede saudável
    print("[FASE 1: Rede Operando Normalmente]")
    cluster.operacao_reserva_cp(1, 1)
    
    # Corte de rede
    cluster.simular_particao()
    
    # Teste de reserva (CP) sob partição
    cluster.operacao_reserva_cp(1, 2)
    
    # Teste de catálogo (AP) sob partição
    cluster.operacao_catalogo_ap(1, "Mochila Impermeável 2026 Edition")
    
    # Volta da rede
    cluster.reestabelecer_rede()

if __name__ == "__main__":
    print("=" * 75)
    print("  SUÍTE DE SIMULAÇÃO T2 - QUORUM E TEOREMA CAP")
    print("=" * 75)
    demonstrar_quorum()
    demonstrar_teorema_cap()
