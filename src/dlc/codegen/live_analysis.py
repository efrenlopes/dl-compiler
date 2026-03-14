from dlc.inter.basic_block import BasicBlock
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa import SSA
from dlc.inter.ssa_operand import TempVersion
from dlc.semantic.type import Type


class LivenessAnalysis:


    def __init__(self, ssa: SSA, types: tuple[Type]) -> None:
        self.ssa = ssa
        self.__types = types        
        # Variáveis usadas antes de serem definidas no bloco
        self.__use: dict[BasicBlock, set[TempVersion]] = {}
        # Variáveis definidas no bloco
        self.__def: dict[BasicBlock, set[TempVersion]] = {}
        # Todas as variáveis dos tipos em types
        self.vars: set[TempVersion] = set()
        # Variáveis que estão vivas na entrada de um bloco
        self.live_in: dict[BasicBlock, set[TempVersion]] = \
            {bb: set() for bb in ssa.ir.bb_sequence}
        # Variáveis que estão vivas na saída de um bloco
        self.live_out: dict[BasicBlock, set[TempVersion]] = \
            {bb: set() for bb in ssa.ir.bb_sequence}
        
        self.__compute_gen_kill()
        self.__compute_live_intervals()



    def __compute_gen_kill(self) -> None:
        for bb in self.ssa.ir.bb_sequence:
            self.__use[bb] = set()
            self.__def[bb] = set()
            
            for instr in bb:
                # Encontrando as variáveis
                for op in (instr.arg1, instr.arg2, instr.result):
                    if isinstance(op, TempVersion) and op.type in self.__types:
                        self.vars.add(op)

                # Encontrando os usos de variáveis
                for op in (instr.arg1, instr.arg2):
                    if isinstance(op, TempVersion) and \
                            op.type in self.__types and op not in self.__def[bb]:
                        self.__use[bb].add(op)
                
                # Encontrando as definições de variáveis
                if isinstance(instr.result, TempVersion) and \
                        instr.result.type in self.__types:
                    self.__def[bb].add(instr.result)



    def __compute_live_intervals(self) -> None:
        changed = True
        while changed:
            changed = False
            for bb in reversed(self.ssa.ir.bb_sequence):
                # O OUT agora inclui os usos das PHIs nos sucessores
                new_out: set[TempVersion] = set()
                for succ in bb.successors:
                    new_out |= self.live_in[succ]
                    
                    # Checar se o sucessor tem PHIs que usam valores vindos deste bloco
                    for instr in succ.phi_instrs:
                        assert( isinstance(instr, PhiInstr))
                        version = instr.paths.get(bb)
                        if version and isinstance(version, TempVersion) and \
                                version.type in self.__types:
                            new_out.add(version)
                
                if new_out != self.live_out[bb]:
                    self.live_out[bb] = new_out
                    changed = True
                
                # IN continua sendo: USE + (OUT - DEF)
                new_in = self.__use[bb] | (self.live_out[bb] - self.__def[bb])
                if new_in != self.live_in[bb]:
                    self.live_in[bb] = new_in
                    changed = True



    def print_liveness(self) -> None:
        print(f"{'Bloco':<10} | {'LIVE-IN':<25} | {'LIVE-OUT':<25}")
        print("-" * 70)
        for bb in self.ssa.ir.bb_sequence:
            in_str = ", ".join(str(v) for v in self.live_in[bb])
            out_str = ", ".join(str(v) for v in self.live_out[bb])
            print(f"{str(bb):<10} | {in_str:<25} | {out_str:<25}")
