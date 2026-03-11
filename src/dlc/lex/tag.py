from enum import Enum, auto


class Tag(Enum):

    #Operadores e delimitadores
    ASSIGN = auto()
    SUM = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    POW = auto()
    EQ = auto()
    NE = auto()
    NOT = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    OR = auto()
    AND = auto()
    SEMI = auto()
    COMMA = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    
    #Palavras reservadas
    PROGRAM = auto()
    BEGIN = auto()
    END = auto()
    WRITE = auto()
    READ = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    INT = auto()
    REAL = auto()
    BOOL = auto()
    LIT_TRUE = auto()
    LIT_FALSE = auto()

    #ID e Literais numéricos
    ID = auto()
    LIT_INT = auto()
    LIT_REAL = auto()

    #Outros
    UNKNOWN = auto()
    EOF = auto()
    CONVERT = auto()
        

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'<Tag: {self.name}>'