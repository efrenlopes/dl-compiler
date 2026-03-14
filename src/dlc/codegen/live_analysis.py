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
                        version = instr.paths.get(bb)
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
