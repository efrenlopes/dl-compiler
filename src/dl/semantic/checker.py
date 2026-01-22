from dl.lex.tag import Tag
from dl.semantic.env import Env, SymbolInfo
from dl.semantic.type import Type
from dl.tree.ast import AST
from dl.tree.nodes import Visitor, ProgramNode, BlockNode, DeclNode, AssignNode, IfNode, WriteNode, VarNode, LiteralNode, BinaryNode, ConvertNode, ExprNode


class Checker(Visitor):
    
    def __init__(self, ast: AST):
        self.__env_top = Env()
        self.has_semantic_error = False
        ast.root.accept(self)


    def __error(self, line: int, msg: str):
        self.has_semantic_error = True
        print(f'Erro semântico na linha {line}: {msg}')  
        

    def visit_program_node(self, node: ProgramNode):
        node.stmt.accept(self)
        

    def visit_block_node(self, node: BlockNode):
        saved_env = self.__env_top
        self.__env_top = Env(self.__env_top)
        for stmt in node.stmts:
            stmt.accept(self)        
        for var in self.__env_top.var_list():
            info = self.__env_top.get_local(var)
            if not info.used:
                print(f"Aviso: variável {var} declarada na linha {info.declaration_line} mas não usada")
        self.__env_top = saved_env


    def visit_decl_node(self, node: DeclNode):
        var_name = node.var.name
        if self.__env_top.get_local(var_name) is None:
            node.var.type = Type.tag_to_type(node.token.tag)
            node.var.scope = self.__env_top.number
            self.__env_top.put(var_name, SymbolInfo(node.var.type, node.var.scope, node.line))
        else:
            self.__error(node.line, f'"{var_name}" já declarada!')


    @staticmethod
    def assign_type_rules(var_type: Type, expr_type: Type):
        if not var_type or not expr_type:
            return None
        if var_type == expr_type:
            return var_type
        elif var_type.is_numeric and expr_type.is_numeric:
            if var_type.rank > expr_type.rank:
                return var_type
        return None


    def visit_assign_node(self, node: AssignNode):
        #var
        info = self.__env_top.get(node.var.name)
        if not info:
            self.__error(node.var.line, f'{node.var.name} não declarada!')
        else:
            node.var.type = info.type
            node.var.scope = info.scope
            info.initialized = True
        #expr
        node.expr.accept(self)
        #Erro
        if not Checker.is_assign_types_compatible(node.var.type, node.expr.type):
            self.__error(node.line, 'Tipo da variável incompatível com o tipo da expressão')
        else:            
            #widen
            node.expr = Checker.widening(node.expr, node.var.type)
            info.initialized = True

    @staticmethod
    def is_assign_types_compatible(var_type: Type, expr_type: Type):
        if not var_type or not expr_type:
            return False
        if var_type == expr_type:
            return True
        return (var_type.is_numeric and expr_type.is_numeric and 
                var_type.rank > expr_type.rank)

    @staticmethod
    def widening(expr: ExprNode, type: Type):
        if expr.type == type:
            return expr
        w = ConvertNode(expr)
        w.type = type
        return w


    def visit_if_node(self, node: IfNode):
        pass        
        
    def visit_write_node(self, node: WriteNode):
        pass
    
    
    def visit_var_node(self, node: VarNode):
        info = self.__env_top.get(node.name)
        if not info:
            self.__error(node.line, f'{node.name} não declarada!')
        else:
            node.type = info.type
            node.scope = info.scope
            info.used = True
            if not info.initialized:
                    self.__error(node.line, f'{node.name} não inicializada!')    


    def visit_literal_node(self, node: LiteralNode):
        node.type = Type.tag_to_type(node.token.tag)
        match node.type:
            case Type.BOOL:
                node.value = (node.token.tag == Tag.LIT_TRUE)
            case Type.INT:
                value = int(node.raw_value)
                if Type.MIN_INT <= value <= Type.MAX_INT:
                    node.value = value
                else:
                    self.__error(node.line, f'O valor {value} está fora da faixa de valores dos inteiros')
            case Type.REAL:
                value = float(node.raw_value)
                if Type.MIN_REAL <= value <= Type.MAX_REAL:
                    node.value = value
                else:
                    self.__error(node.line, f'O valor {value} está fora da faixa de valores dos reais')            


    def visit_binary_node(self, node: BinaryNode):
        pass        
    
    def visit_convert_node(self, node: ConvertNode):
        pass
