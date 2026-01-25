from dl.semantic.type import Type
from dl.inter.ic import IC
from dl.codegen.live_range import LiveRange
from dl.codegen.reg_alloc import LinearScanRegisterAllocation


class X64CodeGenerator():
    OP_ARITH = {
        '+': 'add', 
        '-': 'sub', 
        '*': 'imul', 
    }

    OP_REL = {
        '==': 'sete', 
        '<': 'setl', 
        '>': 'setg'
    }
    
    # Registradores de 32bits de propósito geral preservados 
    REGISTERS = ['r12d', 'r13d', 'r14d', 'r15d'] #[r12d..r15d]
    
    # Registradores para operações
    ACC_REG = 'eax' #rax 64bits / eax 32bits
    CALL_ARG_REG = 'edi'
    

    # Alinhamento em 16 bytes (SysV ABI)
    def __align16(self, size: int) -> int:
        return (size + 15) // 16 * 16
    

    def __resolve_arg(self, arg):
        if arg.is_label:
            return f'L{arg.number}'
        elif arg.is_const:
            return str(arg)
        if arg in self.reg_alloc:
            return self.reg_alloc[arg]
        elif arg in self.spill_loc:
            offset = self.spill_loc[arg]
            return f'[rbp - {offset}]'


    def __init__(self, ic: IC):
        # Alocação de registros
        live_ranges = LiveRange.compute_live_ranges(ic)
        scan_reg_alloc = LinearScanRegisterAllocation(live_ranges, self.REGISTERS)
        
        # Atributos
        self.code = []
        self.reg_alloc = scan_reg_alloc.register_map
        self.spill_loc = scan_reg_alloc.spill_map

        # Cálculo do frame
        raw_frame_size = scan_reg_alloc.spill_count * Type.INT.size
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

            self.code.append(f'\t# {instr}')
            match instr.op:
                case 'label':
                    self.code.append(f'\t{dest}:')
                
                case 'goto':
                    self.code.append(f'\tjmp {dest}')

                case 'if':
                    self.code.append(f'\tmov {self.ACC_REG}, {arg1}')
                    self.code.append(f'\tcmp {self.ACC_REG}, 0')
                    self.code.append(f'\tjne {dest}')

                case 'iffalse':
                    self.code.append(f'\tmov {self.ACC_REG}, {arg1}')
                    self.code.append(f'\tcmp {self.ACC_REG}, 0')
                    self.code.append(f'\tje {dest}')
                
                case 'print':
                    self.code.append(f'\tmov {self.CALL_ARG_REG}, {arg1}')
                    self.code.append('\tcall print_int')
                
                case '=':  # Assign
                    self.code.append(f'\tmov {self.ACC_REG}, {arg1}')
                    self.code.append(f'\tmov {dest}, {self.ACC_REG}')
                
                case _:
                    if instr.op in self.OP_ARITH: # Operações aritméticas
                        self.code.append(f'\tmov {self.ACC_REG}, {arg1}')
                        self.code.append(f'\t{self.OP_ARITH[instr.op]} {self.ACC_REG}, {arg2}')
                        self.code.append(f'\tmov {dest}, {self.ACC_REG}')
                    else: # Operações relacionais
                        self.code.append(f'\tmov {self.ACC_REG}, {arg1}')
                        self.code.append(f'\tcmp {self.ACC_REG}, {arg2}')
                        self.code.append(f'\t{self.OP_REL[instr.op]} al')
                        self.code.append(f'\tmovzx {self.ACC_REG}, al')
                        self.code.append(f'\tmov {dest}, {self.ACC_REG}')



        # Epílogo
        self.code.extend([
            '\t# finaliza',
            'leave',
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
            '.section .rodata',
            '\tfmt_int:    .string "output: %d\\n"',
            '',
            '.section .note.GNU-stack,"",@progbits\n'
        ])
