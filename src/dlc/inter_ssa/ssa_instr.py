from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAOperand



class SSAInstr:
    def __init__(self, op: SSAOperator, arg1: SSAOperand, arg2: SSAOperand, result: SSAOperand):
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
            case SSAOperator.MOVE: 
                return f'{result} {op} {arg1}'
            case SSAOperator.LABEL: 
                return f'{result}:'
            case SSAOperator.IF | SSAOperator.IFFALSE: 
                return f'{op} {arg1} {SSAOperator.GOTO} {result}'
            case SSAOperator.GOTO: 
                return f'{op} {result}'
            case SSAOperator.CONVERT | SSAOperator.PLUS | SSAOperator.MINUS | SSAOperator.NOT:
                return f'{result} {SSAOperator.MOVE} {op} {arg1}'
            case SSAOperator.PRINT: 
                return f'{op} {arg1}'
            case SSAOperator.READ:
                return f'{op} {result}'
            case SSAOperator.PHI:
                return f'{SSAOperator.PHI}'
            case _: 
                return f'{result} {SSAOperator.MOVE} {arg1} {op} {arg2}'

    def __repr__(self):
        return f'<Instr: {self.op}>'