from dlc.inter.ssa import SSA
from dlc.inter.operator import Operator
from dlc.semantic.type import Type


class LivenessAnalysis:


    def __init__(self, ssa: SSA, types: tuple[Type]):
        self.ssa = ssa
        self.types = types
        # Conjuntos por Bloco Básico
        self.vars = set() # Todas as variáveis dos tipos em types
        self.use = {}  # Variáveis usadas antes de serem definidas no bloco
        self.def_ = {} # Variáveis definidas no bloco
        self.live_in = {bb: set() for bb in ssa.ir.bb_sequence}
        self.live_out = {bb: set() for bb in ssa.ir.bb_sequence}
        
        self._compute_gen_kill()
        self._compute_live_intervals()



    def _compute_gen_kill(self):
        for bb in self.ssa.ir.bb_sequence:
            self.use[bb] = set()
            self.def_[bb] = set()
            
            for instr in bb:

                for op in (instr.arg1, instr.arg2, instr.result):
                    if op.is_temp_version and op.type in self.types:
                        self.vars.add(op)

                # Lógica normal para outras instruções
                for op in (instr.arg1, instr.arg2):
                    if op.is_temp_version and op.type in self.types and op not in self.def_[bb]:
                        self.use[bb].add(op)
                
                if instr.result.is_temp_version and instr.result.type in self.types:
                    self.def_[bb].add(instr.result)



    def _compute_live_intervals(self):
        changed = True
        while changed:
            changed = False
            for bb in reversed(self.ssa.ir.bb_sequence):
                # NOVIDADE: O OUT agora inclui os usos das PHIs nos sucessores
                new_out = set()
                for succ in bb.successors:
                    new_out |= self.live_in[succ]
                    
                    # Checar se o sucessor tem PHIs que usam valores vindos deste bloco (bb)
                    for instr in succ.phi_instrs:
                        version = instr.arg1.paths.get(bb)
                        if version and version.is_temp_version and version.type in self.types:
                            new_out.add(version) # O valor deve estar vivo na saída de bb
                
                if new_out != self.live_out[bb]:
                    self.live_out[bb] = new_out
                    changed = True
                
                # IN continua sendo: USE + (OUT - DEF)
                new_in = self.use[bb] | (self.live_out[bb] - self.def_[bb])
                if new_in != self.live_in[bb]:
                    self.live_in[bb] = new_in
                    changed = True



    def print_liveness(self):
        print(f"{'Bloco':<10} | {'LIVE-IN':<25} | {'LIVE-OUT':<25}")
        print("-" * 70)
        for bb in self.ssa.ir.bb_sequence:
            in_str = ", ".join(str(v) for v in self.live_in[bb])
            out_str = ", ".join(str(v) for v in self.live_out[bb])
            print(f"{str(bb):<10} | {in_str:<25} | {out_str:<25}")





# from typing import Dict, Set
# from dataclasses import dataclass

# from dlc.inter_ssa.ssa_operand import SSATempVersion
# from dlc.inter_ssa.ssa_operator import SSAOperator


# @dataclass
# class LiveInterval:
#     start: int
#     end: int
#     temp: SSATempVersion
    
#     def __repr__(self):
#         return f"LiveInterval(start={self.start}, end={self.end}, temp={self.temp})"




# class LivenessAnalyzer:


#     @staticmethod
#     def compute_live_ranges(ssa) -> Dict[str, LiveInterval]:

#         # ---------------------------------------------------------
#         # 1. Linearização e Mapeamento de índices
#         # ---------------------------------------------------------
#         all_instructions = []
#         bb_start_end = {}

#         current_idx = 0
#         for bb in ssa.ic.bb_sequence:
#             start_bb = current_idx
#             for instr in bb.instructions:
#                 all_instructions.append(instr)
#                 current_idx += 1
#             bb_start_end[bb] = (start_bb, current_idx - 1)

#         # ---------------------------------------------------------
#         # 2. Data-flow Analysis (Live-In e Live-Out)
#         # ---------------------------------------------------------
#         live_in = {bb: set() for bb in ssa.ic.bb_sequence}
#         live_out = {bb: set() for bb in ssa.ic.bb_sequence}

#         changed = True
#         while changed:
#             changed = False

#             for bb in reversed(ssa.ic.bb_sequence):

#                 # ---- live_out[bb]
#                 new_live_out = set()

#                 for succ in bb.successors:

#                     # PHI uses (uso ocorre na aresta bb -> succ)
#                     for instr in succ.instructions:
#                         if instr.op == SSAOperator.PHI:
#                             phi_obj = instr.arg1
#                             if bb in phi_obj.paths:
#                                 val = phi_obj.paths[bb]
#                                 if isinstance(val, SSATempVersion):
#                                     new_live_out.add(val)

#                     # variáveis vivas na entrada do sucessor,
#                     # exceto as definidas por PHI nele
#                     for var in live_in[succ]:
#                         defined_by_phi = any(
#                             i.op == SSAOperator.PHI and i.result == var
#                             for i in succ.instructions
#                         )
#                         if not defined_by_phi:
#                             new_live_out.add(var)

#                 if new_live_out != live_out[bb]:
#                     live_out[bb] = new_live_out
#                     changed = True

#                 # ---- live_in[bb]
#                 new_live_in = set(live_out[bb])

#                 for instr in reversed(bb.instructions):

#                     # definição mata
#                     if isinstance(instr.result, SSATempVersion):
#                         new_live_in.discard(instr.result)

#                     # usos normais (PHI ignorado aqui)
#                     if instr.op != SSAOperator.PHI:
#                         for op in (instr.arg1, instr.arg2):
#                             if isinstance(op, SSATempVersion):
#                                 new_live_in.add(op)

#                 if new_live_in != live_in[bb]:
#                     live_in[bb] = new_live_in
#                     changed = True

#         # ---------------------------------------------------------
#         # 3. Construção CORRETA dos intervalos
#         #    (backward com conjunto live real)
#         # ---------------------------------------------------------
#         intervals: Dict[SSATempVersion, LiveInterval] = {}

#         # 3.1 Inicializa intervalos no ponto de definição
#         for idx, instr in enumerate(all_instructions):
#             if isinstance(instr.result, SSATempVersion):
#                 intervals[instr.result] = LiveInterval(idx, idx, instr.result)

#         # 3.2 Estende intervalos usando vivacidade real
#         for bb in ssa.ic.bb_sequence:

#             start_idx, end_idx = bb_start_end[bb]

#             # começa com o conjunto real de live_out
#             live = set(live_out[bb])

#             # tudo que está vivo na saída precisa alcançar o fim do bloco
#             for v in live:
#                 if v in intervals:
#                     intervals[v].end = max(intervals[v].end, end_idx)

#             # percorre o bloco de trás para frente
#             for idx in reversed(range(start_idx, end_idx + 1)):

#                 instr = all_instructions[idx]

#                 # definição
#                 if isinstance(instr.result, SSATempVersion):
#                     v = instr.result

#                     # se estava vivo aqui, intervalo começa antes
#                     if v in live:
#                         intervals[v].start = min(intervals[v].start, idx)

#                     # definição mata
#                     live.discard(v)

#                 # usos normais (PHI já tratado nas arestas)
#                 if instr.op != SSAOperator.PHI:
#                     for op in (instr.arg1, instr.arg2):
#                         if isinstance(op, SSATempVersion):
#                             live.add(op)

#                             if op in intervals:
#                                 intervals[op].start = min(intervals[op].start, idx)
#                                 intervals[op].end = max(intervals[op].end, idx)

#         return intervals