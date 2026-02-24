from dlc.inter.basic_block import BasicBlock
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operand import SSAConst, SSALabel, SSAOperand, SSATemp
from dlc.inter_ssa.ssa_operator import SSAOperator
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


class SSA_IC(Visitor):
    
    __OP_MAP = {
        Tag.SUM: SSAOperator.SUM,
        Tag.SUB: SSAOperator.SUB,
        Tag.MUL: SSAOperator.MUL,
        Tag.DIV: SSAOperator.DIV,
        Tag.MOD: SSAOperator.MOD,
        Tag.POW: SSAOperator.POW,
        Tag.EQ : SSAOperator.EQ,
        Tag.NE : SSAOperator.NE,
        Tag.LT: SSAOperator.LT,
        Tag.LE: SSAOperator.LE,
        Tag.GT: SSAOperator.GT,
        Tag.GE: SSAOperator.GE
    }

    def __init__(self, ast: AST):
        self.__var_temp_map = {}
        self.label_bb_map = {}
        self.__comments = {}

        L0 = SSALabel()
        bb_entry = BasicBlock()
        self.label_bb_map[L0] = bb_entry
        self.__bb_current = bb_entry
        self.bb_sequence = []
        self.add_instr( SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, L0 ))
        
        ast.root.accept(self)


    def __iter__(self):
        for bb in self.bb_sequence:
            for instr in bb:
                yield instr
    

    def bb_from_label(self, label):
        if label not in self.label_bb_map:
            self.label_bb_map[label] = BasicBlock()
        return self.label_bb_map[label]


    def add_instr(self, instr: SSAInstr, comment: str=None):
        match instr.op:
            case SSAOperator.LABEL:
                new_bb = self.bb_from_label(instr.result)
                self.bb_sequence.append(new_bb)
                self.__bb_current = new_bb

            case SSAOperator.GOTO:
                bb_target = self.bb_from_label(instr.result)
                self.__bb_current.add_successor(bb_target)
            
            case SSAOperator.IF:
                bb_target = self.bb_from_label(instr.arg2)
                bb_fall = self.bb_from_label(instr.result)
                self.__bb_current.add_successor(bb_target)
                self.__bb_current.add_successor(bb_fall)

        self.__bb_current.instructions.append(instr)
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
        dot.render('out/teste_fluxo', view=True) 





    def __str__(self):
        tac = []
        for bb in self.bb_sequence:
            tac.append(str(bb))
            for instr in bb:
                comment = self.__comments.get(instr)
                if comment:
                    tac.append(f'   {str(instr):<20} \t\t#{comment}')
                else:
                    tac.append(f'   {instr}')
        return '\n'.join(tac)


    def visit_program_node(self, node: ProgramNode):
        node.stmt.accept(self)
    

    def visit_block_node(self, node: BlockNode):
        for stmt in node.stmts:
            stmt.accept(self)
        
    
    def visit_decl_node(self, node: DeclNode):
        for var in node.vars:
            temp = SSATemp(var.type, True)
            key = (var.name, var.scope)
            self.__var_temp_map[key] = temp
            comment = f'var {var.name} [scope={var.scope}]'
            self.add_instr( SSAInstr(SSAOperator.ALLOCA, SSAOperand.EMPTY, SSAOperand.EMPTY, temp), comment)
        

    def visit_assign_node(self, node: AssignNode):
        arg = node.expr.accept(self)
        key = (node.var.name, node.var.scope)
        temp = self.__var_temp_map[key]
        self.add_instr(SSAInstr(SSAOperator.STORE, arg, SSAOperand.EMPTY, temp))


    def visit_var_node(self, node: VarNode):
        temp = SSATemp(node.type)
        key = (node.name, node.scope)
        var = self.__var_temp_map[key]
        self.add_instr(SSAInstr(SSAOperator.LOAD, var, SSAOperand.EMPTY, temp))
        return temp




    def visit_literal_node(self, node: LiteralNode):
        return SSAConst(node.type, node.value)


    def visit_convert_node(self, node: ConvertNode):
        arg = node.expr.accept(self)
        temp = SSATemp(node.type)
        self.add_instr(SSAInstr(SSAOperator.CONVERT, arg, SSAOperand.EMPTY, temp))        
        return temp


    def visit_binary_node(self, node: BinaryNode):
        EMPTY = SSAOperand.EMPTY
        
        if node.token.tag == Tag.OR:
            #labels
            lbl_test_b = SSALabel()
            lbl_true = SSALabel()
            lbl_false = SSALabel()
            lbl_out = SSALabel()
            temp = SSATemp(Type.BOOL)

            #Test-A
            arg1 = node.expr1.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg1, lbl_true, lbl_test_b))
            #Test-B
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_test_b))
            arg2 = node.expr2.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg2, lbl_true, lbl_false))
            #Block-True
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, True), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
            #Block-False
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, False), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
            #Out
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_out))
        
        elif node.token.tag == Tag.AND:
            #labels
            lbl_test_b = SSALabel()
            lbl_false = SSALabel()
            lbl_true = SSALabel()
            lbl_out = SSALabel()
            temp = SSATemp(Type.BOOL)

            #Test-A
            arg1 = node.expr1.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg1, lbl_test_b, lbl_false))
            #Test-B
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_test_b))
            arg2 = node.expr2.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg2, lbl_true, lbl_false))
            #true
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, True), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
            #false
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, False), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
            #end
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_out))
        else:
            arg1 = node.expr1.accept(self)
            arg2 = node.expr2.accept(self)
            temp = SSATemp(node.type)              
            self.add_instr(SSAInstr(SSA_IC.__OP_MAP[node.operator], arg1, arg2, temp))
        
        return temp




    def visit_unary_node(self, node: UnaryNode):
        arg = node.expr.accept(self)
        temp = SSATemp(node.type)
        
        match node.token.tag:
            case Tag.SUM:
                op = SSAOperator.PLUS
            case Tag.SUB:
                op = SSAOperator.MINUS
            case Tag.NOT:
                op = SSAOperator.NOT
        
        self.add_instr(SSAInstr(op, arg, SSAOperand.EMPTY, temp))
        return temp



    def visit_if_node(self, node: IfNode):
        arg = node.expr.accept(self)
        lbl_true = SSALabel()
        lbl_out = SSALabel()
        EMPTY = SSAOperand.EMPTY

        #Test
        self.add_instr(SSAInstr(SSAOperator.IF, arg, lbl_true, lbl_out))
        #Block-True
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
        node.stmt.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
        #out
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_out))


    def visit_else_node(self, node: ElseNode):
        arg = node.expr.accept(self)
        lbl_true = SSALabel()
        lbl_false = SSALabel()
        lbl_out = SSALabel()
        EMPTY = SSAOperand.EMPTY

        #Test
        self.add_instr(SSAInstr(SSAOperator.IF, arg, lbl_true, lbl_false))
        #if-stmt
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
        node.stmt1.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
        #else-stmt
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_false))
        node.stmt2.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_out))
        #out
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_out))



    def visit_while_node(self, node: WhileNode):
        lbl_entry = SSALabel()
        lbl_body = SSALabel()
        lbl_exit = SSALabel()
        EMPTY = SSAOperand.EMPTY
        #Test
        self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_entry))
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_entry))
        arg = node.expr.accept(self)
        self.add_instr(SSAInstr(SSAOperator.IF, arg, lbl_body, lbl_exit))
        #true
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_body))
        node.stmt.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_entry))
        #end
        self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_exit))

    
    def visit_write_node(self, node: WriteNode):
        arg = node.expr.accept(self)
        self.add_instr(SSAInstr(SSAOperator.PRINT, arg, SSAOperand.EMPTY, SSAOperand.EMPTY))


    def visit_read_node(self, node: ReadNode):
        #if (node.var.name, node.var.scope) not in self.__var_temp_map:
        #    temp = SSATemp(node.var.type)
        #    self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        temp = self.__var_temp_map[(node.var.name, node.var.scope)]
        self.add_instr(SSAInstr(SSAOperator.READ, SSAOperand.EMPTY, SSAOperand.EMPTY, temp))





    OPS = {
        SSAOperator.SUM: lambda a, b: a + b,
        SSAOperator.SUB: lambda a, b: a - b,
        SSAOperator.MUL: lambda a, b: a * b,
        SSAOperator.DIV: lambda a, b: a / b if isinstance(a, float) else a//b,
        SSAOperator.MOD: lambda a, b: a % b,
        SSAOperator.POW: lambda a, b: a ** b,
        SSAOperator.EQ: lambda a, b: a == b,
        SSAOperator.NE: lambda a, b: a != b,
        SSAOperator.LT: lambda a, b: a < b,
        SSAOperator.LE: lambda a, b: a <= b,
        SSAOperator.GT: lambda a, b: a > b,
        SSAOperator.GE: lambda a, b: a >= b,
        SSAOperator.PLUS: lambda a, _: + a,
        SSAOperator.MINUS: lambda a, _: - a,
        SSAOperator.NOT: lambda a, _: not a,
        SSAOperator.CONVERT: lambda a, _: float(a)
    }

    @staticmethod
    def operate(op: SSAOperator, value1, value2):
        value = SSA_IC.OPS[op](value1, value2)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value

    @staticmethod
    def operate_unary(op: SSAOperator, value):
        value = SSA_IC.OPS[op](value)
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
                    case SSAOperator.PHI:
                        value = get_value( instr.arg1.paths.get(bb_prev, SSAOperand.EMPTY)) #retorna SSAOperand.EMPTY como valor padrão para o caso de PHIs inúteis
                        mem[result] = value
                    case SSAOperator.ALLOCA:
                        mem[result] = None
                    case SSAOperator.STORE:
                        mem[result] = value1
                    case SSAOperator.LOAD:
                        mem[result] = mem[instr.arg1]
                    case SSAOperator.LABEL:
                        continue
                    case SSAOperator.IF:
                        if value1:                    
                            bb_next = self.bb_from_label(instr.arg2)
                        else:
                            bb_next = self.bb_from_label(instr.result)
                    case SSAOperator.GOTO:
                        bb_next = self.bb_from_label(result)
                    case SSAOperator.PRINT:
                        if isinstance(value1, float):
                            print(f'output: {value1:.4f}')
                        else:
                            print(f'output: {int(value1)}')
                    case SSAOperator.READ:
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
                    #case SSAOperator.CONVERT | SSAOperator.PLUS | SSAOperator.MINUS | SSAOperator.NOT:
                    #    mem[result] = SSA_IC.operate(op, value1, value2)
                    case SSAOperator.MOVE:
                        mem[result] = value1
                    case _:
                        mem[result] = SSA_IC.operate(op, value1, value2)


            #TRANSIÇÃO DE BLOCOS
            bb_prev = bb
            bb = bb_next
