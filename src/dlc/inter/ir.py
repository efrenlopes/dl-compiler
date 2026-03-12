from dlc.inter.basic_block import BasicBlock
from dlc.inter.instr import Instr
from dlc.inter.operand import Const, Label, Operand, Temp
from dlc.inter.operator import Operator
from dlc.lex.tag import Tag
from dlc.semantic.type import Type
from dlc.tree.ast import AST
from dlc.tree.nodes import (
    Visitor,
    ProgramNode,
    BlockNode,
    DeclNode,
    AssignNode,
    IfNode,
    ElseNode,
    WhileNode,
    WriteNode,
    ReadNode,
    ConvertNode,
    VarNode,
    BinaryNode,
    UnaryNode,
    LiteralNode
)
from ctypes import c_int32, c_double


class IR(Visitor):
    
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

    def __init__(self, ast: AST):
        self.__var_temp_map = {}
        self.label_bb_map = {}
        self.__comments = {}

        L0 = Label()
        bb_entry = BasicBlock()
        self.label_bb_map[L0] = bb_entry
        self.__bb_current = bb_entry
        self.bb_sequence = []
        self.add_instr( Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, L0 ))
        
        ast.root.accept(self)


    def __iter__(self):
        for bb in self.bb_sequence:
            for instr in bb:
                yield instr
    

    def bb_from_label(self, label):
        return self.label_bb_map[label]

    def __bb_from_label(self, label):
        if label not in self.label_bb_map:
            self.label_bb_map[label] = BasicBlock()
        return self.label_bb_map[label]


    def add_instr(self, instr: Instr, comment: str=None):
        match instr.op:
            case Operator.LABEL:
                new_bb: BasicBlock = self.__bb_from_label(instr.result)
                new_bb.label_instr = instr
                self.bb_sequence.append(new_bb)
                self.__bb_current = new_bb
            case Operator.GOTO | Operator.IF:
                for arg in (instr.arg2, instr.result):
                    if arg.is_label:
                        bb_target = self.__bb_from_label(arg)
                        self.__bb_current.add_successor(bb_target)
                self.__bb_current.goto_instr = instr
            case Operator.PHI:
                self.__bb_current.phi_instrs.append(instr)
            case _:
                self.__bb_current.body_instrs.append(instr)

        if comment:
            self.__comments[instr] = comment




    def plot(self):
        from graphviz import Digraph
        dot = Digraph()
        dot.attr(fontname="consolas")
        for bb in self.bb_sequence:
            code = [str(i) for i in bb]
            dot.node(name=str(bb), label='\n'.join(code), shape="box", xlabel=str(bb))
            for s in bb.successors:
                dot.edge(str(bb), str(s))
            #for s in bb.predecessors:
            #    dot.edge(str(bb), str(s), color="red")
        dot.render('out/teste_fluxo', view=False) 





    def __str__(self):
        tac = []
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


    def visit_program_node(self, node: ProgramNode):
        node.stmt.accept(self)
    

    def visit_block_node(self, node: BlockNode):
        for stmt in node.stmts:
            stmt.accept(self)
        
    
    def visit_decl_node(self, node: DeclNode):
        for var in node.vars:
            temp = Temp(var.type, True)
            key = (var.name, var.scope)
            self.__var_temp_map[key] = temp
            comment = f'var {var.name} [scope={var.scope}]'
            self.add_instr( Instr(Operator.ALLOCA, Operand.EMPTY, Operand.EMPTY, temp), comment)
        

    def visit_assign_node(self, node: AssignNode):
        arg = node.expr.accept(self)
        key = (node.var.name, node.var.scope)
        temp = self.__var_temp_map[key]
        self.add_instr(Instr(Operator.STORE, arg, Operand.EMPTY, temp))


    def visit_var_node(self, node: VarNode):
        temp = Temp(node.type)
        key = (node.name, node.scope)
        var = self.__var_temp_map[key]
        self.add_instr(Instr(Operator.LOAD, var, Operand.EMPTY, temp))
        return temp




    def visit_literal_node(self, node: LiteralNode):
        return Const(node.type, node.value)


    def visit_convert_node(self, node: ConvertNode):
        arg = node.expr.accept(self)
        temp = Temp(node.type)
        self.add_instr(Instr(Operator.CONVERT, arg, Operand.EMPTY, temp))        
        return temp


    def visit_binary_node(self, node: BinaryNode):
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




    def visit_unary_node(self, node: UnaryNode):
        arg = node.expr.accept(self)
        temp = Temp(node.type)
        
        match node.token.tag:
            case Tag.SUM:
                op = Operator.PLUS
            case Tag.SUB:
                op = Operator.MINUS
            case Tag.NOT:
                op = Operator.NOT
        
        self.add_instr(Instr(op, arg, Operand.EMPTY, temp))
        return temp



    def visit_if_node(self, node: IfNode):
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


    def visit_else_node(self, node: ElseNode):
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



    def visit_while_node(self, node: WhileNode):
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

    
    def visit_write_node(self, node: WriteNode):
        arg = node.expr.accept(self)
        self.add_instr(Instr(Operator.PRINT, arg, Operand.EMPTY, Operand.EMPTY))


    def visit_read_node(self, node: ReadNode):
        #if (node.var.name, node.var.scope) not in self.__var_temp_map:
        #    temp = SSATemp(node.var.type)
        #    self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        temp = self.__var_temp_map[(node.var.name, node.var.scope)]
        self.add_instr(Instr(Operator.READ, Operand.EMPTY, Operand.EMPTY, temp))





    OPS = {
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
        Operator.PLUS: lambda a, _: + a,
        Operator.MINUS: lambda a, _: - a,
        Operator.NOT: lambda a, _: not a,
        Operator.CONVERT: lambda a, _: float(a)
    }



    @staticmethod
    def operate(op: Operator, value1, value2):
        value = IR.OPS[op](value1, value2)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value



    def interpret(self):
        mem = {}

        def get_value(arg):
            if arg.is_temp or arg.is_temp_version:
                return mem.get(arg)
            elif arg.is_const:
                return arg.value

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
                        value = get_value( instr.arg1.paths.get(bb_prev) ) #value = get_value( instr.arg1.paths.get(bb_prev, Operand.EMPTY)) #retorna Operand.EMPTY como valor padrão para o caso de PHIs inúteis
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
                            bb_next = self.bb_from_label(instr.arg2)
                        else:
                            bb_next = self.bb_from_label(instr.result)
                    case Operator.GOTO:
                        bb_next = self.bb_from_label(result)
                    case Operator.PRINT:
                        if isinstance(value1, float):
                            print(f'output: {value1:.4f}')
                        else:
                            print(f'output: {int(value1)}')
                    case Operator.READ:
                        try:
                            i = input('input: ')
                            match result.type:
                                case Type.BOOL:
                                    i = bool(int(i))
                                case Type.INT:
                                    i = int(i)
                                case Type.REAL:
                                    i = float(i)
                            mem[result] = i
                        except ValueError:
                            print('Entrada de dados inválida! Interpretação encerrada.')
                            return
                    case Operator.MOVE:
                        mem[result] = value1
                    case _:
                        mem[result] = IR.operate(op, value1, value2)


            #TRANSIÇÃO DE BLOCOS
            bb_prev = bb
            bb = bb_next
