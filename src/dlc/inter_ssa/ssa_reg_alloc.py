from typing import Dict, List

from dlc.inter_ssa.ssa_live_analysis import LiveInterval

class SSALinearScanRegisterAllocator:
    def __init__(self, intervals: Dict[str, LiveInterval], registers: List[str]):
        # 1. Ordena os intervalos pelo tempo de início (start)
        self.intervals = sorted(intervals.values(), key=lambda x: x.start)
        
        # 2. Registradores disponíveis (nomes literais)
        self.free_regs = list(registers) 
        
        # 3. Estruturas de controle
        self.active: List[LiveInterval] = []
        self.allocations: Dict[str, str] = {} # var_name -> nome_do_reg
        self.spills = {}         # variáveis que vão para a memória (pilha)
        self.spill_count = 0
        self._allocate()

    def _allocate(self):
        for i in self.intervals:
            # Passo A: Limpar registradores de variáveis que já morreram
            self._expire_old_intervals(i)

            # Passo B: Verificar se há registradores físicos livres
            if not self.free_regs:
                # Se não há nomes de registradores sobrando, decide quem sofre Spill
                self._spill_at_interval(i)
            else:
                # Aloca o primeiro registrador disponível da lista
                reg = self.free_regs.pop(0)
                self.allocations[i.temp] = reg
                self.active.append(i)
                # Mantém active ordenado pelo 'end' para facilitar o expire_old
                self.active.sort(key=lambda x: x.end)

        return self.allocations, self.spills

    def _expire_old_intervals(self, current_interval):
        # Remove da lista 'active' todos que terminam antes do início do atual
        # Note que se end == current.start, eles ainda interferem (dependendo da sua semântica)
        # Usamos < aqui para garantir que se uma instr usa e outra define, o reg seja liberado
        while self.active and self.active[0].end < current_interval.start:
            old = self.active.pop(0)
            reg = self.allocations.get(old.temp)
            if reg:
                # Devolve o nome do registrador para a lista de livres
                self.free_regs.append(reg)
        
        # Garante que a lista de livres esteja sempre em ordem (opcional, para estética)
        self.free_regs.sort()

    def _spill_at_interval(self, i):
        if not self.active:
            self.spill_count += 1
            self.spills[i.temp] = self.spill_count
            return
        # Candidato ao Spill: quem em 'active' termina mais longe no futuro?
        # O último elemento de 'active' tem o maior 'end' devido ao sort no allocate()
        spill_candidate = self.active[-1]

        if spill_candidate.end > i.end:
            # O candidato atual vive mais tempo que o novo intervalo 'i'.
            # Roubamos o registrador do candidato e damos para 'i'.
            reg = self.allocations[spill_candidate.temp]
            self.allocations[i.temp] = reg
            
            # Remove a alocação do candidato e joga para a pilha
            del self.allocations[spill_candidate.temp]
            self.spill_count += 1
            self.spills[spill_candidate.temp] = self.spill_count
            
            self.active.pop() # Remove o candidato de active
            self.active.append(i)
            self.active.sort(key=lambda x: x.end)
        else:
            # O próprio intervalo novo 'i' termina mais longe que todos em active,
            # então ele mesmo vai direto para o Spill.
            self.spill_count += 1
            self.spills[i.temp] = self.spill_count
