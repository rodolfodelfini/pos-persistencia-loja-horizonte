"""
==============================================================================
Simulador de PITR (Point-in-Time Recovery) e Arquivamento de WAL - Trabalho 3 (T3)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações:
1. Réplica vs Backup: Por que replicação não protege contra comandos DELETE acidentais
2. Restauração com Base Backup + Reaplicação contínua de WAL
3. Parada no instante exato: Alvo configurado = 10:06:59 (1 segundo antes do incidente das 10:07:00)
==============================================================================
"""

from datetime import datetime, timedelta

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

class SimuladorPITR:
    def __init__(self):
        # Base física restaurável gerada no snapshot das 10:00
        self.base_backup_10h00 = [
            {"id": 701, "cliente": 42, "valor": 289.90, "timestamp": "10:00:00"}
        ]
        
        # Histórico de transações registradas no Write-Ahead Log (WAL)
        self.wal_stream = [
            {"lsn": 101, "timestamp": "10:03:00", "op": "INSERT", "pedido_id": 801, "cliente": 18, "valor": 99.00},
            {"lsn": 102, "timestamp": "10:05:00", "op": "INSERT", "pedido_id": 802, "cliente": 99, "valor": 150.00},
            {"lsn": 103, "timestamp": "10:07:00", "op": "DELETE_ALL", "detalhe": "DROP/DELETE INDEVIDO DE PEDIDOS!"}
        ]

    def demonstrar_falha_da_replica(self):
        separador("1. Por que Réplicas não protegem contra erros operacionais humanos")
        print("Cenário: Às 10:07:00 um operador envia acidentalmente 'DELETE FROM pedido;'")
        print("Líder executa o DELETE...")
        print("-> A réplica síncrona/assíncrona recebe o comando e replica a exclusão com PERFEIÇÃO!")
        print("-> Resultado na Réplica: Todos os pedidos foram apagados!")
        print("[CONCLUSÃO]: Réplica é para alta disponibilidade de hardware; BACKUP + PITR é para recuperação de dados.")

    def executar_restauracao_pitr(self, alvo_recovery="10:06:59"):
        separador(f"2. Execução de PITR: Recuperação Ponto no Tempo até o alvo {alvo_recovery}")
        
        print("[ETAPA 1: Restaurar a Base Backup Física das 10:00:00]")
        tabela_recuperada = list(self.base_backup_10h00)
        print(f"  -> Base restaurada em ambiente isolado. Pedidos restaurados: {len(tabela_recuperada)}")
        
        print(f"\n[ETAPA 2: Reaplicar Sequência de WALs arquivados até o target '{alvo_recovery}']")
        for log in self.wal_stream:
            ts = log["timestamp"]
            if ts <= alvo_recovery:
                tabela_recuperada.append({
                    "id": log["pedido_id"],
                    "cliente": log["cliente"],
                    "valor": log["valor"],
                    "timestamp": ts
                })
                print(f"  -> [WAL LSN {log['lsn']} @ {ts}] Reaplicando INSERT Pedido #{log['pedido_id']} (Valor R${log['valor']})")
            else:
                print(f"  -> [WAL LSN {log['lsn']} @ {ts}] ALVO ULTRAPASSADO ({ts} > {alvo_recovery}).")
                print(f"     INTERRUPÇÃO PROPOSITADA! Operação '{log['op']}' ignorada com sucesso.")
                break
                
        print(f"\n[ETAPA 3: Validar e Devolver o Serviço]")
        print("Tabela 'pedido' recuperada com sucesso pós-PITR:")
        for p in tabela_recuperada:
            print(f"  Pedido #{p['id']}: Cliente {p['cliente']} | R$ {p['valor']} (Criado às {p['timestamp']})")
            
        print("\n[EVIDÊNCIA DE INTEGRIDADE]:")
        print(f"  Total de pedidos resgatados: {len(tabela_recuperada)}.")
        print("  Os pedidos legítimos das 10:03 e 10:05 foram preservados intactos!")
        print("  A exclusão catastrófica das 10:07:00 foi completamente evitada.")

if __name__ == "__main__":
    pitr = SimuladorPITR()
    pitr.demonstrar_falha_da_replica()
    pitr.executar_restauracao_pitr("10:06:59")
