from dl.lex.tag import Tag
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
        type_tok = self.__move()
        var_tok = self.__match(Tag.ID)
        var = VarNode(var_tok)
        return DeclNode(type_tok, var)

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
        var_tok = match(Tag.ID)
        match(Tag.ASSIGN)
        expr = self.__expr()
        var = VarNode(var_tok)
        return AssignNode(var_tok, var, expr)

    def __if(self):
        match = self.__match
        if_tok = match(Tag.IF)
        match(Tag.LPAREN)
        expr = self.__expr()
        match(Tag.RPAREN)
        stmt = self.__stmt()
        return IfNode(if_tok, expr, stmt)

    def __write(self):
        match = self.__match
        write_tok = match(Tag.WRITE)
        match(Tag.LPAREN)
        expr = self.__expr()
        match(Tag.RPAREN)
        return WriteNode(write_tok, expr)

    def __expr(self):
        expr = self.__equal()
        while self.lookahead.tag == Tag.OR:
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__equal())
        return expr

    def __equal(self):
        expr = self.__rel()
        while self.lookahead.tag == Tag.EQ:
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__rel())
        return expr

    def __rel(self):
        expr = self.__arith()
        while self.lookahead.tag in (Tag.LT, Tag.GT):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__arith())
        return expr

    def __arith(self):
        expr = self.__term()
        while self.lookahead.tag in (Tag.SUM, Tag.SUB):
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__term())
        return expr

    def __term(self):
        expr = self.__factor()
        while self.lookahead.tag == Tag.MUL:
            op_tok = self.__move()
            expr = BinaryNode(op_tok, expr, self.__factor())
        return expr

    def __factor(self):
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
                self.__error(self.lookahead.line, 'Expressão inválida!')
        return expr
