from dl.lex.tag import Tag
from dl.lex.lexer import Token
from dl.tree.ast import AST
from dl.tree.nodes import (
    ProgramNode,
    BlockNode,
    VarNode,
    DeclNode,
    AssignNode,
    IfNode,
    WriteNode,
    BinaryNode,
    LiteralNode,
)

class Parser:
    
    def __init__(self, lex):
        self.lexer = lex
        self.lookahead = None
        self.ast = None
        self.__move()
        self.__parse()

    def __error(self, line: int, msg: str):
        print(f'Erro sintático na linha {line}: {msg}')
        exit()

    def __move(self):
        save = self.lookahead
        self.lookahead = self.lexer.next_token()
        return save
    
    def __match(self, tag: Tag):
        if self.lookahead.tag == tag:
            return self.__move()
        self.__error(self.lookahead.line, f'"{self.lookahead.lexeme}" inesperado')

    def __parse(self):
        root = self.__program()
        self.ast = AST(root)

    def __program(self):
        match = self.__match
        prog_tok = match(Tag.PROGRAM)
        prog_name_tok = match(Tag.ID)
        stmt = self.__stmt()
        match(Tag.DOT)
        match(Tag.EOF)
        return ProgramNode(prog_tok, prog_name_tok.lexeme, stmt)

    def __stmt(self):
        match self.lookahead.tag:
            case Tag.BEGIN: 
                return self.__block()
            case Tag.INT | Tag.REAL | Tag.BOOL: 
                return self.__decl()
            case Tag.ID: 
                return self.__assign()
            case Tag.IF: 
                return self.__if()
            case Tag.WRITE: 
                return self.__write()   
            case _: 
                self.__error(self.lookahead.line, 'comando inválido!')        

    def __decl(self):
        self.__move()
        self.__match(Tag.ID)

    def __block(self):
        match = self.__match
        begin_tok = match(Tag.BEGIN)
        block = BlockNode(begin_tok)
        while self.lookahead.tag != Tag.END:
            stmt = self.__stmt()
            block.add_stmt(stmt)
            match(Tag.SEMI)
        match(Tag.END)
        return block

    def __assign(self):
        match = self.__match
        match(Tag.ID)
        match(Tag.ASSIGN)
        self.__expr()

    def __if(self):
        match = self.__match
        match(Tag.IF)
        match(Tag.LPAREN)
        self.__expr()
        match(Tag.RPAREN)
        self.__stmt()

    def __write(self):
        match = self.__match
        match(Tag.WRITE)
        match(Tag.LPAREN)
        self.__expr()
        match(Tag.RPAREN)

    def __expr(self):
        self.__equal()
        while self.lookahead.tag == Tag.OR:
            self.__move()
            self.__equal()

    def __equal(self):
        self.__rel()
        while self.lookahead.tag == Tag.EQ:
            self.__move()
            self.__rel()

    def __rel(self):
        self.__arith()
        while self.lookahead.tag in (Tag.LT, Tag.GT):
            self.__move()
            self.__arith()

    def __arith(self):
        self.__term()
        while self.lookahead.tag in (Tag.SUM, Tag.SUB):
            self.__move()
            self.__term()

    def __term(self):
        self.__factor()
        while self.lookahead.tag == Tag.MUL:
            self.__move()
            self.__factor()

    def __factor(self):
        match = self.__match
        match self.lookahead.tag:
            case Tag.LPAREN:
                match(Tag.LPAREN)
                self.__expr()
                match(Tag.RPAREN)
            case Tag.LIT_INT | Tag.LIT_REAL | Tag.LIT_TRUE | Tag.LIT_FALSE:
                self.__move()
            case Tag.ID:
                self.__move()
            case _:
                self.__error(self.lookahead.line, 'Expressão inválida!')