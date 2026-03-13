from dlc.inter.operand import Operand
from dlc.inter.operator import Operator


class Instr:
    def __init__(self, op: Operator, 
                 arg1: Operand, arg2: Operand, result: Operand) -> None:
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
            
    def __str__(self) -> str:
        op = self.op
        arg1 = self.arg1
        arg2 = self.arg2
        result = self.result
        OP = Operator
        match op:
            case OP.MOVE: 
                return f'{result} {op} {arg1}'
            case OP.LABEL: 
                return f'{result}:'
            case OP.IF:
                return f'{op} {arg1} {OP.GOTO} {arg2} else {OP.GOTO} {result}'
            case OP.GOTO: 
                return f'{op} {result}'
            case OP.CONVERT | OP.PLUS | OP.MINUS | OP.NOT:
                return f'{result} {OP.MOVE} {op} {arg1}'
            case OP.PRINT: 
                return f'{op} {arg1}'
            case OP.READ:
                return f'{op} {result}'
            case OP.ALLOCA:
                return f'{result} {OP.MOVE} {OP.ALLOCA}'
            case OP.STORE:
                return f'{OP.STORE} {arg1}, {result}'
            case OP.LOAD:
                return f'{result} {OP.MOVE} {OP.LOAD} {arg1}'
            case _: 
                return f'{result} {OP.MOVE} {arg1} {op} {arg2}'


    def __repr__(self) -> str:
        return f'<Instr: {self.op}>'