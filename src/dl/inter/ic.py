from dl.lex.tag import Tag
from dl.tree.ast import AST
from dl.semantic.type import Type
from dl.inter.operand import Op, Temp, Const, Label
from dl.inter.instr import Instr
from dl.tree.nodes import Visitor, ProgramNode, BlockNode, DeclNode, AssignNode, IfNode, ConvertNode, VarNode, BinaryNode
from ctypes import c_int32, c_double


class IC(Visitor):
    
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
        self.add_instr(Instr('=', arg, Op.EMPTY, temp))


    def visit_var_node(self, node: VarNode):
        return self.__var_temp_map[(node.name, node.scope)]        



    def visit_if_node(self, node): pass
    
    def visit_write_node(self, node): pass
    
    def visit_literal_node(self, node): pass
    
    def visit_binary_node(self, node): pass
    
    def visit_convert_node(self, node): pass


        
    
    # def visit_if_node(self, node: IfNode):
    #     arg = node.expr.accept(self)
    #     lbl_end = Label()
    #     #test
    #     self.add_instr(Instr('iffalse', arg, Op.EMPTY, lbl_end))
    #     #true
    #     node.stmt.accept(self)
    #     self.add_instr(Instr('goto', Op.EMPTY, Op.EMPTY, lbl_end))
    #     #end
    #     self.add_instr(Instr('label', Op.EMPTY, Op.EMPTY, lbl_end))
        
    
    # def visit_write_node(self, node: ConvertNode):
    #     arg = node.expr.accept(self)
    #     self.add_instr(Instr('print', arg, Op.EMPTY, Op.EMPTY))

    
    # def visit_literal_node(self, node):
    #     type = Type.tag_to_type(node.token.tag)
    #     const = Const(type, node.value)
    #     return const

    
    # def visit_binary_node(self, node: BinaryNode):
    #     arg1 = node.expr1.accept(self)
    #     arg2 = node.expr2.accept(self)
    #     temp = Temp(node.type)
    #     EMPTY = Op.EMPTY
        
    #     if node.token.tag == Tag.OR:
    #         #labels
    #         lbl_true = Label()
    #         lbl_false = Label()
    #         lbl_end = Label()
    #         #tests
    #         self.add_instr(Instr('if', arg1, EMPTY, lbl_true))
    #         self.add_instr(Instr('if', arg2, EMPTY, lbl_true))
    #         self.add_instr(Instr('goto', EMPTY, EMPTY, lbl_false))
    #         #true
    #         self.add_instr(Instr('label', EMPTY, EMPTY, lbl_true))
    #         self.add_instr(Instr('=', Const(Type.BOOL, True), EMPTY, temp))
    #         self.add_instr(Instr('goto', EMPTY, EMPTY, lbl_end))
    #         #false
    #         self.add_instr(Instr('label', EMPTY, EMPTY, lbl_false))
    #         self.add_instr(Instr('=', Const(Type.BOOL, False), EMPTY, temp))
    #         self.add_instr(Instr('goto', EMPTY, EMPTY, lbl_end))
    #         #end
    #         self.add_instr(Instr('label', EMPTY, EMPTY, lbl_end))
    #     else:   
    #         self.add_instr(Instr(node.operator, arg1, arg2, temp))
        
    #     return temp
        
    
    # def visit_convert_node(self, node: ConvertNode):
    #     arg = node.expr.accept(self)
    #     temp = Temp(node.type)
    #     self.add_instr(Instr('convert', arg, Op.EMPTY, temp))        
    #     return temp
        

    # def update_label_index(self):
    #     for i, instr in enumerate(self.__instr):
    #         if instr.op == 'label':
    #             self.__label_map[instr.result] = i
    
    # def label_index(self, label: str):
    #     return self.__label_map[label]


    # OPS = {
    #     '+': lambda a, b: a + b,
    #     '-': lambda a, b: a - b,
    #     '*': lambda a, b: a * b,
    #     '==': lambda a, b: a == b,
    #     '<': lambda a, b: a < b,
    #     '>': lambda a, b: a > b,
    #     '|': lambda a, b: a or b
    # }

    # @staticmethod
    # def operate(op: str, value1, value2):
    #     value = IC.OPS[op](value1, value2)
    #     if isinstance(value, int):
    #         return c_int32(value).value
    #     elif isinstance(value, float):
    #         return c_double(value).value
    #     elif isinstance(value, bool):
    #         return value
        

    # def interpret(self):
    #     self.update_label_index()
    #     vars = {}
                
    #     def get_value(arg):
    #         if arg.is_temp:
    #             return vars[arg]
    #         if arg.is_const:
    #             return arg.value

    #     index = 0
    #     while True:
    #         if index >= len(self.__instr):
    #             break  

    #         op = self.__instr[index].op
    #         result = self.__instr[index].result
    #         value1 = get_value(self.__instr[index].arg1)
    #         value2 = get_value(self.__instr[index].arg2)
            
    #         if op == 'label':
    #             pass
    #         elif op == 'if':
    #             if value1:                    
    #                 index = self.__label_map[result]                    
    #                 continue
    #         elif op == 'iffalse':
    #             if not value1:
    #                 index = self.__label_map[result]
    #                 continue
    #         elif op == 'goto':
    #             index = self.__label_map[result]
    #             continue
    #         elif op == 'print':
    #             print('output:', value1)
    #         elif op == 'convert':
    #             vars[result] = float(value1)
    #         elif op == '=':
    #             vars[result] = value1
    #         else:
    #             vars[result] = IC.operate(op, value1, value2)
                
    #         index += 1        
