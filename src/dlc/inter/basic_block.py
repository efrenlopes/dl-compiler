from __future__ import annotations

from collections.abc import Generator

from dlc.inter.instr import Instr


class BasicBlock:
    
    __count = -1
 
    def __init__(self) -> None:
        BasicBlock.__count += 1
        self.number = BasicBlock.__count
        #bb sections
        self.label_instr: Instr|None = None
        self.phi_instrs: list[Instr] = []
        self.body_instrs: list[Instr] = []
        self.goto_instr: Instr|None = None
        #links
        self.successors: list[BasicBlock] = []
        self.predecessors: list[BasicBlock] = []

    def add_successor(self, bb: BasicBlock) -> None:
        if bb not in self.successors:
            self.successors.append(bb)
        if self not in bb.predecessors:
            bb.predecessors.append(self)

    def __iter__(self) -> Generator[Instr, None, None]:
        if self.label_instr:
            yield self.label_instr
        for i in self.phi_instrs:
            yield i
        for i in self.body_instrs:
            yield i
        if self.goto_instr:
            yield self.goto_instr
    
   
    def __str__(self) -> str:
        return f'bb{self.number}'
    

    def __repr__(self) -> str:
        return f'<{str(self)}>'
        #return f'<bb{self.number}: [{self.instructions[0]}]->[{self.instructions[-1]}]>'