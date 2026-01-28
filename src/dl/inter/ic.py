from dl.lex.tag import Tag
from dl.tree.ast import AST
from dl.semantic.type import Type
from dl.inter.operator import Operator
from dl.inter.operand import Operand, Temp, Const, Label
from dl.inter.instr import Instr
from dl.tree.nodes import (
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
        Tag.EQ : Operator.EQ,
        Tag.NE : Operator.NE,
        Tag.LT: Operator.LT,
        Tag.LE: Operator.LE,
        Tag.GT: Operator.GT,
        Tag.GE: Operator.GE
    }

    def __init__(self, ast: AST = None):
        self.__instr = []
        self.__label_map = {}
        self.__var_temp_map = {}
        if ast:
            ast.root.accept(self)

    def __iter__(self):
        return iter(self.__instr)
    
    def __len__(self):
        return len(self.__instr)
    
    def __getitem__(self, index):
        return self.__instr[index]

    def add_instr(self, instr: Instr):
        self.__instr.append( instr )

    def __str__(self):
        tac = []
        for instr in self.__instr:
            tac.append(str(instr))
        return '\n'.join(tac)




    def visit_program_node(self, node: ProgramNode):
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
        arg1 = node.expr1.accept(self)
        arg2 = node.expr2.accept(self)
        temp = Temp(node.type)
        EMPTY = Operand.EMPTY
        
        if node.token.tag == Tag.OR:
            #labels
            lbl_true = Label()
            lbl_false = Label()
            lbl_end = Label()
            #tests
            self.add_instr(Instr(Operator.IF, arg1, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.IF, arg2, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_false))
            #true
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_end))
        elif node.token.tag == Tag.AND:
            #labels
            lbl_false = Label()
            lbl_true = Label()
            lbl_end = Label()
            #tests
            self.add_instr(Instr(Operator.IFFALSE, arg1, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.IFFALSE, arg2, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_true))
            #true
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, True), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(Instr(Operator.MOVE, Const(Type.BOOL, False), EMPTY, temp))
            self.add_instr(Instr(Operator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(Instr(Operator.LABEL, EMPTY, EMPTY, lbl_end))            
        else:   
            self.add_instr(Instr(IC.__OP_MAP[node.operator], arg1, arg2, temp))
        
        return temp




    def visit_if_node(self, node: IfNode):
        arg = node.expr.accept(self)
        lbl_out = Label()
        #test
        self.add_instr(Instr(Operator.IFFALSE, arg, Operand.EMPTY, lbl_out))
        #true
        node.stmt.accept(self)
        self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_out))
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
        self.add_instr(Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, lbl_out))
        #out
        self.add_instr(Instr(Operator.LABEL, Operand.EMPTY, Operand.EMPTY, lbl_out))

        # expr = self._expr.gen_inter_code()
        # lbl_true = emitter.new_label()
        # lbl_false = emitter.new_label()
        # lbl_out = emitter.new_label()
        # #Vai para lbl_true caso verdade e para lbl_false caso contrário
        # emitter.emit_if_goto(expr.as_inter_code(), lbl_true)
        # emitter.emit_goto(lbl_false)
        # #Processa o corpo do IF e vai para lbl_out
        # emitter.emit_label(lbl_true)
        # self._stmt1.gen_inter_code()
        # emitter.emit_goto(lbl_out)
        # #Processa o corpo do ELSE
        # emitter.emit_label(lbl_false)
        # self._stmt2.gen_inter_code()
        # #Label para fora do IF-ELSE
        # emitter.emit_label(lbl_out)


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
        Operator.EQ: lambda a, b: a == b,
        Operator.NE: lambda a, b: a != b,
        Operator.LT: lambda a, b: a < b,
        Operator.LE: lambda a, b: a <= b,
        Operator.GT: lambda a, b: a > b,
        Operator.GE: lambda a, b: a >= b,
    }

    @staticmethod
    def operate(op: str, value1, value2):
        value = IC.OPS[op](value1, value2)
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
                        print('Entrada de dados inválida! Programa encerrado.')
                case Operator.CONVERT:
                    vars[result] = float(value1)
                case Operator.MOVE:
                    vars[result] = value1
                case _:
                    vars[result] = IC.operate(op, value1, value2)
                
            index += 1
