"""
==============================================================================
Simulador de Garantias de Sessão e Atraso de Replicação - Trabalho 2 (T2)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações:
1. Replicação Assíncrona e Atraso de Propagação (Replication Lag)
2. Violação de Monotonic Reads: O cliente observa regressão temporal em recarregamento
3. Violação de Read-Your-Writes: O cliente grava e lê dado defasado de réplica
4. Implementação da Solução de Engenharia: Roteamento baseado em Versão Mínima
==============================================================================
"""

import time

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

class ClusterReplicado:
    def __init__(self):
        # Líder e duas réplicas de leitura com lag
        self.lider = {"versao": 8, "dados": {"endereco": "Av. Paulista, 1000", "status_pedido": "PAGO"}}
        self.replica_B = {"versao": 7, "dados": {"endereco": "Rua Augusta, 500", "status_pedido": "EM_PROCESSAMENTO"}}
        self.replica_C = {"versao": 6, "dados": {"endereco": "Rua da Consolação, 200", "status_pedido": "CRIADO"}}

    # Balanceador ingênuo round-robin entre réplicas
    def leitura_round_robin(self, requisicoes=3):
        replicas = [("Réplica B", self.replica_B), ("Réplica C", self.replica_C)]
        versoes_observadas = []
        
        print("[BALANCEAMENTO ROUND-ROBIN INGÊNUO SEM GARANTIA DE SESSÃO]:")
        for i in range(requisicoes):
            nome_replica, rep = replicas[i % len(replicas)]
            v = rep["versao"]
            versoes_observadas.append(v)
            print(f"  Leitura {i+1} direcionada para {nome_replica} -> Retornou Versão: {v}")
            
        return versoes_observadas

    # Roteamento inteligente com garantia de Monotonic Reads e Read-Your-Writes
    def leitura_com_garantia_sessao(self, versao_minima_conhecida):
        print(f"\n[ROTEADOR COM GARANTIA DE SESSÃO (Versão Mínima Exigida: v{versao_minima_conhecida})]:")
        candidatos = [("Réplica B", self.replica_B), ("Réplica C", self.replica_C), ("Líder", self.lider)]
        
        for nome, no in candidatos:
            if no["versao"] >= versao_minima_conhecida:
                print(f"  -> Roteado com sucesso para {nome} (Versão {no['versao']} >= v{versao_minima_conhecida})")
                print(f"  -> Dados retornados: {no['dados']}")
                return no["versao"], no["dados"]
            else:
                print(f"  -> {nome} descartado: possui versão {no['versao']} (Lag detectado, violaria consistência de sessão)")
        return None

def demonstrar_monotonic_reads():
    separador("1. Violação de Monotonic Reads: O Tempo Voltando sob Round-Robin")
    cluster = ClusterReplicado()
    
    print("Cenário: Réplica B já aplicou v7; Réplica C ainda está atrasada na v6.")
    versoes = cluster.leitura_round_robin(requisicoes=3)
    
    print("\nLinha do tempo observada pelo usuário:")
    print(f"  Leitura 1: v{versoes[0]} (Avanço)")
    print(f"  Leitura 2: v{versoes[1]} (REGRESSÃO! Violou Monotonic Reads)")
    print(f"  Leitura 3: v{versoes[2]} (Avanço)")
    print("[EVIDÊNCIA]: O usuário viu a versão 7, recarregou a página e viu a versão 6 anterior!")

def demonstrar_read_your_writes():
    separador("2. Violação de Read-Your-Writes: O Caso do Endereço Atualizado")
    cluster = ClusterReplicado()
    
    print("Passo 1: Cliente 42 altera endereço para 'Av. Paulista, 1000' (Gravado no Líder como v8)")
    print("Passo 2: O líder confirma 'SUCESSO 200 OK' ao cliente.")
    print("Passo 3: A aplicação redireciona o cliente para a tela de confirmação e lê da Réplica B...")
    
    dado_lido = cluster.replica_B["dados"]["endereco"]
    versao_lida = cluster.replica_B["versao"]
    print(f"  -> Resultado retornado da Réplica B: '{dado_lido}' (Versão {versao_lida})")
    print("[VIOLAÇÃO DETECTADA]: O cliente acabou de atualizar o endereço, mas continua vendo o endereço antigo na tela seguinte!")

def demonstrar_solucao_garantia():
    separador("3. Solução de Arquitetura: Token de Sessão / Versão Mínima")
    cluster = ClusterReplicado()
    
    # O cliente acabou de gravar a versão 8 e recebe um token de progresso da sessão
    token_sessao_versao = 8
    print(f"O cliente carrega o token de sessão com versao_observada = {token_sessao_versao}")
    
    cluster.leitura_com_garantia_sessao(versao_minima_conhecida=token_sessao_versao)
    print("\n[CONCLUSÃO]: Com a garantia de sessão, o sistema rejeita réplicas com lag e direciona a leitura para o Líder ou aguarda sincronização, assegurando Monotonic Reads e Read-Your-Writes.")

if __name__ == "__main__":
    print("=" * 75)
    print("  SUÍTE DE SIMULAÇÃO T2 - GARANTIAS DE SESSÃO E REPLICAÇÃO")
    print("=" * 75)
    demonstrar_monotonic_reads()
    demonstrar_read_your_writes()
    demonstrar_solucao_garantia()
