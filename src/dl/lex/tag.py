from enum import Enum, auto

class Tag(Enum):

    #Operadores e delimitadores
    ASSIGN = '='
    SUM = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    EQ = '=='
    NE = '!='
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    OR = '|'
    AND = '&'
    SEMI = ';'
    DOT = '.'
    LPAREN = '('
    RPAREN = ')'

    #Palavras reservadas
    PROGRAM = 'programa'
    BEGIN = 'inicio'
    END = 'fim'
    WRITE = 'escreva'
    READ = 'leia'
    IF = 'se'
    WHILE = 'enquanto'
    INT = 'inteiro'
    REAL = 'real'
    BOOL = 'booleano'
    LIT_TRUE = 'verdade'
    LIT_FALSE = 'falso'

    #ID e Literais numéricos
    ID = auto()
    LIT_INT = auto()
    LIT_REAL = auto()

    #Outros
    UNK = auto()
    EOF = auto()
    CONVERT = auto()
        

    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f'<Tag: {self.name}>'