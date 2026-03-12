"""Parser module for the DL compiler.

This module contains the Parser class which performs syntax analysis
on tokens produced by the lexer and builds an abstract syntax tree.
"""
from typing import NoReturn

import colorama

from dlc.lex.lexemes import FIXED_LEXEMES
from dlc.lex.lexer import Lexer
from dlc.lex.tag import Tag
from dlc.lex.token import Token
from dlc.tree.ast import AST
from dlc.tree.nodes import (
    AssignNode,
    BinaryNode,
    BlockNode,
    DeclNode,
    ElseNode,
    ExprNode,
    IfNode,
    LiteralNode,
    ProgramNode,
    ReadNode,
    StmtNode,
    UnaryNode,
    VarNode,
    WhileNode,
    WriteNode,
)


class Parser:
    """Parser for the DL compiler.
    
    Performs syntax analysis on tokens produced by the lexer and builds
    an abstract syntax tree (AST) according to the DL language grammar.
    
    Attributes
    ----------
    lexer : Lexer
        The lexer instance that provides tokens.
    lookahead : Token
        The current token being analyzed.
    ast : AST
        The abstract syntax tree built during parsing.
    had_errors : bool
        Flag indicating whether syntax errors were encountered.

    """
    
    lexer: Lexer
    lookahead: Token
    ast: AST
    had_errors: bool
    
    def __init__(self, lex: Lexer) -> None:
        self.lexer = lex
        self.lookahead = lex.next_token()
        self.had_errors = False
        self.__parse()

    
    def __error(self, line: int, msg: str) -> NoReturn:
        colorama.init()
        print(colorama.Fore.RED, end='')
        print(f'Erro sintático na linha {line}: {msg}')
        print(colorama.Style.RESET_ALL, end='')
        self.had_errors = True
        raise SyntaxError()

    
    def __move(self) -> Token:
        save = self.lookahead
        self.lookahead = self.lexer.next_token()
        return save
    
    
    @staticmethod
    def __tag_to_msg(tag: Tag) -> str:
        match tag:
            case Tag.ID:
                return 'nome'
            case Tag.LIT_INT:
                return 'literal inteiro'
            case Tag.LIT_REAL:
                return 'literal real'
            case Tag.UNKNOWN:
                return 'desconhecido'
            case Tag.EOF:
                return 'fim de arquivo'
            case _:
                return FIXED_LEXEMES[tag]

    
    def __match(self, tag: Tag) -> Token:
        if self.lookahead.tag == tag:
            return self.__move()
        expected = Parser.__tag_to_msg(tag)
        found = self.lookahead.lexeme
        self.__error(self.lookahead.line, f'Esperado "{expected}", mas achou "{found}"')
    
    def __synchronize(self) -> None:
        while self.lookahead.tag not in (Tag.EOF, Tag.BEGIN, Tag.IF, Tag.WRITE, 
                                            Tag.INT, Tag.REAL, Tag.BOOL, Tag.END):
            self.__move()

    def __parse(self) -> None:
        try:
            root = self.__program()
            self.ast = AST(root)
        except SyntaxError:
           pass

    def __program(self) -> ProgramNode:
        match = self.__match
        prog_tok = match(Tag.PROGRAM)
        prog_name_tok = match(Tag.ID)
        stmt = self.__stmt()
        match(Tag.DOT)
        match(Tag.EOF)
        return ProgramNode(prog_tok, prog_name_tok.lexeme, stmt)


    def __block(self) -> BlockNode:
        match = self.__match
        begin_tok = match(Tag.BEGIN)
        block = BlockNode(begin_tok)
        while self.lookahead.tag not in (Tag.END, Tag.EOF):
            try:
                stmt = self.__stmt()
                block.add_stmt(stmt)
                match(Tag.SEMI)
            except SyntaxError:
                self.__synchronize()
        match(Tag.END)
        return block


    def __stmt(self) -> StmtNode:
        match self.lookahead.tag:
            case Tag.BEGIN: 
                return self.__block()
            case Tag.INT | Tag.REAL | Tag.BOOL: 
                return self.__decl()
            case Tag.ID: 
                return self.__assign()
            case Tag.IF: 
                return self.__if()
            case Tag.WHILE:
                return self.__while()
            case Tag.WRITE: 
                return self.__write()
            case Tag.READ:
                return self.__read()
            case _: 
                self.__error(self.lookahead.line, 
                        f'"{self.lookahead.lexeme}" não é um comando válido!')


    def __decl(self) -> DeclNode:
        match = self.__match
        type_tok = self.__move()
        var = VarNode(match(Tag.ID))
        decl_node = DeclNode(type_tok)
        decl_node.add_var(var)
        while self.lookahead.tag == Tag.COMMA:
            match(Tag.COMMA)
            var = VarNode(match(Tag.ID))
            decl_node.add_var(var)
        return decl_node

    def __assign(self) -> AssignNode:
        match = self.__match
        var_tok = match(Tag.ID)
        match(Tag.ASSIGN)
        expr = self.__expr()
        var = VarNode(var_tok)
        return AssignNode(var_tok, var, expr)

    def __if(self) -> IfNode | ElseNode:
        match = self.__match
        if_tok = match(Tag.IF)
        match(Tag.LPAREN)
        expr = self.__expr()
        match(Tag.RPAREN)
        stmt1 = self.__stmt()
        if self.lookahead.tag != Tag.ELSE:
            return IfNode(if_tok, expr, stmt1)
        match(Tag.ELSE)
        stmt2 = self.__stmt()
        return ElseNode(if_tok, expr, stmt1, stmt2)

    def __while(self) -> WhileNode:
        match = self.__match
        while_tok = match(Tag.WHILE)
        match(Tag.LPAREN)
        expr = self.__expr()
        match(Tag.RPAREN)
        stmt = self.__stmt()
        return WhileNode(while_tok, expr, stmt)

    def __write(self) -> WriteNode:
        match = self.__match
        write_tok = match(Tag.WRITE)
        match(Tag.LPAREN)
        expr = self.__expr()
        match(Tag.RPAREN)
        return WriteNode(write_tok, expr)

    def __read(self) -> ReadNode:
        match = self.__match
        read_tok = match(Tag.READ)
        match(Tag.LPAREN)
        var = VarNode(match(Tag.ID))
        match(Tag.RPAREN)
        return ReadNode(read_tok, var)

    def __expr(self) -> ExprNode:
        expr = self.__land()
        while self.lookahead.tag == Tag.OR:
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__land())
        return expr

    def __land(self) -> ExprNode:
        expr = self.__equal()
        while self.lookahead.tag == Tag.AND:
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__equal())
        return expr

    def __equal(self) -> ExprNode:
        expr = self.__rel()
        while self.lookahead.tag in (Tag.EQ, Tag.NE):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__rel())
        return expr

    def __rel(self) -> ExprNode:
        expr = self.__arith()
        while self.lookahead.tag in (Tag.LT, Tag.LE, Tag.GT, Tag.GE):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__arith())
        return expr

    def __arith(self) -> ExprNode:
        expr = self.__term()
        while self.lookahead.tag in (Tag.SUM, Tag.SUB):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__term())
        return expr

    def __term(self) -> ExprNode:
        expr = self.__unary()
        while self.lookahead.tag in (Tag.MUL, Tag.DIV, Tag.MOD):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__unary())
        return expr

    def __unary(self) -> ExprNode:
        if self.lookahead.tag in (Tag.SUM, Tag.SUB, Tag.NOT):
            op = self.__move()
            return UnaryNode(op, self.__unary())
        else:
            return self.__pow()

    def __pow(self) -> ExprNode:
        expr = self.__factor()
        if self.lookahead.tag == Tag.POW:
            op = self.__move()
            return BinaryNode(op, expr, self.__unary())
        return expr

    def __factor(self) -> ExprNode:
        match = self.__match
        expr = None
        match self.lookahead.tag:
            case Tag.LPAREN:
                match(Tag.LPAREN)
                expr = self.__expr()
                match(Tag.RPAREN)
            case Tag.LIT_INT | Tag.LIT_REAL | Tag.LIT_TRUE | Tag.LIT_FALSE:
                lit_tok = self.__move()
                expr = LiteralNode(lit_tok)
            case Tag.ID:
                var_tok = self.__move()
                expr = VarNode(var_tok)
            case _:
                self.__error(self.lookahead.line, 
                        f'"{self.lookahead.lexeme}" invalidou a expressão!')
        return expr
