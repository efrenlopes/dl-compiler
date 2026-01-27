from dl.semantic.type import Type
from dl.inter.operator import Operator
from dl.inter.ic import IC
from dl.codegen.live_range import LiveRange
from dl.codegen.reg_alloc import LinearScanRegisterAllocation


class X64CodeGenerator():
    OP_ARITH_INT = {
            Operator.SUM: 'add',
            Operator.SUB: 'sub', 
            Operator.MUL: 'imul',
            Operator.DIV: 'idiv',
            Operator.MOD: 'idiv'
    }

    OP_ARITH_DOUBLE = {
            Operator.SUM: 'addsd',
            Operator.SUB: 'subsd',
            Operator.MUL: 'mulsd',
            Operator.DIV: 'divsd',
            Operator.MOD: 'divsd'
    }

    OP_REL_INT = {
        Operator.EQ: 'sete',
        Operator.LT: 'setl', 
        Operator.GT: 'setg'
    }

    OP_REL_DOUBLE = {
        Operator.EQ: 'sete',
        Operator.LT: 'setb', 
        Operator.GT: 'seta'
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
    
    # Registradores para operações
    ACC_REG = {
        Type.BOOL: 'eax',
        Type.INT: 'eax',
        Type.REAL: 'xmm1'
    }

    CALL_ARG_REG = {
        Type.BOOL: 'edi',
        Type.INT: 'edi',
        Type.REAL: 'xmm0'
    }

    # Registradores de 32bits de propósito geral preservados 
    INT_REGISTERS = ['r12d', 'r13d', 'r14d', 'r15d'] #[r12d..r15d]
    DOUBLE_REGISTERS = ['xmm8', 'xmm9', 'xmm10', 'xmm11'] #[xmm8...xmm15]



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
        elif arg in self.spill_loc:
            offset = self.spill_loc[arg]
            return f'[rbp - {offset}]'


    def __init__(self, ic: IC):
        # Alocação de registros
        int_live_ranges, double_live_ranges = LiveRange.compute_live_ranges(ic)
        int_scan_reg_alloc = LinearScanRegisterAllocation(int_live_ranges, self.INT_REGISTERS)
        double_scan_reg_alloc = LinearScanRegisterAllocation(double_live_ranges, self.DOUBLE_REGISTERS)
        int_reg_alloc = int_scan_reg_alloc.register_map
        double_reg_alloc = double_scan_reg_alloc.register_map
        int_spill_loc = int_scan_reg_alloc.spill_map
        double_spill_loc = double_scan_reg_alloc.spill_map

        #Atualizando os índices de spill para os endereços reais
        double_stack_top = int_scan_reg_alloc.spill_count * Type.INT.size
        for k in double_spill_loc:
            double_spill_loc[k] += double_stack_top

        # Atributos
        self.const_map = {}
        self.code = []
        self.reg_alloc = int_reg_alloc | double_reg_alloc
        self.spill_loc = int_spill_loc | double_spill_loc

        # Cálculo do frame
        raw_frame_size = int_scan_reg_alloc.spill_count*Type.INT.size + double_scan_reg_alloc.spill_count*Type.REAL.size
        frame_size = self.__align16(raw_frame_size)

        
        # Cabeçalho
        self.code.extend([
            '# Compilar com: gcc prog.s -o prog', #-no-pie
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


        # Gerar código para cada instrução
        for instr in ic:
            dest = self.__resolve_arg(instr.result)
            arg1 = self.__resolve_arg(instr.arg1)
            arg2 = self.__resolve_arg(instr.arg2)
            if arg1:
                type = instr.arg1.type

            self.code.append(f'\t# {instr}')
            match instr.op:
                case Operator.LABEL:
                    self.code.append(f'\t{dest}:')
                
                case Operator.GOTO:
                    self.code.append(f'\tjmp {dest}')

                case Operator.IF:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\tcmp {self.ACC_REG[type]}, 0')
                    self.code.append(f'\tjne {dest}')

                case Operator.IFFALSE:
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\tcmp {self.ACC_REG[type]}, 0')
                    self.code.append(f'\tje {dest}')
                
                case Operator.PRINT:
                    self.code.append(f'\t{self.MOVE[type]} {self.CALL_ARG_REG[type]}, {arg1}')
                    self.code.append(f'\tcall {self.PRINT[type]}')
                
                case Operator.MOVE:  # Assign
                    self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                    self.code.append(f'\t{self.MOVE[type]} {dest}, {self.ACC_REG[type]}')
                
                case Operator.CONVERT:
                    self.code.append(f'\t{self.MOVE[Type.INT]} {self.ACC_REG[Type.INT]}, {arg1}')
                    self.code.append(f'\tcvtsi2sd {self.ACC_REG[Type.REAL]}, {self.ACC_REG[Type.INT]}')
                    self.code.append(f'\t{self.MOVE[Type.REAL]} {dest}, {self.ACC_REG[Type.REAL]}')
                
                case _:
                    if instr.op in (Operator.SUM, Operator.SUB, Operator.MUL):
                        self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                        self.code.append(f'\t{self.OP_ARITH[type][instr.op]} {self.ACC_REG[type]}, {arg2}')
                        self.code.append(f'\t{self.MOVE[type]} {dest}, {self.ACC_REG[type]}')
                    elif instr.op in (Operator.EQ, Operator.LT, Operator.GT):
                        self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                        self.code.append(f'\t{self.CMP[type]} {self.ACC_REG[type]}, {arg2}')
                        self.code.append(f'\t{self.OP_REL[type][instr.op]} al')
                        self.code.append('\tmovzx eax, al')
                        self.code.append(f'\tmov {dest}, eax')
                    elif instr.op == Operator.DIV:
                        if type == Type.REAL:
                            self.code.append(f'\t{self.MOVE[type]} {self.ACC_REG[type]}, {arg1}')
                            self.code.append(f'\t{self.OP_ARITH[type][instr.op]} {self.ACC_REG[type]}, {arg2}')
                            self.code.append(f'\t{self.MOVE[type]} {dest}, {self.ACC_REG[type]}')
                        else:
                            self.code.append(f'\tmov eax, {arg1}')
                            self.code.append('\tcdq')
                            self.code.append(f'\tmov ecx, {arg2}')
                            self.code.append('\tidiv ecx')
                            self.code.append(f'\tmov {dest}, eax')
                    elif instr.op == Operator.MOD:
                        if type == Type.REAL:
                            self.code.append(f'\tmovsd xmm0, {arg1}')
                            self.code.append(f'\tmovsd xmm1, {arg2}')
                            self.code.append('\tmov eax, 2')
                            self.code.append('\tcall fmod@PLT')
                            self.code.append(f'\tmovsd {dest}, xmm0')
                        else:
                            self.code.append(f'\tmov eax, {arg1}')
                            self.code.append('\tcdq')
                            self.code.append(f'\tmov ecx, {arg2}')
                            self.code.append('\tidiv ecx')
                            self.code.append(f'\tmov {dest}, edx')


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
            '    lea rdi, [rip + fmt_int]',
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
            '   sub rsp, 16                 # Alinhamento de pilha (16 bytes)',
            '   lea rdi, [rip + fmt_double] # Carrega o ponteiro da string de formato',
            '   mov eax, 1                  # Indica ao printf que existe 1 reg XMM sendo usado (XMM0)',
            '   call printf',
            '   leave',
            '   ret',

            '.section .rodata',
            '\tfmt_int:    .string "output: %d\\n"',
            '\tfmt_double: .string "output: %.4f\\n"'
        ])

        for value in self.const_map:
            self.code.append(f'\t{self.const_map[value]}: .double {value}')
        
        self.code.append('\n.section .note.GNU-stack,"",@progbits\n')
        #'\tconstn: .double 12.5',
        #    '',