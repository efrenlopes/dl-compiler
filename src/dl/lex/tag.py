from enum import Enum, auto

class Tag(Enum):

    #Operadores e delimitadores
    ASSIGN = auto()
    SUM = auto()
    SUB = auto()
    MUL = auto()
    EQ = auto()
    LT = auto()
    GT = auto()
    OR = auto()
    SEMI = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()

    #Literais numéricos
    LIT_INT = auto()
    LIT_REAL = auto()

    #ID e Palavras reservadas
    ID = auto()
    PROGRAM = auto()
    BEGIN = auto()
    END = auto()
    WRITE = auto()
    IF = auto()
    INT = auto()
    REAL = auto()
    BOOL = auto()
    LIT_TRUE = auto()
    LIT_FALSE = auto()

    #Outros
    EOF = auto()
    UNK = auto()
        
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<Tag: {str(self)}>'