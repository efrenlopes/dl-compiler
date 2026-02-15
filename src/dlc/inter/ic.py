from dlc.lex.tag import Tag
from dlc.tree.ast import AST
from dlc.semantic.type import Type
from dlc.inter.operator import Operator
from dlc.inter.operand import Operand, Temp, Const, Label
from dlc.inter.instr import Instr
from dlc.inter.basic_block import BasicBlock
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


class IC(Visitor):
    
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
        self.__instr = []
        self.__label_map = {}
        self.__label_bb_map = {}
        self.__var_temp_map = {}
        self.__bb_sequence = [BasicBlock()]
        ast.root.accept(self)

    def __iter__(self):
        return iter(self.__instr)
    
    def __len__(self):
        return len(self.__instr)
    
    def __getitem__(self, index):
        return self.__instr[index]

    


    def __bb_from_label(self, label):
        if label not in self.__label_bb_map:
            self.__label_bb_map[label] = BasicBlock()
        return self.__label_bb_map[label]



    def add_instr(self, instr: Instr):
        bb = self.__bb_sequence[-1]
        instr_prev = bb.instructions[-1] if bb.instructions else None

        # 1. Decidir se precisamos trocar de bloco ANTES de processar a instrução
        if instr.op == Operator.LABEL:
            bb_new = self.__bb_from_label(instr.result)
            # Se o bloco atual está vazio, apenas substitui (resolve o bb0 do init)
            if not bb.instructions:
                self.__bb_sequence[-1] = bb_new
            else:
                # Só conecta se o bloco anterior não terminou em GOTO
                if instr_prev and instr_prev.op != Operator.GOTO:
                    bb.add_successor(bb_new)
                self.__bb_sequence.append(bb_new)
            bb = bb_new

        # Se a anterior foi um salto, a instrução ATUAL (não sendo label) precisa de um novo bloco
        elif instr_prev and instr_prev.op in (Operator.GOTO, Operator.IF, Operator.IFFALSE):
            bb_new = BasicBlock()
            # Se era um IF, o bloco novo é o caminho "falso" (fall-through)
            if instr_prev.op != Operator.GOTO:
                bb.add_successor(bb_new)
            self.__bb_sequence.append(bb_new)
            bb = bb_new

        # 2. Agora que estamos no bloco correto, processamos a instrução
        if instr.op in (Operator.GOTO, Operator.IF, Operator.IFFALSE):
            target_bb = self.__bb_from_label(instr.result)
            bb.add_successor(target_bb)

        bb.instructions.append(instr)




    def plot(self):
        from graphviz import Digraph
        dot = Digraph()
        dot.attr(fontname="consolas")
        for bb in self.__bb_sequence:
            code = [str(i) for i in bb]
            code.insert(0, '-----')
            code.insert(0, str(bb))
            dot.node(str(bb), '\n'.join(code), shape="box")
            for s in bb.successors:
                dot.edge(str(bb), str(s))
        dot.render('out/teste_fluxo', view=True) 





    def __str__(self):
        tac = []
        for bb in self.__bb_sequence:
            for instr in bb:
                tac.append(str(instr))
        return '\n'.join(tac)

    # def __str__(self):
    #     tac = []
    #     for instr in self.__instr:
    #         tac.append(str(instr))
    #     return '\n'.join(tac)




    def visit_program_node(self, node: ProgramNode):
        L0 = Label()
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, L0))
        node.stmt.accept(self)
    

    def visit_block_node(self, node: BlockNode):
        for stmt in node.stmts:
            stmt.accept(self)
        
    
    def visit_decl_node(self, node: DeclNode):
        pass
        

    def visit_assign_node(self, node: AssignNode):
        arg = node.expr.accept(self)

        if (node.var.name, node.var.scope) not in self.__var_temp_map:
            temp = Temp(node.var.type)
            self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        
        temp = node.var.accept(self)
        self.add_instr(Instr(Operator.MOVE, arg, Operand.EMPTY, temp))


    def visit_var_node(self, node: VarNode):
        return self.__var_temp_map[(node.name, node.scope)]        




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
            lbl_true = Label()
            lbl_false = Label()
            lbl_end = Label()
            temp = Temp(Type.BOOL)

            #tests
            arg1 = node.expr1.accept(self)
            self.add_instr(Instr(Operator.IF, arg1, EMPTY, lbl_true))
            arg2 = node.expr2.accept(self)
            self.add_instr(Instr(Operator.IF, arg2, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_false))
            #true
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
            #self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_end))
        
        
        elif node.token.tag == Tag.AND:
            #labels
            lbl_false = Label()
            lbl_true = Label()
            lbl_end = Label()
            temp = Temp(Type.BOOL)

            #tests
            arg1 = node.expr1.accept(self)
            self.add_instr(Instr(Operator.IFFALSE, arg1, EMPTY, lbl_false))
            arg2 = node.expr2.accept(self)
            self.add_instr(Instr(Operator.IFFALSE, arg2, EMPTY, lbl_false))
                #self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_true))
            #true
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
                #self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_end))            
        else:
            arg1 = node.expr1.accept(self)
            arg2 = node.expr2.accept(self)
            temp = Temp(node.type)              
            self.add_instr(Instr(IC.__OP_MAP[node.operator], arg1, arg2, temp))
        
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
        lbl_out = Label()
        #test
        self.add_instr(Instr(Operator.IFFALSE, arg, Operand.EMPTY, lbl_out))
        #true
        node.stmt.accept(self)
            #self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_out))
        #out
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_out))


    def visit_else_node(self, node: ElseNode):
        arg = node.expr.accept(self)
        lbl_else = Label()
        lbl_out = Label()
        #test
        self.add_instr(Instr(Operator.IFFALSE, arg, Operand.EMPTY, lbl_else))
        #if-stmt
        node.stmt1.accept(self)
        self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_out))
        #else-stmt
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_else))
        node.stmt2.accept(self)
            #self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_out))
        #out
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_out))



    def visit_while_node(self, node: WhileNode):
        lbl_begin = Label()
        lbl_end = Label()
        #test
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_begin))
        arg = node.expr.accept(self)
        self.add_instr(Instr(Operator.IFFALSE, arg, Operand.EMPTY, lbl_end))
        #true
        node.stmt.accept(self)
        self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_begin))
        #end
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_end))

    
    def visit_write_node(self, node: WriteNode):
        arg = node.expr.accept(self)
        self.add_instr(Instr(Operator.PRINT, arg, Operand.EMPTY, Operand.EMPTY))


    def visit_read_node(self, node: ReadNode):
        if (node.var.name, node.var.scope) not in self.__var_temp_map:
            temp = Temp(node.var.type)
            self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        temp = node.var.accept(self)
        self.add_instr(Instr(Operator.READ, Operand.EMPTY, Operand.EMPTY, temp))


    
        

    def update_label_index(self):
        for i, instr in enumerate(self.__instr):
            if instr.op == Operator.LABEL:
                self.__label_map[instr.result] = i
    
    def label_index(self, label: Label):
        return self.__label_map[label]




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
        Operator.PLUS: lambda a: + a,
        Operator.MINUS: lambda a: - a,
        Operator.NOT: lambda a: not a,
        Operator.CONVERT: lambda a: float(a)
    }

    @staticmethod
    def operate(op: Operator, value1, value2):
        value = IC.OPS[op](value1, value2)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value

    @staticmethod
    def operate_unary(op: Operator, value):
        value = IC.OPS[op](value)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value

    def interpret(self):
        self.update_label_index()
        vars = {}
                
        def get_value(arg):
            if arg.is_temp:
                return vars[arg]
            if arg.is_const:
                return arg.value

        index = 0
        while True:
            if index >= len(self.__instr):
                break  

            op = self.__instr[index].op
            result = self.__instr[index].result
            value1 = get_value(self.__instr[index].arg1)
            value2 = get_value(self.__instr[index].arg2)
            
            match op:
                case Operator.LABEL:
                    pass
                case Operator.IF:
                    if value1:                    
                        index = self.__label_map[result]                    
                        continue
                case Operator.IFFALSE:
                    if not value1:
                        index = self.__label_map[result]
                        continue
                case Operator.GOTO:
                    index = self.__label_map[result]
                    continue
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
                        vars[result] = i
                    except ValueError:
                        print('Entrada de dados inválida! Interpretação encerrada.')
                        return
                case Operator.CONVERT | Operator.PLUS | Operator.MINUS | Operator.NOT:
                    vars[result] = IC.operate_unary(op, value1)
                case Operator.MOVE:
                    vars[result] = value1
                case _:
                    vars[result] = IC.operate(op, value1, value2)
                
            index += 1
