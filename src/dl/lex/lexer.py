from dl.lex.tag import Tag
from dl.lex.token import Token

class Lexer:
    EOF_CHAR = ''

    def __init__(self, file_name: str):
        self.__file = open(file_name, 'r')
        self.line = 1
        self.peek = ' '
        #Keywords
        self.__words = {}
        self.__words['programa'] = Tag.PROGRAM
        self.__words['inicio'] = Tag.BEGIN
        self.__words['fim'] = Tag.END
        self.__words['escreva'] = Tag.WRITE
        self.__words['se'] = Tag.IF
        self.__words['inteiro'] = Tag.INT
        self.__words['real'] = Tag.REAL
        self.__words['booleano'] = Tag.BOOL
        self.__words['verdade'] = Tag.LIT_TRUE
        self.__words['falso'] = Tag.LIT_FALSE

    def __next_char(self):
        if (self.peek == '\n'):
            self.line += 1
        self.peek = self.__file.read(1)
        return self.peek

    def next_token(self):
        next_char = self.__next_char

        while self.peek in [' ', '\n', '\t', '\r']:
            next_char()

        match self.peek:
            case '=':
                next_char()
                if self.peek == '=':
                    next_char()
                    return Token(Tag.EQ, '==', self.line)
                return Token(Tag.ASSIGN, '=', self.line)
            case '+':
                next_char()
                return Token(Tag.SUM, '+', self.line)
            case '-':
                next_char()
                return Token(Tag.SUB, '-', self.line)
            case '*':
                next_char()
                return Token(Tag.MUL, '*', self.line)
            case '|':
                next_char()
                return Token(Tag.OR, '|', self.line)
            case '<':
                next_char()                
                return Token(Tag.LT, '<', self.line)
            case '>':
                next_char()
                return Token(Tag.GT, '>', self.line)
            case ';':
                next_char()
                return Token(Tag.SEMI, ';', self.line)
            case '.':
                next_char()
                return Token(Tag.DOT, '.', self.line)
            case '(':
                next_char()
                return Token(Tag.LPAREN, '(', self.line)
            case ')':
                next_char()
                return Token(Tag.RPAREN, ')', self.line)
            case Lexer.EOF_CHAR:
                return Token(Tag.EOF, Lexer.EOF_CHAR, self.line)
            
            case _:
                lex = ''
                if self.peek.isdigit():
                    while self.peek.isdigit():
                        lex += self.peek
                        next_char()
                    if self.peek != '.':
                        return Token(Tag.LIT_INT, lex, self.line)
                    
                    while True:
                        lex += self.peek
                        next_char()
                        if not self.peek.isdigit():
                            break
                    return Token(Tag.LIT_REAL, lex, self.line)
                elif ( self.peek.isalpha() or self.peek == '_' ):
                    while( self.peek.isalnum() or self.peek == '_' ):
                        lex += self.peek
                        next_char()
                    if ( lex in self.__words ):
                        return Token(self.__words[lex], lex, self.line)
                    return Token(Tag.ID, lex, self.line)

        unk = self.peek
        next_char()
        return Token(Tag.UNK, unk, self.line)