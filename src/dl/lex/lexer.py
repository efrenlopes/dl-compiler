from dl.lex.tag import Tag
from dl.lex.token import Token

class Lexer:
    EOF_CHAR = ''

    def __init__(self, input_stream):
        self.__input = input_stream
        self.line = 1
        self.peek = ' '
        #Keywords
        self.__words = {}
        self.__words[Tag.PROGRAM.value] = Tag.PROGRAM
        self.__words[Tag.BEGIN.value] = Tag.BEGIN
        self.__words[Tag.END.value] = Tag.END
        self.__words[Tag.WRITE.value] = Tag.WRITE
        self.__words[Tag.IF.value] = Tag.IF
        self.__words[Tag.WHILE.value] = Tag.WHILE
        self.__words[Tag.INT.value] = Tag.INT
        self.__words[Tag.REAL.value] = Tag.REAL
        self.__words[Tag.BOOL.value] = Tag.BOOL
        self.__words[Tag.LIT_TRUE.value] = Tag.LIT_TRUE
        self.__words[Tag.LIT_FALSE.value] = Tag.LIT_FALSE

    def __next_char(self):
        if (self.peek == '\n'):
            self.line += 1
        self.peek = self.__input.read(1)
        return self.peek

    def next_token(self):
        next_char = self.__next_char

        while self.peek in [' ', '\n', '\t', '\r']:
            next_char()

        match self.peek:
            case Tag.ASSIGN.value:
                next_char()
                if self.peek == Tag.ASSIGN.value:
                    next_char()
                    return Token(self.line, Tag.EQ)
                return Token(self.line, Tag.ASSIGN)
            case Tag.SUM.value:
                next_char()
                return Token(self.line, Tag.SUM)
            case Tag.SUB.value:
                next_char()
                return Token(self.line, Tag.SUB)
            case Tag.MUL.value:
                next_char()
                return Token(self.line, Tag.MUL)
            case Tag.OR.value:
                next_char()
                return Token(self.line, Tag.OR)
            case Tag.LT.value:
                next_char()                
                return Token(self.line, Tag.LT)
            case Tag.GT.value:
                next_char()
                return Token(self.line, Tag.GT)
            case Tag.SEMI.value:
                next_char()
                return Token(self.line, Tag.SEMI)
            case Tag.DOT.value:
                next_char()
                return Token(self.line, Tag.DOT)
            case Tag.LPAREN.value:
                next_char()
                return Token(self.line, Tag.LPAREN)
            case Tag.RPAREN.value:
                next_char()
                return Token(self.line, Tag.RPAREN)
            case Lexer.EOF_CHAR:
                return Token(self.line, Tag.EOF)
            case _:
                lex = ''
                if self.peek.isdigit():
                    while self.peek.isdigit():
                        lex += self.peek
                        next_char()
                    if self.peek != '.':
                        return Token(self.line, Tag.LIT_INT, lex)
                    
                    while True:
                        lex += self.peek
                        next_char()
                        if not self.peek.isdigit():
                            break
                    return Token(self.line, Tag.LIT_REAL, lex)
                elif ( self.peek.isalpha() or self.peek == '_' ):
                    while( self.peek.isalnum() or self.peek == '_' ):
                        lex += self.peek
                        next_char()
                    if ( lex in self.__words ):
                        return Token(self.line, self.__words[lex])
                    return Token(self.line, Tag.ID, lex)

        unk = self.peek
        next_char()
        return Token(self.line, Tag.UNK, unk)