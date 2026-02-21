class BasicBlock:
    
    __count = -1

    def __init__(self):
        BasicBlock.__count += 1
        self.number = BasicBlock.__count
        self.instructions = []
        self.successors = []
        self.predecessors = []

    def add_successor(self, bb):
        if bb not in self.successors:
            self.successors.append(bb)
        if self not in bb.predecessors:
            bb.predecessors.append(self)

    def __iter__(self):
        return iter(self.instructions)
    
    def __getitem__(self, index):
        return self.instructions[index]
    
    def __str__(self):
        return f'bb{self.number}'
    
    def __repr__(self):
        return str(self)
        #return f'<bb{self.number}: [{self.instructions[0]}]->[{self.instructions[-1]}]>'