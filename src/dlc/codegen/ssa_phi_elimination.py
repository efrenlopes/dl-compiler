from dlc.inter.basic_block import BasicBlock
from dlc.inter.instr import Instr
from dlc.inter.operand import Operand
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

            copies_by_pred: dict[BasicBlock, list[tuple[TempVersion, TempVersion]]] = {}

            # coletar cópias
            for phi in bb.phi_instrs:
                assert(isinstance(phi, PhiInstr))
                res = phi.result

                for pred, src in phi.paths.items():
                    if src == res:
                        continue
                    assert isinstance(res, TempVersion) and isinstance(src, TempVersion)
                    copies_by_pred.setdefault(pred, []).append((res, src))

            # resolver cópias em cada predecessor
            for pred, copies in copies_by_pred.items():
                for res, src in copies:
                    move = Instr(Operator.MOVE, src, Operand.EMPTY, res)
                    pred.body_instrs.append(move)

            bb.phi_instrs.clear()