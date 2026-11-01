"""
==============================================================================
Orquestrador de Padrão Saga com Compensação e Idempotência - Trabalho 3 (T3)
Disciplina: Persistência de Dados e Bancos Distribuídos
Caso de Estudo: Loja Horizonte

Demonstrações práticas:
1. Cenário Feliz: Pedido Pendente -> Reserva Estoque -> Cobrança -> Confirmação
2. Cenário de Falha Definitiva: Falha de Pagamento -> Compensação Atômica de Estoque
3. Cenário Crítico de Timeout / Indeterminação: Tratamento com Chave de Idempotência
   (Evita cobrança duplicada e impede compensação às cegas)
==============================================================================
"""

import uuid
import time
import enum

def separador(titulo):
    print("\n" + "=" * 75)
    print(f"  {titulo.upper()}")
    print("=" * 75)

class EstadoSaga(enum.Enum):
    INICIADO = "INICIADO"
    ESTOQUE_RESERVADO = "ESTOQUE_RESERVADO"
    PAGAMENTO_CONFIRMADO = "PAGAMENTO_CONFIRMADO"
    PEDIDO_CONCLUIDO = "PEDIDO_CONCLUIDO"
    COMPENSANDO_ESTOQUE = "COMPENSANDO_ESTOQUE"
    PEDIDO_CANCELADO = "PEDIDO_CANCELADO"
    AGUARDANDO_RECONCILIACAO = "AGUARDANDO_RECONCILIACAO"

class OrquestradorSagaHorizonte:
    def __init__(self):
        # Simulação de microserviços desacoplados
        self.estoque_servico = {"10": {"disponivel": 5, "reservado": 0}}
        self.pedidos_db = {}
        self.gateway_pagamentos = {} # chave_idempotencia -> status
        self.compensacoes_executadas = set() # Idempotência de compensação

    def criar_pedido(self, pedido_id, cliente_id, produto_id, valor):
        idempotency_key = f"PAY-REQ-{pedido_id}-{uuid.uuid4().hex[:8]}"
        self.pedidos_db[pedido_id] = {
            "estado": EstadoSaga.INICIADO,
            "produto_id": produto_id,
            "valor": valor,
            "idempotency_key": idempotency_key
        }
        print(f"\n[SAGA #{pedido_id}] Criado: Pedido={pedido_id}, Cliente={cliente_id}, ChaveIdempotência={idempotency_key}")
        return idempotency_key

    # Etapa 1: Reserva Local de Estoque
    def etapa_reservar_estoque(self, pedido_id):
        pedido = self.pedidos_db[pedido_id]
        prod_id = pedido["produto_id"]
        estoque = self.estoque_servico[prod_id]
        
        if estoque["disponivel"] >= 1:
            estoque["disponivel"] -= 1
            estoque["reservado"] += 1
            pedido["estado"] = EstadoSaga.ESTOQUE_RESERVADO
            print(f"  -> [PASSO 1 - SUCESSO] Estoque reservado localmente (Disp: {estoque['disponivel']}, Res: {estoque['reservado']})")
            return True
        else:
            pedido["estado"] = EstadoSaga.PEDIDO_CANCELADO
            print("  -> [PASSO 1 - FALHA] Saldo insuficiente. Saga abortada.")
            return False

    # Ação Compensatória: Liberação de Reserva de Estoque
    def compensar_reserva_estoque(self, pedido_id):
        # Proteção contra compensação duplicada (Idempotência)
        if pedido_id in self.compensacoes_executadas:
            print(f"  -> [COMPENSAÇÃO] Ação já executada para pedido #{pedido_id}. Ignorando duplicação.")
            return
            
        pedido = self.pedidos_db[pedido_id]
        prod_id = pedido["produto_id"]
        estoque = self.estoque_servico[prod_id]
        
        estoque["disponivel"] += 1
        estoque["reservado"] -= 1
        self.compensacoes_executadas.add(pedido_id)
        pedido["estado"] = EstadoSaga.PEDIDO_CANCELADO
        print(f"  -> [AÇÃO COMPENSATÓRIA EXECUTADA]: Estoque liberado! (Disp: {estoque['disponivel']}, Res: {estoque['reservado']})")

    # Etapa 2: Cobrança Externa e Tratamento dos 3 Resultados da Transação
    def etapa_cobrar_e_decidir(self, pedido_id, cenario_simulado="SUCESSO"):
        pedido = self.pedidos_db[pedido_id]
        chave = pedido["idempotency_key"]
        
        print(f"  -> [PASSO 2] Enviando cobrança ao gateway externo (Chave: {chave})...")
        
        # Mapeamento dos retornos do gateway financeiro
        if cenario_simulado == "SUCESSO":
            resultado_pagamento = "CONFIRMADO"
        elif cenario_simulado == "CARTAO_RECUSADO":
            resultado_pagamento = "FALHA_DEFINITIVA"
        else:
            resultado_pagamento = "DESCONHECIDO" # Timeout de rede
            
        print(f"     Resultado retornado da API: [{resultado_pagamento}]")
        
        # Implementação em Python do fluxo de decisão da Saga
        match resultado_pagamento:
            case "CONFIRMADO":
                pedido["estado"] = EstadoSaga.PEDIDO_CONCLUIDO
                print(f"  -> [PASSO 3 - CONCLUSÃO] Pedido #{pedido_id} CONFIRMADO com sucesso!")
                
            case "FALHA_DEFINITIVA":
                print(f"  -> [FALHA DEFINITIVA] Cartão sem limite. Iniciando compensação...")
                pedido["estado"] = EstadoSaga.COMPENSANDO_ESTOQUE
                self.compensar_reserva_estoque(pedido_id)
                
            case "DESCONHECIDO":
                print(f"  -> [TIMEOUT / INDETERMINAÇÃO DETECTADA]:")
                print(f"     1. NÃO gerar nova cobrança (evita cobrança em dobro)!")
                print(f"     2. NÃO compensar às cegas (o dinheiro pode ter sido debitado)!")
                print(f"     3. Mantendo pedido em AGUARDANDO_RECONCILIACAO...")
                pedido["estado"] = EstadoSaga.AGUARDANDO_RECONCILIACAO
                
                # Resolução assíncrona por reconciliação
                self._reconciliar_com_mesma_chave(pedido_id, chave)

    def _reconciliar_com_mesma_chave(self, pedido_id, chave):
        print(f"  -> [RECONCILIAÇÃO AUTOMÁTICA]: Consultando gateway com a mesma chave estável ({chave})...")
        # Supondo que a consulta detectou que a cobrança havia passado no gateway antes do timeout
        status_real = "CONFIRMADO"
        print(f"     Resultado obtido da consulta: [{status_real}].")
        self.pedidos_db[pedido_id]["estado"] = EstadoSaga.PEDIDO_CONCLUIDO
        print(f"  -> [RECUPERAÇÃO CONCLUÍDA]: Pedido #{pedido_id} finalizado sem perda de consistência.")

