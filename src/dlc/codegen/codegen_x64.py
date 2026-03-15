from dlc.codegen.interference_graph import InterferenceGraph
from dlc.codegen.live_analysis import LivenessAnalysis
from dlc.inter.operand import Const, Label, Operand
from dlc.inter.operator import Operator
from dlc.inter.ssa import SSA
from dlc.inter.ssa_operand import TempVersion
from dlc.semantic.type import Type

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
    Operator.NE: 'setne',
    Operator.LT: 'setl',
    Operator.LE: 'setle',
    Operator.GT: 'setg',
    Operator.GE: 'setge'
}

OP_REL_DOUBLE = {
    Operator.EQ: 'sete',
    Operator.NE: 'setne',
    Operator.LT: 'setb',
    Operator.LE: 'setbe',
    Operator.GT: 'seta',
    Operator.GE: 'setae',
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

#Registradores callee-saved por tipo
INT_REGISTERS: list[str] = ['r12d', 'r13d'] #['r12d', 'r13d', 'r14d', 'r15d']
DOUBLE_REGISTERS: list[str] = ['xmm2']



class CodeGeneratorX64:

    # Alinhamento em 16 bytes (SysV ABI)
    def __align16(self, size: int) -> int:
        return (size + 15) // 16 * 16
    

    def __resolve_arg(self, arg: Operand) -> str | None:
        if isinstance(arg, Label):
            return f'L{arg.number}'
        elif isinstance(arg, Const):
            if arg.type.is_float:
                if arg.value not in self.const_map:
                    n = len(self.const_map)
                    self.const_map[arg.value] = f'const_{n}'
                return f'[rip + {self.const_map[arg.value]}]'
            return str(arg)
        elif arg in self.reg_alloc:
            assert(isinstance(arg, TempVersion))
            return self.reg_alloc[arg]
        elif arg in self.mem_alloc:
            assert(isinstance(arg, TempVersion))
            offset = self.mem_alloc[arg]
            return f'[rbp - {offset}]'
        return None

    

    def __init__(self, ssa: SSA) -> None:
        self.ssa = ssa
        # Análise de vivacidade
        int_liveness = LivenessAnalysis(ssa, types=(Type.INT, Type.BOOL))
        double_liveness = LivenessAnalysis(ssa, types=(Type.REAL,))
        # Alocação de registradores
        int_ig = InterferenceGraph(int_liveness, INT_REGISTERS)
        double_ig =  InterferenceGraph(double_liveness, DOUBLE_REGISTERS)


        #Atualizando os índices de spill para os endereços reais
        for k in int_ig.mem_alloc:
            int_ig.mem_alloc[k] = (int_ig.mem_alloc[k] + 1) * Type.INT.size
        double_stack_top = int_ig.spill_slots_count * Type.INT.size
        for k in double_ig.mem_alloc:
            double_ig.mem_alloc[k] = \
                double_stack_top + (double_ig.mem_alloc[k] + 1) * Type.REAL.size

        # Atributos
        self.const_map: dict[float, str] = {}
        self.code: list[str] = []
        self.reg_alloc = int_ig.reg_alloc | double_ig.reg_alloc
        self.mem_alloc = int_ig.mem_alloc | double_ig.mem_alloc

        # Cálculo do frame
        raw_frame_size = int_ig.spill_slots_count*Type.INT.size + \
                            double_ig.spill_slots_count*Type.REAL.size
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

        # Gerar código para cada instrução
        for instr in ssa.ir:
            result = self.__resolve_arg(instr.result)
            arg1 = self.__resolve_arg(instr.arg1)
            arg2 = self.__resolve_arg(instr.arg2)
            type = instr.arg1.type \
                        if isinstance(instr.arg1, (TempVersion, Const)) else None
            result_type = instr.result.type \
                        if isinstance(instr.result, TempVersion) else None

            code = self.code
            code.append(f'\t# {instr}')
            match instr.op:
                case Operator.PHI:
                    raise RuntimeError('Este gerador de código deve receber um SSA \
                                            com instruções Phi eliminadas')

                case Operator.LABEL:
                    code.append(f'\t{result}:')
                
                case Operator.GOTO:
                    code.append(f'\tjmp {result}')

                case Operator.IF:
                    assert type is not None
                    code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                    code.append(f'\tcmp {ACC_REG[type]}, 0')
                    code.append(f'\tjne {arg2}')
                    code.append(f'\tjmp {result}')

                case Operator.PRINT:
                    assert type is not None
                    code.append(f'\t{MOVE[type]} {CALL_ARG_REG[type]}, {arg1}')
                    code.append(f'\tcall {PRINT[type]}')
                
                case Operator.READ:
                    assert result_type is not None
                    code.append(f'\tcall {READ[result_type]}')
                    code.append(
                        f'\t{MOVE[result_type]} {result}, {ACC_REG[result_type]}')

                case Operator.MOVE | Operator.PLUS:
                    assert type is not None
                    code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                    code.append(f'\t{MOVE[type]} {result}, {ACC_REG[type]}')
                
                case Operator.CONVERT:
                    code.append(f'\t{MOVE[Type.INT]} {ACC_REG[Type.INT]}, {arg1}')
                    code.append(f'\tcvtsi2sd {ACC_REG[Type.REAL]}, {ACC_REG[Type.INT]}')
                    code.append(f'\t{MOVE[Type.REAL]} {result}, {ACC_REG[Type.REAL]}')

                case Operator.MINUS:
                    assert type is not None and result_type is not None
                    code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                    code.append(f'\tneg {ACC_REG[type]}')
                    code.append(f'\t{MOVE[result_type]} {result}, {ACC_REG[type]}')

                case Operator.NOT:
                    assert type is not None and result_type is not None
                    code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                    code.append(f'\txor {ACC_REG[type]}, 1')
                    code.append(f'\t{MOVE[result_type]} {result}, {ACC_REG[type]}')
                    
                case _:
                    if instr.op in (Operator.SUM, Operator.SUB, Operator.MUL):
                        assert type is not None and result_type is not None
                        code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                        code.append(
                            f'\t{OP_ARITH[type][instr.op]} {ACC_REG[type]}, {arg2}')
                        code.append(f'\t{MOVE[result_type]} {result}, {ACC_REG[type]}')
                    elif instr.op in (Operator.EQ, Operator.NE, Operator.LT, 
                                            Operator.LE, Operator.GT, Operator.GE):
                        assert type is not None
                        code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                        code.append(f'\t{CMP[type]} {ACC_REG[type]}, {arg2}')
                        code.append(f'\t{OP_REL[type][instr.op]} al')
                        code.append('\tmovzx eax, al')
                        code.append(f'\tmov {result}, eax')
                    elif instr.op == Operator.DIV:
                        assert type is not None and result_type is not None
                        if type == Type.REAL:
                            code.append(f'\t{MOVE[type]} {ACC_REG[type]}, {arg1}')
                            code.append(
                                f'\t{OP_ARITH[type][instr.op]} {ACC_REG[type]}, {arg2}')
                            code.append(
                                f'\t{MOVE[result_type]} {result}, {ACC_REG[type]}')
                        else:
                            code.append(f'\tmov eax, {arg1}')
                            code.append('\tcdq')
                            code.append(f'\tmov ecx, {arg2}')
                            code.append('\tidiv ecx')
                            code.append(f'\tmov {result}, eax')
                    elif instr.op == Operator.MOD:
                        if type == Type.REAL:
                            code.append(f'\tmovsd xmm0, {arg1}')
                            code.append(f'\tmovsd xmm1, {arg2}')
                            code.append('\tmov eax, 2')
                            code.append('\tcall fmod@PLT')
                            code.append(f'\tmovsd {result}, xmm0')
                        else:
                            code.append(f'\tmov eax, {arg1}')
                            code.append('\tcdq')
                            code.append(f'\tmov ecx, {arg2}')
                            code.append('\tidiv ecx')
                            code.append(f'\tmov {result}, edx')
                    elif instr.op == Operator.POW:
                        if type == Type.REAL:
                            code.append(f'\tmovsd xmm0, {arg1}')
                            code.append(f'\tmovsd xmm1, {arg2}')
                            code.append('\tcall power')
                            code.append(f'\tmovsd {result}, xmm0')
                        else:
                            code.append(f'\tmov eax, {arg1}')
                            code.append('\tcvtsi2sd xmm0, eax')
                            code.append(f'\tmov eax, {arg2}')
                            code.append('\tcvtsi2sd xmm1, eax')
                            code.append('\tcall power')
                            code.append('\tcvtsd2si eax, xmm0')
                            code.append(f'\tmov {result}, eax')


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
            '   lea rdi, [rip + fmt_out_double] # Ponteiro da string de formato',
            '   mov eax, 1                      # Indica que o reg XMM0 está em uso',
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
            '    mov eax, 2             # Os argumentos estão em XMM0 e XMM1',
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