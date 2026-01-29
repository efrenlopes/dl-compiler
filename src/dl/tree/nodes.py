from abc import ABC, abstractmethod
from dl.lex.tag import Tag
from dl.lex.lexer import Token
from dl.tree.visitor import Visitor


class Node(ABC):
    
    def __init__(self, token: Token):
        self.token = token
    
    @property
    def line(self):
        return self.token.line
    
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass
    
    def __iter__(self):
        for attr in vars(self).values():
            if isinstance(attr, Node):
                yield attr
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, Node):
                        yield item

    def __len__(self):
        return sum(1 for _ in self)

    def __repr__(self):
        return f'<{self.__class__.__name__}:{str(self)}>'



class ExprNode(Node):
    def __init__(self, token: Token):
        super().__init__(token)
        self.type = None



class VarNode(ExprNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.scope = None
        
    @property
    def name(self):
        return self.token.lexeme
        
    def accept(self, visitor: Visitor):
        return visitor.visit_var_node(self)
    
    def __str__(self):
        if self.type:
            return f'{self.name}:{self.type}'
        return self.name



class LiteralNode(ExprNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.value = None

    @property
    def raw_value(self):
        if self.token.tag == Tag.LIT_TRUE:
            return Tag.LIT_TRUE.value
        elif self.token.tag == Tag.LIT_FALSE:
            return Tag.LIT_FALSE.value
        else:
            return self.token.lexeme
    
    def accept(self, visitor: Visitor):
        return visitor.visit_literal_node(self)
    
    def __str__(self):
        if self.type:
            return f'{self.value}:{self.type}'
        return self.raw_value



class BinaryNode(ExprNode):
    def __init__(self, token: Token, expr1: ExprNode, expr2: ExprNode):
        super().__init__(token)
        self.expr1 = expr1
        self.expr2 = expr2

    @property
    def operator(self):
        return self.token.tag
    
    def accept(self, visitor: Visitor):
        return visitor.visit_binary_node(self)

    def __str__(self):
        if self.type:
            return f'{self.operator.value}:{self.type}'
        return self.operator.value



class ConvertNode(ExprNode):
    def __init__(self, expr: ExprNode):
        super().__init__(None)
        self.expr = expr

    @property
    def operator(self):
        return Tag.CONVERT
    
    def accept(self, visitor: Visitor):
        return visitor.visit_convert_node(self)

    def __str__(self):
        if self.type:
            return f'{Tag.CONVERT.name}:{self.type}'        
        return Tag.CONVERT.name



class StmtNode(Node):
    
    def __init__(self, token: Token):
        super().__init__(token)
        
    def __str__(self):
        return f'[{self.__class__.__name__}]'

    def __repr__(self):
        return f'<{str(self)}>'



class ProgramNode(StmtNode):
    def __init__(self, token: Token, name: str, stmt: StmtNode):
        super().__init__(token)
        self.name = name
        self.stmt = stmt
        
    def accept(self, visitor: Visitor):
        return visitor.visit_program_node(self)




class BlockNode(StmtNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.stmts = []

    def add_stmt(self, stmt: StmtNode):
        self.stmts.append(stmt)

    def accept(self, visitor: Visitor):
        return visitor.visit_block_node(self)




class DeclNode(StmtNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.vars = []
    
    def add_var(self, var: VarNode):
        self.vars.append(var)
        
    def accept(self, visitor: Visitor):
        return visitor.visit_decl_node(self)




class AssignNode(StmtNode):
    def __init__(self, token: Token, var: VarNode, expr: ExprNode):
        super().__init__(token)
        self.var = var
        self.expr = expr

    def accept(self, visitor: Visitor):
        return visitor.visit_assign_node(self)




class IfNode(StmtNode):
    def __init__(self, token: Token, expr: ExprNode, stmt: StmtNode):
        super().__init__(token)
        self.expr = expr
        self.stmt = stmt

    def accept(self, visitor: Visitor):
        return visitor.visit_if_node(self)


class ElseNode(StmtNode):
    def __init__(self, token: Token, expr: ExprNode, stmt1: StmtNode, stmt2: StmtNode):
        super().__init__(token)
        self.expr = expr
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def accept(self, visitor: Visitor):
        return visitor.visit_else_node(self)


class WhileNode(StmtNode):
    def __init__(self, token: Token, expr: ExprNode, stmt: StmtNode):
        super().__init__(token)
        self.expr = expr
        self.stmt = stmt

    def accept(self, visitor: Visitor):
        return visitor.visit_while_node(self)



class WriteNode(StmtNode):
    def __init__(self, token: Token, expr: ExprNode):
        super().__init__(token)
        self.expr = expr

    def accept(self, visitor: Visitor):
        return visitor.visit_write_node(self)



class ReadNode(StmtNode):
    def __init__(self, token: Token, var: VarNode):
        super().__init__(token)
        self.var = var

    def accept(self, visitor: Visitor):
        return visitor.visit_read_node(self)
