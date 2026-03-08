from dlc.inter_ssa.ssa import SSA
from dlc.inter_ssa.ssa_interference_graph import SSAInterferenceGraph
from dlc.inter_ssa.ssa_live_analysis import LivenessAnalysis
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.semantic.type import Type


class SSAX64CodeGenerator():
    OP_ARITH_INT = {
            SSAOperator.SUM: 'add',
            SSAOperator.SUB: 'sub', 
            SSAOperator.MUL: 'imul',
            SSAOperator.DIV: 'idiv',
            SSAOperator.MOD: 'idiv'
    }

    OP_ARITH_DOUBLE = {
            SSAOperator.SUM: 'addsd',
            SSAOperator.SUB: 'subsd',
            SSAOperator.MUL: 'mulsd',
            SSAOperator.DIV: 'divsd',
            SSAOperator.MOD: 'divsd'
    }

    OP_REL_INT = {
        SSAOperator.EQ: 'sete',
        SSAOperator.NE: 'setne',
        SSAOperator.LT: 'setl',
        SSAOperator.LE: 'setle',
        SSAOperator.GT: 'setg',
        SSAOperator.GE: 'setge'
    }

    OP_REL_DOUBLE = {
        SSAOperator.EQ: 'sete',
        SSAOperator.NE: 'setne',
        SSAOperator.LT: 'setb',
        SSAOperator.LE: 'setbe',
        SSAOperator.GT: 'seta',
        SSAOperator.GE: 'setae',
    }

    OP_ARITH = {
        Type.BOOL: OP_ARITH_INT,
        Type.INT: OP_ARITH_INT,
        Type.REAL: OP_ARITH_DOUBLE
    }

    OP_REL = {
        Type.BOOL: OP_REL_INT,
        Type.INT: OP_REL_INT,
        Type.REAL: OP_REL_DOUBLE
    }

    MOVE = {Type.BOOL: 'mov', Type.INT: 'mov', Type.REAL: 'movsd'}
    CMP = {Type.BOOL: 'cmp', Type.INT: 'cmp', Type.REAL: 'ucomisd'}
    PRINT = {Type.BOOL: 'print_int', Type.INT: 'print_int', Type.REAL: 'print_double'}
    READ = {Type.BOOL: 'read_int', Type.INT: 'read_int', Type.REAL: 'read_double'}
    
    # Registradores para operações
    ACC_REG = {
        Type.BOOL: 'eax',
        Type.INT: 'eax',
        Type.REAL: 'xmm0'
    }

    PHI_REG = {
        Type.BOOL: 'r11d',
        Type.INT: 'r11d',
        Type.REAL: 'xmm1'
    }

    CALL_ARG_REG = {
        Type.BOOL: 'edi',
        Type.INT: 'edi',
        Type.REAL: 'xmm0'
    }

    INT_REGISTERS = ['r12d', 'r13d', 'r14d', 'r15d'] #Registradores inteiros de 32 bits callee-saved
    DOUBLE_REGISTERS = [] #Todos as variáveis double ficarão na pilha



    # Alinhamento em 16 bytes (SysV ABI)
    def __align16(self, size: int) -> int:
        return (size + 15) // 16 * 16
    

    def __resolve_arg(self, arg):
        if arg.is_label:
            return f'L{arg.number}'
        elif arg.is_const:
            if arg.type.is_float:
                if arg.value not in self.const_map:
                    n = len(self.const_map)
                    self.const_map[arg.value] = f'const_{n}'
                return f'[rip + {self.const_map[arg.value]}]'
            return str(arg)
        if arg in self.reg_alloc:
            return self.reg_alloc[arg]
        elif arg in self.mem_alloc:
            offset = self.mem_alloc[arg]
            return f'[rbp - {offset}]'

    


    # def __resolve_phis(self, current_bb, target_label):
    #     target_bb = self.ssa.ic.bb_from_label(target_label)
    #     if not target_bb:
    #         return

    #     # 1. Coletamos todos os movimentos necessários antes de executar qualquer um
    #     moves = []
    #     for instr in target_bb.instructions:
    #         if instr.op == SSAOperator.PHI:
    #             phi_var_version = instr.arg1.paths.get(current_bb)
    #             if phi_var_version:
    #                 dest = self.__resolve_arg(instr.result)
    #                 src = self.__resolve_arg(phi_var_version)

    #                 if dest != src:
    #                     moves.append((dest, src, phi_var_version.type))

    #     self.code.append(f'\t# --- Resolvendo PHIs para {target_label} ---')

    #     for dest, src, v_type in moves:
    #         instr_mov = self.MOVE[v_type]
    #         phi_reg = self.PHI_REG[v_type]

    #         self.code.append(f'\t{instr_mov} {phi_reg}, {src}')
    #         self.code.append(f'\t{instr_mov} {dest}, {phi_reg}')


    def __resolve_phis(self, current_bb, target_label):
        target_bb = self.ssa.ic.bb_from_label(target_label)
        if not target_bb:
            return

        copies = []

        # 1. Coletar cópias
        for instr in target_bb.instructions:
            if instr.op == SSAOperator.PHI:
                phi_var_version = instr.arg1.paths.get(current_bb)

                if phi_var_version:
                    dest = self.__resolve_arg(instr.result)
                    src = self.__resolve_arg(phi_var_version)

                    if dest != src:
                        copies.append((dest, src, phi_var_version.type))

        if not copies:
            return

        self.code.append(f'\t# --- Resolvendo PHIs para {target_label} ---')

        copies = list(copies)

        while copies:
            progress = False
            # 2. procurar cópia segura
            for dest, src, v_type in copies:

                if dest not in [s for _, s, _ in copies]:
                    instr_mov = self.MOVE[v_type]
                    self.code.append(f'\t{instr_mov} {dest}, {src}')
                    copies.remove((dest, src, v_type))
                    progress = True
                    break

            if progress:
                continue

            # 3. existe ciclo → quebrar com temporário
            dest, src, v_type = copies.pop(0)
            instr_mov = self.MOVE[v_type]
            tmp = self.PHI_REG[v_type]
            self.code.append(f'\t{instr_mov} {tmp}, {src}')
            copies.append((dest, tmp, v_type))




    def __init__(self, ssa: SSA):
        # Análise de vivacidade
        self.ssa = ssa
        int_liveness = LivenessAnalysis(ssa, types=(Type.INT, Type.BOOL))
        double_liveness = LivenessAnalysis(ssa, types=(Type.REAL,))


        int_ig = SSAInterferenceGraph(int_liveness, self.INT_REGISTERS)
        double_ig =  SSAInterferenceGraph(double_liveness, self.DOUBLE_REGISTERS)

        int_reg_alloc = int_ig.reg_alloc
        int_mem_alloc = int_ig.mem_alloc

        double_reg_alloc = double_ig.reg_alloc
        double_mem_alloc = double_ig.mem_alloc



        #Atualizando os índices de spill para os endereços reais
        for k in int_mem_alloc:
            int_mem_alloc[k] = (int_mem_alloc[k] + 1) * Type.INT.size
            
        double_stack_top = int_ig.spill_slots_count * Type.INT.size
        for k in double_mem_alloc:
            double_mem_alloc[k] = double_stack_top + (double_mem_alloc[k] + 1) * Type.REAL.size


        # Atributos
        self.const_map = {}
        self.code = []
        self.reg_alloc = int_reg_alloc | double_reg_alloc
        self.mem_alloc = int_mem_alloc | double_mem_alloc

        # Cálculo do frame
        raw_frame_size = int_ig.spill_slots_count*Type.INT.size + double_ig.spill_slots_count*Type.REAL.size
        frame_size = self.__align16(raw_frame_size)

        
        # Cabeçalho
        self.code.extend([
            '# Compilar com: gcc prog.s -o prog -lm',
            '.intel_syntax noprefix',
            '',
            '.section .text',
            '.globl main',
            '.extern printf',
            '',
            'main:',
            '\t# stack',
            '\tpush rbp',
            '\tmov rbp, rsp',
            f'\tsub rsp, {frame_size}',
            ''
        ])

        current_bb = None

        # Gerar código para cada instrução
        for instr in ssa.ic:
            result = self.__resolve_arg(instr.result)
            arg1 = self.__resolve_arg(instr.arg1)
            arg2 = self.__resolve_arg(instr.arg2)
            if arg1:
                type = instr.arg1.type
            if instr.result and instr.result.is_temp_version:
                result_type = instr.result.type

            self.code.append(f'\t# {instr}')
            match instr.op:
                case SSAOperator.PHI:
                    continue

                case SSAOperator.LABEL:
                    current_bb = ssa.ic.bb_from_label(instr.result)
                    self.code.append(f'\t{result}:')
                
                case SSAOperator.GOTO:
                    self.__resolve_phis(current_bb, instr.result)
                    self.code.append(f'\tjmp {result}')




                case SSAOperator.IF:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\tcmp {self.ACC_REG[type]}, 0')

                    label_true = self.__resolve_arg(instr.arg2)
                    label_false = self.__resolve_arg(instr.result)

                    internal_label_false = f".L_if_false_{len(self.code)}"

                    # se cond == 0 → FALSE
                    self.code.append(f'\tje {internal_label_false}')

                    # TRUE
                    self.__resolve_phis(current_bb, instr.arg2)
                    self.code.append(f'\tjmp {label_true}')

                    # FALSE
                    self.code.append(f'{internal_label_false}:')
                    self.__resolve_phis(current_bb, instr.result)
                    self.code.append(f'\tjmp {label_false}')




                case SSAOperator.PRINT:
                    self.code.append(f'\t{self.MOVE[type]} {self.CALL_ARG_REG[type]}, {arg1}')
                    self.code.append(f'\tcall {self.PRINT[type]}')
                
                case SSAOperator.READ:
                    self.code.append(f'\tcall {self.READ[result_type]}')
                    self.code.append(f'\t{self.MOVE[result_type]} {result}, {self.ACC_REG[result_type]}')

                case SSAOperator.MOVE | SSAOperator.PLUS:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\t{self.MOVE[type]} {result}, {self.ACC_REG[type]}')
                
                case SSAOperator.CONVERT:
                    self.code.append(f'\t{self.MOVE[Type.INT]} {self.ACC_REG[Type.INT]}, {arg1}')
                    self.code.append(f'\tcvtsi2sd {self.ACC_REG[Type.REAL]}, {self.ACC_REG[Type.INT]}')
                    self.code.append(f'\t{self.MOVE[Type.REAL]} {result}, {self.ACC_REG[Type.REAL]}')

                case SSAOperator.MINUS:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\tneg {self.ACC_REG[type]}')
                    self.code.append(f'\t{self.MOVE[result_type]} {result}, {self.ACC_REG[type]}')

                case SSAOperator.NOT:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\txor {self.ACC_REG[type]}, 1')
                    self.code.append(f'\t{self.MOVE[result_type]} {result}, {self.ACC_REG[type]}')
                    

                case _:
                    if instr.op in (SSAOperator.SUM, SSAOperator.SUB, SSAOperator.MUL):
                        self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                        self.code.append(f'\t{self.OP_ARITH[type][instr.op]} {self.ACC_REG[type]}, {arg2}')
                        self.code.append(f'\t{self.MOVE[result_type]} {result}, {self.ACC_REG[type]}')
                    elif instr.op in (SSAOperator.EQ, SSAOperator.NE, SSAOperator.LT, SSAOperator.LE, SSAOperator.GT, SSAOperator.GE):
                        self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                        self.code.append(f'\t{self.CMP[type]} {self.ACC_REG[type]}, {arg2}')
                        self.code.append(f'\t{self.OP_REL[type][instr.op]} al')
                        self.code.append('\tmovzx eax, al')
                        self.code.append(f'\tmov {result}, eax')
                    elif instr.op == SSAOperator.DIV:
                        if type == Type.REAL:
                            self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                            self.code.append(f'\t{self.OP_ARITH[type][instr.op]} {self.ACC_REG[type]}, {arg2}')
                            self.code.append(f'\t{self.MOVE[result_type]} {result}, {self.ACC_REG[type]}')
                        else:
                            self.code.append(f'\tmov eax, {arg1}')
                            self.code.append('\tcdq')
                            self.code.append(f'\tmov ecx, {arg2}')
                            self.code.append('\tidiv ecx')
                            self.code.append(f'\tmov {result}, eax')
                    elif instr.op == SSAOperator.MOD:
                        if type == Type.REAL:
                            self.code.append(f'\tmovsd xmm0, {arg1}')
                            self.code.append(f'\tmovsd xmm1, {arg2}')
                            self.code.append('\tmov eax, 2')
                            self.code.append('\tcall fmod@PLT')
                            self.code.append(f'\tmovsd {result}, xmm0')
                        else:
                            self.code.append(f'\tmov eax, {arg1}')
                            self.code.append('\tcdq')
                            self.code.append(f'\tmov ecx, {arg2}')
                            self.code.append('\tidiv ecx')
                            self.code.append(f'\tmov {result}, edx')
                    elif instr.op == SSAOperator.POW:
                        if type == Type.REAL:
                            self.code.append(f'\tmovsd xmm0, {arg1}')
                            self.code.append(f'\tmovsd xmm1, {arg2}')
                            self.code.append('\tcall power')
                            self.code.append(f'\tmovsd {result}, xmm0')
                        else:
                            self.code.append(f'\tmov eax, {arg1}')
                            self.code.append('\tcvtsi2sd xmm0, eax')
                            self.code.append(f'\tmov eax, {arg2}')
                            self.code.append('\tcvtsi2sd xmm1, eax')
                            self.code.append('\tcall power')
                            self.code.append('\tcvtsd2si eax, xmm0')
                            self.code.append(f'\tmov {result}, eax')




        # Epílogo
        self.code.extend([
            '\t# finaliza',
            '\tleave',
            '\tmov eax, 0',
            '\tret',
            '',
            '# ---------------------------------------------------------',
            '# Rotina: print_int',
            '# ---------------------------------------------------------',
            'print_int:',
            '    push rbp',
            '    mov rbp, rsp',
            '    sub rsp, 16',
            '    mov esi, edi',
            '    lea rdi, [rip + fmt_out_int]',
            '    xor eax, eax',
            '    call printf',
            '    leave',
            '    ret',
            '',
            '# ---------------------------------------------------------',
            '# Rotina: print_double',
            '# ---------------------------------------------------------',
            'print_double:',
            '   push rbp',
            '   mov rbp, rsp',
            '   sub rsp, 16                     # Alinhamento de pilha (16 bytes)',
            '   lea rdi, [rip + fmt_out_double] # Carrega o ponteiro da string de formato',
            '   mov eax, 1                      # Indica ao printf que existe 1 reg XMM sendo usado (XMM0)',
            '   call printf',
            '   leave',
            '   ret',
            '',
            '# ---------------------------------------------------------',
            '# Rotina: read_int',
            '# Retorno: eax (o valor lido)',
            '# ---------------------------------------------------------',
            'read_int:',
            '    push rbp',
            '    mov rbp, rsp',
            '    sub rsp, 16',
            '',
            '    # Exibe o prompt "input: "',
            '    lea rdi, [rip + str_input_prompt]',
            '    xor eax, eax',
            '    call printf@PLT',
            '    ',
            '    # Realiza a leitura',
            '    lea rdi, [rip + fmt_in_int]',
            '    lea rsi, [rbp - 4]',
            '    xor eax, eax',
            '    call scanf@PLT',
            '',
            '    mov eax, [rbp - 4]',
            '    leave',
            '    ret',
            '',
            '# ---------------------------------------------------------',
            '# Rotina: read_double',
            '# Retorno: xmm0',
            '# ---------------------------------------------------------',
            'read_double:',
            '    push rbp',
            '    mov rbp, rsp',
            '    sub rsp, 16',
            '',
            '    # Exibe o prompt "input: "',
            '    lea rdi, [rip + str_input_prompt]',
            '    xor eax, eax',
            '    call printf@PLT',
            '',
            '    # Realiza a leitura',
            '    lea rdi, [rip + fmt_in_double]',
            '    lea rsi, [rbp - 8]',
            '    xor eax, eax',
            '    call scanf@PLT',
            '',
            '    movsd xmm0, [rbp - 8]',
            '    leave',
            '    ret',            '',
            '',
            '# ---------------------------------------------------------',
            '# Rotina: power (Calcula XMM0 ^ XMM1)',
            '# ---------------------------------------------------------',
            '# Argumentos: ',
            '#   XMM0: Base (Double)',
            '#   XMM1: Expoente (Double)',
            '# Retorno:',
            '#   XMM0: Resultado do cálculo',
            '# ---------------------------------------------------------',
            'power:',
            '    push rbp',
            '    mov rbp, rsp',
            '    sub rsp, 16            # ADICIONE ISSO para alinhamento de 16 bytes!',
            '    mov eax, 2             # Indica que existem 2 argumentos em registradores XMM (XMM0 e XMM1)',
            '    call pow@PLT           # Chama a função pow da libc',
            '    leave',
            '    ret',
            '',
            '.section .rodata',
            '\tstr_input_prompt: .string "input: "',
            '\tfmt_in_int:       .string "%d"',
            '\tfmt_in_double:    .string "%lf"',
            '\tfmt_out_int:      .string "output: %d\\n"',
            '\tfmt_out_double:   .string "output: %.4lf\\n"',
        ])

        for value in self.const_map:
            self.code.append(f'\t{self.const_map[value]}: .double {value}')
        
        self.code.append('\n.section .note.GNU-stack,"",@progbits\n')