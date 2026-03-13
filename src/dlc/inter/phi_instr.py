from dlc.inter.basic_block import BasicBlock
from dlc.inter.instr import Instr
from dlc.inter.operand import Operand
from dlc.inter.operator import Operator


class PhiInstr(Instr):
    def __init__(self) -> None:
        super().__init__(Operator.PHI, Operand.EMPTY, Operand.EMPTY, Operand.EMPTY)
        self.paths: dict[BasicBlock, Operand] = {}


    def add_path(self, block: BasicBlock, value: Operand) -> None:
        self.paths[block] = value
            

    def __str__(self) -> str:
        return (f'{self.result} {Operator.MOVE} {Operator.PHI}('
            f'{", ".join(f"{bb}: {temp}" for bb, temp in self.paths.items())})')


    def __repr__(self) -> str:
        return f'<Instr: {self.op}>'