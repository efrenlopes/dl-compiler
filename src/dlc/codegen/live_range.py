from dlc.inter.ic import IC
from dlc.inter.operator import Operator

class LiveRange:
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
    
    def __str__(self):
        return f'({self.start}, {self.end})'
    
    def __repr__(self):
        return f'LiveRange:{str(self)}'

    @staticmethod
    def compute_live_ranges(ic: IC):
        int_live_ranges = {}
        double_live_ranges = {}
        
        # 1. Passo: Cálculo Linear (O que você já fez)
        # Mapeamos o label para o índice da instrução para detectar loops
        label_to_idx = {}
        instructions = list(ic) # Lineariza para facilitar o acesso por índice

        for i, instr in enumerate(instructions):
            # Registrar onde os labels estão
            if instr.op == Operator.LABEL:
                label_to_idx[instr.result] = i

            # Coleta temporários para atualizar start/end
            operands = [instr.arg1, instr.arg2, instr.result]
            for var in operands:
                if var.is_temp:
                    target_map = double_live_ranges if var.type.is_float else int_live_ranges
                    if var not in target_map:
                        target_map[var] = LiveRange(i, i)
                    else:
                        target_map[var].end = i

        # 2. Passo: Correção de Loops (A solução comum)
        # Se houver um salto para trás (back-edge), estendemos o range de 
        # todas as variáveis que atravessam esse loop.
        for i, instr in enumerate(instructions):
            if instr.op in (Operator.GOTO, Operator.IF, Operator.IFFALSE):
                target_label = instr.result
                if target_label in label_to_idx:
                    target_idx = label_to_idx[target_label]
                    
                    # Se o destino do salto é ANTES da instrução atual, temos um LOOP
                    if target_idx < i:
                        # Todas as variáveis que nasceram antes ou durante o loop
                        # e que "sobrevivem" até o salto, devem ter seu fim estendido
                        # até o final do loop (a instrução de salto atual i)
                        for ranges in [int_live_ranges, double_live_ranges]:
                            for var, lr in ranges.items():
                                # Se a variável está viva no início do loop, 
                                # ela deve estar viva até o final dele.
                                if lr.start <= i and lr.end >= target_idx:
                                    lr.end = max(lr.end, i)

        return int_live_ranges, double_live_ranges








# class LiveRange:
#     def __init__(self):
#         self.start = None
#         self.end = None
    
#     def __str__(self):
#         return f'({self.start}, {self.end})'
    
#     def __repr__(self):
#         return f'LiveRange:{str(self)}'
    
#     @staticmethod
#     def compute_live_ranges(ic: IC):
#         int_live_ranges = {}
#         double_live_ranges = {}
#         for i, instr in enumerate(ic):
#             vars = []
#             if instr.arg1.is_temp:
#                 vars.append(instr.arg1)
#             if instr.arg2.is_temp:
#                 vars.append(instr.arg2)
#             if instr.result.is_temp:
#                 vars.append(instr.result)

#             for var in vars:
#                 live_ranges = double_live_ranges if var.type.is_float else int_live_ranges
#                 if var not in live_ranges:
#                     live_ranges[var] = LiveRange()
#                 if live_ranges[var].start is None:
#                     live_ranges[var].start = i
#                 live_ranges[var].end = i
            
#         return int_live_ranges, double_live_ranges
