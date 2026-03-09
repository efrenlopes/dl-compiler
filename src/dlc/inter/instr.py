from dlc.inter.operator import Operator
from dlc.inter.operand import Operand



class Instr:
    def __init__(self, op: Operator, arg1: Operand, arg2: Operand, result: Operand):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
            
    def __str__(self):
        op = self.op
        arg1 = self.arg1
        arg2 = self.arg2
        result = self.result
        
        match op:
            case Operator.MOVE: 
                return f'{result} {op} {arg1}'
            case Operator.LABEL: 
                return f'{result}:'
            case Operator.IF:
                return f'{op} {arg1} {Operator.GOTO} {arg2} else {Operator.GOTO} {result}'
            case Operator.GOTO: 
                return f'{op} {result}'
            case Operator.CONVERT | Operator.PLUS | Operator.MINUS | Operator.NOT:
                return f'{result} {Operator.MOVE} {op} {arg1}'
            case Operator.PRINT: 
                return f'{op} {arg1}'
            case Operator.READ:
                return f'{op} {result}'
            case Operator.PHI:
                return f'{result} {Operator.MOVE} {Operator.PHI}({", ".join(f"{bb}: {ver}" for bb, ver in arg1.paths.items())})'
            case Operator.ALLOCA:
                return f'{result} {Operator.MOVE} {Operator.ALLOCA} {result.type}'
            case Operator.STORE:
                return f'{Operator.STORE} {arg1}, {result}'
            case Operator.LOAD:
                return f'{result} {Operator.MOVE} {Operator.LOAD} {arg1}'

            case _: 
                return f'{result} {Operator.MOVE} {arg1} {op} {arg2}'

    def __repr__(self):
        return f'<Instr: {self.op}>'