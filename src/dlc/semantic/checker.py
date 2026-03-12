import colorama

from dlc.lex.tag import Tag
from dlc.semantic.env import Env, SymbolInfo
from dlc.semantic.type import Type
from dlc.tree.ast import AST
from dlc.tree.nodes import (
    AssignNode,
    BinaryNode,
    BlockNode,
    ConvertNode,
    DeclNode,
    ElseNode,
    ExprNode,
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


class Checker(Visitor[None]):
    
    def __init__(self, ast: AST) -> None:
        self.__env_top = Env()
        self.had_errors = False
        ast.root.accept(self)


    def __error(self, line: int, msg: str) -> None:
        self.had_errors = True
        colorama.init()
        print(colorama.Fore.RED, end='')
        print(f'Erro semântico na linha {line}: {msg}')
        print(colorama.Style.RESET_ALL, end='')

    def __warning(self, line: int, msg: str) -> None:
        colorama.init()
        print(colorama.Fore.YELLOW, end='')
        print(f'Aviso na linha {line}: {msg}') 
        print(colorama.Style.RESET_ALL, end='')
        
        
    def visit_program_node(self, node: ProgramNode) -> None:
        node.stmt.accept(self)
        

    def visit_block_node(self, node: BlockNode) -> None:
        saved_env = self.__env_top
        self.__env_top = Env(self.__env_top)
        for stmt in node.stmts:
            stmt.accept(self)        
        for var in self.__env_top.var_list():
            info = self.__env_top.get_local(var)
            if info and not info.used:
                self.__warning(info.declaration_line,
                            f'variável "{var}" declarada mas não usada.')
        self.__env_top = saved_env


    def visit_decl_node(self, node: DeclNode) -> None:
        for var in node.vars:
            if self.__env_top.get_local(var.name) is None:
                var.type = Type.tag_to_type(node.token.tag)
                var.scope = self.__env_top.number
                self.__env_top.put(var.name, SymbolInfo(var.type, var.scope, node.line))
            else:
                self.__error(node.line, f'"{var.name}" já declarada!')


    def visit_assign_node(self, node: AssignNode) -> None:
        node.expr.accept(self)
        info = self.__env_top.get(node.var.name)
        if info:
            node.var.type = info.type
            node.var.scope = info.scope
            info.initialized = True
            if node.var.type != Type.common_type(node.var.type, node.expr.type):
                self.__error(node.line, 
                             'Tipo da variável incompatível com o tipo da expressão')
            else:            
                #widen
                node.expr = Checker.widening(node.expr, node.var.type)
        else:
            self.__error(node.var.line, f'"{node.var.name}" não declarada!')


    @staticmethod
    def widening(expr: ExprNode, type: Type) -> ExprNode:
        if expr.type == type:
            return expr
        w = ConvertNode(expr)
        w.type = type
        return w


    def visit_if_node(self, node: IfNode) -> None:
        node.expr.accept(self)
        if not node.expr.type.is_boolean:
            self.__error(node.line, 'Esperada uma expressão lógica')
        node.stmt.accept(self)


    def visit_else_node(self, node: ElseNode) -> None:
        node.expr.accept(self)
        if not node.expr.type.is_boolean:
            self.__error(node.line, 'Esperada uma expressão lógica')
        node.stmt1.accept(self)
        node.stmt2.accept(self)


    def visit_while_node(self, node: WhileNode) -> None:
        node.expr.accept(self)
        if not node.expr.type.is_boolean:
            self.__error(node.line, 'Esperada uma expressão lógica')
        node.stmt.accept(self)


    def visit_write_node(self, node: WriteNode) -> None:
        node.expr.accept(self)

    def visit_read_node(self, node: ReadNode) -> None:
        info = self.__env_top.get(node.var.name)
        if info:
            node.var.type = info.type
            node.var.scope = info.scope
            info.initialized = True
        else:
            self.__error(node.var.line, f'"{node.var.name}" não declarada!')


    def visit_var_node(self, node: VarNode) -> None:
        info = self.__env_top.get(node.name)
        if info:
            node.type = info.type
            node.scope = info.scope
            info.used = True
            if not info.initialized:
                self.__error(node.line, f'"{node.name}" não inicializada!')
        else:
            self.__error(node.line, f'"{node.name}" não declarada!')


    def visit_literal_node(self, node: LiteralNode) -> None:
        node.type = Type.tag_to_type(node.token.tag)
        match node.type:
            case Type.BOOL:
                node.value = (node.token.tag == Tag.LIT_TRUE)
            case Type.INT:
                value = int(node.raw_value)
                if Type.MIN_INT <= value <= Type.MAX_INT:
                    node.value = value
                else:
                    self.__error(node.line, 
                                 f'Valor {value} fora da faixa dos inteiros.')
            case Type.REAL:
                value = float(node.raw_value)
                if Type.MIN_REAL <= value <= Type.MAX_REAL:
                    node.value = value
                else:
                    self.__error(node.line,
                                 f'Valor {value} fora da faixa dos reais.')
            case _:
                pass



    def visit_binary_node(self, node: BinaryNode) -> None:
        node.expr1.accept(self)
        node.expr2.accept(self)
        
        t1 = node.expr1.type
        t2 = node.expr2.type
        common_type = Type.common_type(t1, t2)

        match node.operator:
            case Tag.OR | Tag.AND:
                if t1.is_boolean and t2.is_boolean:
                    node.type = Type.BOOL
            case Tag.EQ | Tag.NE:
                if common_type:
                    node.type = Type.BOOL
            case Tag.SUM | Tag.SUB | Tag.MUL | Tag.DIV | Tag.MOD | Tag.POW:
                if t1.is_numeric and t2.is_numeric:
                    node.type = common_type
            case Tag.LT | Tag.LE | Tag.GT | Tag.GE:
                if t1.is_numeric and t2.is_numeric:
                    node.type = Type.BOOL
            case _:
                pass
        
        if node.type.is_undef:
            self.__error(node.line, 
                         f'Operação "{node.operator}" com operandos inválidos.')
        else:
            node.expr1 = Checker.widening(node.expr1, common_type)
            node.expr2 = Checker.widening(node.expr2, common_type)
    


    def visit_unary_node(self, node: UnaryNode) -> None:
        node.expr.accept(self)
        type = node.expr.type

        match node.operator:
            case Tag.SUM | Tag.SUB:
                if type.is_numeric:
                    node.type = node.expr.type
            case Tag.NOT:
                if type.is_boolean:
                    node.type = node.expr.type
            case _:
                pass
        
        if node.type.is_undef:
            self.__error(node.line, 
                         f'Operação unária "{node.operator}" com operando inválido.')


    def visit_convert_node(self, node: ConvertNode) -> None:
        pass
