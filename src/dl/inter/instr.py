from dl.inter.operator import Operator
from dl.inter.operand import Operand

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
            case Operator.IF | Operator.IFFALSE: 
                return f'{op} {arg1} {Operator.GOTO} {result}'
            case Operator.GOTO: 
                return f'{op} {result}'
            case Operator.CONVERT: 
                return f'{result} {Operator.MOVE} {op} {arg1}'
            case Operator.PRINT: 
                return f'{op} {arg1}'
            case Operator.READ:
                return f'{op} {result}'
            case _: 
                return f'{result} {Operator.MOVE} {arg1} {op} {arg2}'

    def __repr__(self):
        return f'<Instr: {self.op}>'