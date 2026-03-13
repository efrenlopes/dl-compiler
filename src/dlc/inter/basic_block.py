from dlc.inter.instr import Instr


class BasicBlock:
    
    __count = -1
    label_instr: Instr

    def __init__(self) -> None:
        BasicBlock.__count += 1
        self.number = BasicBlock.__count
        #bb sections
        self.phi_instrs = []
        self.body_instrs = []
        self.goto_instr = None
        #links
        self.successors = []
        self.predecessors = []

    def add_successor(self, bb):
        if bb not in self.successors:
            self.successors.append(bb)
        if self not in bb.predecessors:
            bb.predecessors.append(self)

    def __iter__(self):
        yield self.label_instr
        for i in self.phi_instrs:
            yield i
        for i in self.body_instrs:
            yield i
        if self.goto_instr is not None:
            yield self.goto_instr
    
    # def __getitem__(self, index):
    #     return self.instructions[index]
    
    def __str__(self) -> str:
        return f'bb{self.number}'
    
    def __repr__(self) -> str:
        return f'<{str(self)}>'
        #return f'<bb{self.number}: [{self.instructions[0]}]->[{self.instructions[-1]}]>'