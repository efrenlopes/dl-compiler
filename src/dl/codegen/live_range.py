from dl.inter.ic import IC

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
        live_ranges = {}
        for i, instr in enumerate(ic):
            vars = []

            if instr.arg1.is_temp:
                vars.append(instr.arg1)
            if instr.arg2.is_temp:
                vars.append(instr.arg2)
            if instr.result.is_temp:
                vars.append(instr.result)

            for var in vars:
                if var not in live_ranges:
                    live_ranges[var] = LiveRange()
                if live_ranges[var].start is None:
                    live_ranges[var].start = i
                live_ranges[var].end = i        
        return live_ranges
