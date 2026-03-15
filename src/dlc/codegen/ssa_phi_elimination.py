from dlc.inter.basic_block import BasicBlock
from dlc.inter.instr import Instr
from dlc.inter.operand import Operand, Temp
from dlc.inter.operator import Operator
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa import SSA
from dlc.inter.ssa_operand import TempVersion


class SSAPhiEliminator:

    def __init__(self, ssa: SSA) -> None:
        self.ssa = ssa
        self.__eliminate_phi()
        

    def __eliminate_phi(self) -> None:
        for bb in self.ssa.ir.bb_sequence:

            if not bb.phi_instrs:
                continue

            copies_by_pred: dict[BasicBlock, list[tuple[TempVersion, TempVersion]]] = {}

            # coletar cópias
            for phi in bb.phi_instrs:
                assert(isinstance(phi, PhiInstr))
                dest = phi.result

                for pred, src in phi.paths.items():
                    if src == dest:
                        continue
                    assert(isinstance(dest, TempVersion) and isinstance(src, TempVersion))
                    copies_by_pred.setdefault(pred, []).append((dest, src))

            # resolver cópias em cada predecessor
            for pred, copies in copies_by_pred.items():
                scheduled = self.__schedule_parallel_copies(copies)
                for dest, src in scheduled:
                    move = Instr(Operator.MOVE, src, Operand.EMPTY, dest)
                    pred.body_instrs.append(move) #insert(-1, move)

            bb.phi_instrs.clear()

    def __schedule_parallel_copies(self, 
            copies: list[tuple[TempVersion, TempVersion]]) -> \
                list[tuple[TempVersion, TempVersion]]:
        copies = copies[:]
        result: list[tuple[TempVersion, TempVersion]] = []

        while copies:
            progress = False

            for dest, src in copies:
                if dest not in [s for _, s in copies]:
                    result.append((dest, src))
                    copies.remove((dest, src))
                    progress = True
                    break

            if progress:
                continue

            # ciclo
            dest, src = copies.pop(0)
            temp = TempVersion(Temp(src.type), 1)
            result.append((temp, src))
            copies.append((dest, temp))

        return result