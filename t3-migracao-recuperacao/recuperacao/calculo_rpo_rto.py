"""
==============================================================================
Calculador e Simulador de Métricas RPO e RTO - Trabalho 3 (T3)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações práticas:
1. Cálculo formal de RPO e RTO diante de um incidente operacional real
2. Comparativo de estratégias de Disaster Recovery (Indústria e Nuvem)
3. Matriz de coerência em recuperação com múltiplos bancos desacoplados
==============================================================================
"""

from datetime import datetime

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

def calcular_metricas_exercicio():
    separador("1. Apuração de SLA: Cálculo de RPO e RTO no Incidente da Loja Horizonte")
    
    # Horários operacionais registrados no incidente
    t_falha = datetime.strptime("10:00:00", "%H:%M:%S")
    t_ponto_recuperavel = datetime.strptime("09:55:00", "%H:%M:%S")
    t_servico_validado = datetime.strptime("10:40:00", "%H:%M:%S")
    
    # Metas de negócio estabelecidas pelo SLA
    meta_rpo_minutos = 5
    meta_rto_minutos = 30
    
    # Cálculos
    rpo_real_minutos = int((t_falha - t_ponto_recuperavel).total_seconds() / 60)
    rto_real_minutos = int((t_servico_validado - t_falha).total_seconds() / 60)
    
    print(f"{'Métrica':<6} | {'Definição de Negócio':<35} | {'Meta SLA':<12} | {'Obtido':<12} | {'Status SLA'}")
    print("-" * 75)
    
    status_rpo = "ATENDIDO (<= 5m)" if rpo_real_minutos <= meta_rpo_minutos else "VIOLADO"
    status_rto = "ATENDIDO (<= 30m)" if rto_real_minutos <= meta_rto_minutos else "VIOLADO (> 30m)"
    
    print(f"RPO    | Quanto dado é aceitável perder      | Até {meta_rpo_minutos} min    | {rpo_real_minutos} minutos  | {status_rpo}")
    print(f"RTO    | Tempo para restaurar o serviço      | Até {meta_rto_minutos} min   | {rto_real_minutos} minutos  | {status_rto}")
    print("-" * 75)
    print("[ANÁLISE DE ENGENHARIA]: O RPO foi cumprido graças ao arquivamento de WAL frequente,")
    print("                         mas o RTO estourou em 10 minutos devido à demora na validação manual.")

def comparar_estrategias_dr():
    separador("2. Comparativo de Estratégias de Disaster Recovery")
    
    estrategias = [
        {"nome": "Backup / Restore", "rpo": "Horas", "rto": "Horas", "custo": "Baixo", "foco": "Reconstrução total da infra e banco"},
        {"nome": "Pilot Light", "rpo": "Minutos", "rto": "Dezenas de min", "custo": "Médio-baixo", "foco": "Dados replicados, nós de app desligados"},
        {"nome": "Warm Standby", "rpo": "Segundos/Min", "rto": "Minutos", "custo": "Médio-alto", "foco": "Ambiente reduzido já em execução"},
        {"nome": "Multi-Região Ativo-Ativo", "rpo": "~Zero", "rto": "~Zero", "custo": "Muito Alto", "foco": "Atende em múltiplos locais simultâneos"}
    ]
    
    print(f"{'Estratégia':<24} | {'RPO Típico':<14} | {'RTO Típico':<16} | {'Custo':<12} | {'Complexidade'}")
    print("-" * 75)
    for e in estrategias:
        print(f"{e['nome']:<24} | {e['rpo']:<14} | {e['rto']:<16} | {e['custo']:<12} | {e['foco']}")
    print("-" * 75)

def matriz_recuperacao_multibanco():
    separador("3. Recuperação de Coerência com Múltiplos Bancos")
    print("Problema: Backups feitos no mesmo horário NÃO garantem estado global consistente!")
    print("Exemplo: O banco de pedidos foi restaurado como PAGO, mas o banco de pagamentos parou antes da cobrança.")
    print("\nChecklist arquitetural exigido pós-DR:")
    print("  [x] Conciliação de IDs entre pedidos relacionais e transações externas.")
    print("  [x] Retomada de Sagas que ficaram em estado 'PENDENTE' sem duplicar efeitos.")
    print("  [x] Validação de invariantes de negócio antes de abrir o tráfego aos clientes.")

if __name__ == "__main__":
    calcular_metricas_exercicio()
    comparar_estrategias_dr()
    matriz_recuperacao_multibanco()
