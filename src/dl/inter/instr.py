from dl.inter.operand import Op

class Instr:
    def __init__(self, op: str, arg1: Op, arg2: Op, result: Op):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
            
    @property
    def is_label(self):
        return self.op == 'label'
    
    @property
    def is_uncond_jump(self):
        return self.op == 'goto'
    
    @property
    def is_cond_jump(self):
        return self.op in ('if', 'iffalse')
    
    @property
    def is_jump(self):
        return self.op in ('goto', 'if', 'iffalse')

    def __str__(self):
        op = self.op
        arg1 = self.arg1
        arg2 = self.arg2
        result = self.result
        
        match self.op:
            case '=': 
                return f'{result} = {arg1}'
            case 'label': 
                return f'{result}:'
            case 'if' | 'iffalse': 
                return f'{op} {arg1} goto {result}'
            case 'goto': 
                return f'{op} {result}'
            case 'convert': 
                return f'{result} = {op} {arg1}'
            case 'print': 
                return f'{op} {arg1}'
            case _: 
                return f'{result} = {arg1} {op} {arg2}'
