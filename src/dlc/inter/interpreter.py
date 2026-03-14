from collections.abc import Callable
from ctypes import c_double, c_int32
from typing import cast

from dlc.inter.ir import IR
from dlc.inter.operand import Const, Label, Operand, Temp
from dlc.inter.operator import Operator
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa_operand import TempVersion
from dlc.semantic.type import Type


class Interpreter:

    OP_BINARY: dict[Operator, 
             Callable[[Operand.RUNTIME_TYPES, Operand.RUNTIME_TYPES], 
                      Operand.RUNTIME_TYPES]] = {
        Operator.SUM: lambda a, b: a + b,
        Operator.SUB: lambda a, b: a - b,
        Operator.MUL: lambda a, b: a * b,
        Operator.DIV: lambda a, b: a / b if isinstance(a, float) else a//b,
        Operator.MOD: lambda a, b: a % b,
        Operator.POW: lambda a, b: a ** b,
        Operator.EQ: lambda a, b: a == b,
        Operator.NE: lambda a, b: a != b,
        Operator.LT: lambda a, b: a < b,
        Operator.LE: lambda a, b: a <= b,
        Operator.GT: lambda a, b: a > b,
        Operator.GE: lambda a, b: a >= b,
    }

    OP_UNARY: dict[Operator, 
             Callable[[Operand.RUNTIME_TYPES], Operand.RUNTIME_TYPES]] = {
        Operator.PLUS: lambda a: + a,
        Operator.MINUS: lambda a: - a,
        Operator.NOT: lambda a: not a,
        Operator.CONVERT: lambda a: float(a)
    }
    
    def __init__(self, ir: IR) -> None:
        self.ir = ir
        
    @staticmethod
    def __normalize(value: Operand.RUNTIME_TYPES) -> Operand.RUNTIME_TYPES:
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        else:
            return c_double(value).value


    def interpret(self) -> None:
        mem: dict[Operand, Operand.RUNTIME_TYPES|None] = {}

        def get_value(arg: Operand) -> Operand.RUNTIME_TYPES | None:
            if arg.is_temp or arg.is_temp_version:
                return mem.get(arg)
            elif arg.is_const:
                arg = cast(Const, arg)
                return arg.value
            return None

        bb_prev = None
        bb = self.ir.bb_sequence[0]
        while bb:
            bb_next = None
            for instr in bb:
                op = instr.op
                result = instr.result
                value1 = get_value(instr.arg1)
                value2 = get_value(instr.arg2)
                
                match op:
                    case Operator.PHI:
                        if bb_prev:
                            instr = cast(PhiInstr, instr)
                            value = get_value( instr.paths[bb_prev] )
                            mem[result] = value
                    case Operator.ALLOCA:
                        mem[result] = None
                    case Operator.STORE:
                        mem[result] = value1
                    case Operator.LOAD:
                        mem[result] = mem[instr.arg1]
                    case Operator.LABEL:
                        continue
                    case Operator.IF:
                        if bool(value1):
                            label = cast(Label, instr.arg2)
                            bb_next = self.ir.bb_from_label(label)
                        else:
                            label = cast(Label, instr.result)
                            bb_next = self.ir.bb_from_label(label)
                    case Operator.GOTO:
                        label = cast(Label, instr.result)
                        bb_next = self.ir.bb_from_label(label)
                    case Operator.PRINT:
                        if value1 is not None:
                            if isinstance(value1, float):
                                print(f'output: {value1:.4f}')
                            else:
                                print(f'output: {int(value1)}')
                    case Operator.READ:
                        try:
                            if isinstance(result, (Temp, TempVersion)):
                                i = input('input: ')
                                match result.type:
                                    case Type.BOOL:
                                        i = bool(int(i))
                                    case Type.INT:
                                        i = int(i)
                                    case Type.REAL:
                                        i = float(i)
                                    case _:
                                        raise RuntimeError('Não é um tipo válido!')
                                mem[result] = i
                        except ValueError:
                            print('Entrada de dados inválida! Interpretação encerrada.')
                            return
                    case Operator.MOVE:
                        mem[result] = value1
                    case _:
                        try:
                            if op in Interpreter.OP_BINARY \
                                    and value1 is not None and value2 is not None:
                                    value = Interpreter.OP_BINARY[op](value1, value2)
                            elif op in Interpreter.OP_UNARY and value1 is not None:
                                value = Interpreter.OP_UNARY[op](value1)
                            else:
                                raise RuntimeError('Operador não existe!')
                            mem[result] = Interpreter.__normalize(value)
                        except ZeroDivisionError:
                            print('Divisão por zero!')
                            return


            # BB transition
            bb_prev = bb
            bb = bb_next
