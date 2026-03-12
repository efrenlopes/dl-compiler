from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any, TypeVar

from dlc.lex.lexer import Token
from dlc.lex.tag import Tag
from dlc.semantic.type import Type
from dlc.tree.visitor import Visitor

T = TypeVar('T')

class Node(ABC):

    def __init__(self, token: Token) -> None:
        self.token = token
    
    @property
    def line(self) -> int:
        return self.token.line
    
    @abstractmethod
    def accept(self, visitor: Visitor[T]) -> T:
        pass
    
    def __iter__(self) -> Generator[Node, None, None]:
        for attr in vars(self).values():
            if isinstance(attr, Node):
                yield attr
            elif isinstance(attr, list):
                for item in attr: # type: ignore
                    if isinstance(item, Node):
                        yield item

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}:{str(self)}>'



class ExprNode(Node):
    type: Type
    
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.type = Type.UNDEF

    def __str__(self) -> str:
        return f'{self.token.lexeme}:{self.type}'


class VarNode(ExprNode):
    scope: int
    
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.scope = -1
        
    @property
    def name(self) -> str:
        return self.token.lexeme
        
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_var_node(self)
    


class LiteralNode(ExprNode):
    
    value: Any
    
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.value = None

    @property
    def raw_value(self) -> str:
        return self.token.lexeme
    
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_literal_node(self)
    
    def __str__(self) -> str:
        value = self.value if self.value else self.raw_value
        return f'{value}:{self.type}'



class BinaryNode(ExprNode):
    
    def __init__(self, token: Token, expr1: ExprNode, expr2: ExprNode) -> None:
        super().__init__(token)
        self.expr1 = expr1
        self.expr2 = expr2

    @property
    def operator(self) -> Tag:
        return self.token.tag
    
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_node(self)


class UnaryNode(ExprNode):
    
    def __init__(self, token: Token, expr: ExprNode) -> None:
        super().__init__(token)
        self.expr = expr

    @property
    def operator(self) -> Tag:
        return self.token.tag
    
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_unary_node(self)



class ConvertNode(ExprNode):
    def __init__(self, expr: ExprNode) -> None:
        super().__init__(Token(0, Tag.CONVERT, 'convert'))
        self.expr = expr

    @property
    def operator(self) -> Tag:
        return self.token.tag
    
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_convert_node(self)



class StmtNode(Node):
    
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        
    def __str__(self) -> str:
        return f'[{self.__class__.__name__}]'

    def __repr__(self) -> str:
        return f'<{str(self)}>'



class ProgramNode(StmtNode):
    
    def __init__(self, token: Token, name: str, stmt: StmtNode) -> None:
        super().__init__(token)
        self.name = name
        self.stmt = stmt
        
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_program_node(self)




class BlockNode(StmtNode):
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.stmts: list[StmtNode] = []

    def add_stmt(self, stmt: StmtNode) -> None:
        self.stmts.append(stmt)

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_block_node(self)




class DeclNode(StmtNode):
    
    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.vars: list[VarNode] = []
    
    def add_var(self, var: VarNode) -> None:
        self.vars.append(var)
        
    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_decl_node(self)




class AssignNode(StmtNode):
    
    def __init__(self, token: Token, var: VarNode, expr: ExprNode) -> None:
        super().__init__(token)
        self.var = var
        self.expr = expr

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_assign_node(self)




class IfNode(StmtNode):
    
    def __init__(self, token: Token, expr: ExprNode, stmt: StmtNode) -> None:
        super().__init__(token)
        self.expr = expr
        self.stmt = stmt

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_if_node(self)


class ElseNode(StmtNode):
    def __init__(self, token: Token, expr: ExprNode, 
                 stmt1: StmtNode, stmt2: StmtNode) -> None:
        super().__init__(token)
        self.expr = expr
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_else_node(self)


class WhileNode(StmtNode):
    
    def __init__(self, token: Token, expr: ExprNode, stmt: StmtNode) -> None:
        super().__init__(token)
        self.expr = expr
        self.stmt = stmt

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_while_node(self)



class WriteNode(StmtNode):
    
    def __init__(self, token: Token, expr: ExprNode) -> None:
        super().__init__(token)
        self.expr = expr

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_write_node(self)



class ReadNode(StmtNode):
    
    def __init__(self, token: Token, var: VarNode) -> None:
        super().__init__(token)
        self.var = var

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_read_node(self)
