from dlc.inter.ic import IC

class LiveRange:
    def __init__(self):
        self.start = None
        self.end = None
    
    def __str__(self):
        return f'({self.start}, {self.end})'
    
    def __repr__(self):
        return f'LiveRange:{str(self)}'
    
    @staticmethod
    def compute_live_ranges(ic: IC):
        int_live_ranges = {}
        double_live_ranges = {}
        for i, instr in enumerate(ic):
            vars = []
            if instr.arg1.is_temp:
                vars.append(instr.arg1)
            if instr.arg2.is_temp:
                vars.append(instr.arg2)
            if instr.result.is_temp:
                vars.append(instr.result)

            for var in vars:
                live_ranges = double_live_ranges if var.type.is_float else int_live_ranges
                if var not in live_ranges:
                    live_ranges[var] = LiveRange()
                if live_ranges[var].start is None:
                    live_ranges[var].start = i
                live_ranges[var].end = i

            
            # Esse trecho de código usa uma heurística: Se uma variável é definida 
            # antes de um label que é alvo de um GOTO posterior, e é usada dentro desse
            # bloco, o end da vida dela deve ser, no mínimo, a instrução de GOTO que fecha o loop.
            # A estratégia consolidada e recomendada usa Control-Flow.

            # if instr.op in (Operator.GOTO, Operator.IF, Operator.IFFALSE):
            #     label_index = ic.label_index(instr.result)
            #     if (label_index < i):
            #         for var, lr in int_live_ranges.items():
            #             if lr.start <= label_index and lr.end >= label_index:
            #                     lr.end = max(lr.end, i)
            #         for var, lr in double_live_ranges.items():
            #             if lr.start <= label_index and lr.end >= label_index:
            #                     lr.end = max(lr.end, i)


                
        return int_live_ranges, double_live_ranges
