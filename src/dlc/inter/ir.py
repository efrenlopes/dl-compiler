from collections import defaultdict
from collections.abc import Callable, Generator
from ctypes import c_double, c_int32
from typing import cast

from graphviz import Digraph  # type: ignore

from dlc.inter.basic_block import BasicBlock
from dlc.inter.instr import Instr
from dlc.inter.operand import Const, Label, Operand, Temp
from dlc.inter.operator import Operator
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa_operand import TempVersion
from dlc.lex.tag import Tag
from dlc.semantic.type import Type
from dlc.tree.ast import AST
from dlc.tree.nodes import (
    AssignNode,
    BinaryNode,
    BlockNode,
    ConvertNode,
    DeclNode,
    ElseNode,
    IfNode,
    LiteralNode,
    ProgramNode,
    ReadNode,
    UnaryNode,
    VarNode,
    WhileNode,
    WriteNode,
)
from dlc.tree.visitor import Visitor


class IR(Visitor[Operand]):
    
    __OP_MAP = {
        Tag.SUM: Operator.SUM,
        Tag.SUB: Operator.SUB,
        Tag.MUL: Operator.MUL,
        Tag.DIV: Operator.DIV,
        Tag.MOD: Operator.MOD,
        Tag.POW: Operator.POW,
        Tag.EQ : Operator.EQ,
        Tag.NE : Operator.NE,
        Tag.LT: Operator.LT,
        Tag.LE: Operator.LE,
        Tag.GT: Operator.GT,
        Tag.GE: Operator.GE
    }

    def __init__(self, ast: AST) -> None:
        self.__var_temp_map: dict[tuple[str, int], Temp] = {}
        self.label_bb_map: defaultdict[Label, BasicBlock] = defaultdict(BasicBlock)
        self.bb_sequence: list[BasicBlock] = []
        self.__comments: dict[Instr, str] = {}
        # Entry Basic Block
        L0 = Label()
        bb_entry = BasicBlock()
        self.label_bb_map[L0] = bb_entry
        self.__bb_current = bb_entry
        self.add_instr( Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, L0 ))
        # Starting IR generation
        ast.root.accept(self)


    def __iter__(self) -> Generator[Instr, None, None]:
        for bb in self.bb_sequence:
            yield from bb
    

    def bb_from_label(self, label: Label) -> BasicBlock:
        return self.label_bb_map[label]


    def add_instr(self, instr: Instr, comment: str|None=None) -> None:
        match instr.op:
            case Operator.LABEL:
                label = cast(Label, instr.result)
                new_bb = self.label_bb_map[label]
                new_bb.label_instr = instr
                self.bb_sequence.append(new_bb)
                self.__bb_current = new_bb
            case Operator.GOTO | Operator.IF:
                for arg in (instr.arg2, instr.result):
                    if arg.is_label:
                        label = cast(Label, arg)
                        bb_target = self.label_bb_map[label]
                        self.__bb_current.add_successor(bb_target)
                self.__bb_current.goto_instr = instr
            case Operator.PHI:
                self.__bb_current.phi_instrs.append(instr)
            case _:
                self.__bb_current.body_instrs.append(instr)

        if comment:
            self.__comments[instr] = comment




    def plot(self) -> None:
        dot = Digraph()
        dot.attr(fontname="consolas") # type: ignore
        for bb in self.bb_sequence:
            code = [str(i) for i in bb]
            dot.node(name=str(bb), label='\n'.join(code), shape="box", xlabel=str(bb)) # type: ignore
            for s in bb.successors:
                dot.edge(str(bb), str(s)) # type: ignore
        dot.render('out/teste_fluxo', view=False)  # type: ignore



    def __str__(self) -> str:
        tac: list[str] = []
        count = 0
        for bb in self.bb_sequence:
            tac.append(f'----{bb}----')
            for instr in bb:
                line = f'{count:03d}\t{str(instr):<20}'
                comment = self.__comments.get(instr)
                if comment:
                    line += f'\t\t#{comment}'
                tac.append(line)
                count += 1
        return '\n'.join(tac)


    def visit_program_node(self, node: ProgramNode) -> Operand:
        node.stmt.accept(self)
        return Operand.EMPTY
    

    def visit_block_node(self, node: BlockNode) -> Operand:
        for stmt in node.stmts:
            stmt.accept(self)
        return Operand.EMPTY
        
    
    def visit_decl_node(self, node: DeclNode) -> Operand:
        for var in node.vars:
            temp = Temp(var.type, True)
            key = (var.name, var.scope)
            self.__var_temp_map[key] = temp
            comment = f'var {var.name} [type={var.type}, scope={var.scope}]'
            self.add_instr(
                Instr(Operator.ALLOCA, Operand.EMPTY, Operand.EMPTY, temp),
                comment
            )
        return Operand.EMPTY
        

    def visit_assign_node(self, node: AssignNode) -> Operand:
        arg = node.expr.accept(self)
        key = (node.var.name, node.var.scope)
        temp = self.__var_temp_map[key]
        self.add_instr(Instr(Operator.STORE, arg, Operand.EMPTY, temp))
        return Operand.EMPTY


    def visit_var_node(self, node: VarNode) -> Operand:
        temp = Temp(node.type)
        key = (node.name, node.scope)
        var = self.__var_temp_map[key]
        self.add_instr(Instr(Operator.LOAD, var, Operand.EMPTY, temp))
        return temp




    def visit_literal_node(self, node: LiteralNode) -> Operand:
        return Const(node.type, node.value)


    def visit_convert_node(self, node: ConvertNode) -> Operand:
        arg = node.expr.accept(self)
        temp = Temp(node.type)
        self.add_instr(Instr(Operator.CONVERT, arg, Operand.EMPTY, temp))        
        return temp


    def visit_binary_node(self, node: BinaryNode) -> Operand:
        EMPTY = Operand.EMPTY
        
        if node.token.tag == Tag.OR:
            #labels
            lbl_test_b = Label()
            lbl_true = Label()
            lbl_false = Label()
            lbl_out = Label()
            temp = Temp(Type.BOOL)

            #Test-A
            arg1 = node.expr1.accept(self)
            self.add_instr(Instr(Operator.IF, arg1, lbl_true, lbl_test_b))
            #Test-B
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_test_b))
            arg2 = node.expr2.accept(self)
            self.add_instr(Instr(Operator.IF, arg2, lbl_true, lbl_false))
            #Block-True
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
            #Block-False
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
            #Out
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_out))
        
        elif node.token.tag == Tag.AND:
            #labels
            lbl_test_b = Label()
            lbl_false = Label()
            lbl_true = Label()
            lbl_out = Label()
            temp = Temp(Type.BOOL)

            #Test-A
            arg1 = node.expr1.accept(self)
            self.add_instr(Instr(Operator.IF, arg1, lbl_test_b, lbl_false))
            #Test-B
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_test_b))
            arg2 = node.expr2.accept(self)
            self.add_instr(Instr(Operator.IF, arg2, lbl_true, lbl_false))
            #true
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
            #false
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
            #end
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_out))
        else:
            arg1 = node.expr1.accept(self)
            arg2 = node.expr2.accept(self)
            temp = Temp(node.type)              
            self.add_instr(Instr(IR.__OP_MAP[node.operator], arg1, arg2, temp))
        
        return temp




    def visit_unary_node(self, node: UnaryNode) -> Operand:
        arg = node.expr.accept(self)
        temp = Temp(node.type)
        
        match node.token.tag:
            case Tag.SUM:
                op = Operator.PLUS
            case Tag.SUB:
                op = Operator.MINUS
            case Tag.NOT:
                op = Operator.NOT
            case _:
                raise RuntimeError('Não é um operador unário')
        
        self.add_instr(Instr(op, arg, Operand.EMPTY, temp))
        return temp



    def visit_if_node(self, node: IfNode) -> Operand:
        arg = node.expr.accept(self)
        lbl_true = Label()
        lbl_out = Label()
        EMPTY = Operand.EMPTY

        #Test
        self.add_instr(Instr(Operator.IF, arg, lbl_true, lbl_out))
        #Block-True
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
        node.stmt.accept(self)
        self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
        #out
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_out))

        return Operand.EMPTY


    def visit_else_node(self, node: ElseNode) -> Operand:
        arg = node.expr.accept(self)
        lbl_true = Label()
        lbl_false = Label()
        lbl_out = Label()
        EMPTY = Operand.EMPTY

        #Test
        self.add_instr(Instr(Operator.IF, arg, lbl_true, lbl_false))
        #if-stmt
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
        node.stmt1.accept(self)
        self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
        #else-stmt
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
        node.stmt2.accept(self)
        self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_out))
        #out
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_out))

        return Operand.EMPTY



    def visit_while_node(self, node: WhileNode) -> Operand:
        lbl_entry = Label()
        lbl_body = Label()
        lbl_exit = Label()
        EMPTY = Operand.EMPTY
        #Test
        self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_entry))
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_entry))
        arg = node.expr.accept(self)
        self.add_instr(Instr(Operator.IF, arg, lbl_body, lbl_exit))
        #true
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_body))
        node.stmt.accept(self)
        self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_entry))
        #end
        self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_exit))

        return Operand.EMPTY

    
    def visit_write_node(self, node: WriteNode) -> Operand:
        arg = node.expr.accept(self)
        self.add_instr(Instr(Operator.PRINT, arg, Operand.EMPTY, Operand.EMPTY))
        return Operand.EMPTY


    def visit_read_node(self, node: ReadNode) -> Operand:
        temp = self.__var_temp_map[(node.var.name, node.var.scope)]
        self.add_instr(Instr(Operator.READ, Operand.EMPTY, Operand.EMPTY, temp))
        return Operand.EMPTY




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



    # @staticmethod
    # def operate(op: Operator, value1: Operand.RUNTIME_TYPES, 
    #             value2: Operand.RUNTIME_TYPES) -> Operand.RUNTIME_TYPES:
    #     value = IR.OP_BINARY[op](value1, value2)
    #     if isinstance(value, bool):
    #         return value
    #     elif isinstance(value, int):
    #         return c_int32(value).value
    #     else:
    #         return c_double(value).value

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
        bb = self.bb_sequence[0]
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
                        if value1:
                            label = cast(Label, instr.arg2)
                            bb_next = self.bb_from_label(label)
                        else:
                            label = cast(Label, instr.result)
                            bb_next = self.bb_from_label(label)
                    case Operator.GOTO:
                        label = cast(Label, instr.result)
                        bb_next = self.bb_from_label(label)
                    case Operator.PRINT:
                        if value1:
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
                        if op in IR.OP_BINARY \
                                and value1 is not None and value2 is not None:
                            value = IR.OP_BINARY[op](value1, value2)
                        elif op in IR.OP_UNARY and value1 is not None:
                            value = IR.OP_UNARY[op](value1)
                        else:
                            raise RuntimeError('Operador não existe!')
                        mem[result] = IR.__normalize(value)

            # BB transition
            bb_prev = bb
            bb = bb_next


    # def interpret(self) -> None:
    #     mem = {}

    #     def get_value(arg):
    #         if arg.is_temp or arg.is_temp_version:
    #             return mem.get(arg)
    #         elif arg.is_const:
    #             return arg.value

    #     bb_prev = None
    #     bb = self.bb_sequence[0]
    #     while bb:
    #         bb_next = None
    #         for instr in bb:
    #             op = instr.op
    #             result = instr.result
    #             value1 = get_value(instr.arg1)
    #             value2 = get_value(instr.arg2)
                
    #             match op:
    #                 case Operator.PHI:
    #                     value = get_value( instr.paths.get(bb_prev) ) #value = get_value( instr.arg1.paths.get(bb_prev, Operand.EMPTY)) #retorna Operand.EMPTY como valor padrão para o caso de PHIs inúteis
    #                     mem[result] = value
    #                 case Operator.ALLOCA:
    #                     mem[result] = None
    #                 case Operator.STORE:
    #                     mem[result] = value1
    #                 case Operator.LOAD:
    #                     mem[result] = mem[instr.arg1]
    #                 case Operator.LABEL:
    #                     continue
    #                 case Operator.IF:
    #                     if value1:                    
    #                         bb_next = self.bb_from_label(instr.arg2)
    #                     else:
    #                         bb_next = self.bb_from_label(instr.result)
    #                 case Operator.GOTO:
    #                     bb_next = self.bb_from_label(result)
    #                 case Operator.PRINT:
    #                     if isinstance(value1, float):
    #                         print(f'output: {value1:.4f}')
    #                     else:
    #                         print(f'output: {int(value1)}')
    #                 case Operator.READ:
    #                     try:
    #                         i = input('input: ')
    #                         match result.type:
    #                             case Type.BOOL:
    #                                 i = bool(int(i))
    #                             case Type.INT:
    #                                 i = int(i)
    #                             case Type.REAL:
    #                                 i = float(i)
    #                         mem[result] = i
    #                     except ValueError:
    #                         print('Entrada de dados inválida! Interpretação encerrada.')
    #                         return
    #                 case Operator.MOVE:
    #                     mem[result] = value1
    #                 case _:
    #                     mem[result] = IR.operate(op, value1, value2)


    #         #TRANSIÇÃO DE BLOCOS
    #         bb_prev = bb
    #         bb = bb_next