def executar_demonstracao_sagas():
    separador("DEMONSTRAÇÃO PRÁTICA DO PADRÃO SAGA - LOJA HORIZONTE")
    orquestrador = OrquestradorSagaHorizonte()
    
    # 1. Fluxo Feliz
    print("\n[CENÁRIO 1: Fluxo de Sucesso Integral]")
    k1 = orquestrador.criar_pedido(701, cliente_id=42, produto_id="10", valor=289.90)
    if orquestrador.etapa_reservar_estoque(701):
        orquestrador.etapa_cobrar_e_decidir(701, cenario_simulado="SUCESSO")
        
    # 2. Fluxo com Falha Definitiva e Compensação
    print("\n[CENÁRIO 2: Pagamento Recusado e Compensação de Estoque]")
    k2 = orquestrador.criar_pedido(702, cliente_id=18, produto_id="10", valor=149.00)
    if orquestrador.etapa_reservar_estoque(702):
        orquestrador.etapa_cobrar_e_decidir(702, cenario_simulado="CARTAO_RECUSADO")
        
    # 3. Fluxo de Timeout / Indeterminação
    print("\n[CENÁRIO 3: Timeout de Rede e Resolução Idempotente com Mesma Chave]")
    k3 = orquestrador.criar_pedido(703, cliente_id=99, produto_id="10", valor=550.00)
    if orquestrador.etapa_reservar_estoque(703):
        orquestrador.etapa_cobrar_e_decidir(703, cenario_simulado="TIMEOUT")

if __name__ == "__main__":
    executar_demonstracao_sagas()
