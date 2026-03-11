from enum import Enum


class Tag(Enum):

    #Operadores e delimitadores
    ASSIGN = '='
    SUM = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    POW = '^'
    EQ = '=='
    NE = '!='
    NOT = '!'
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    OR = '|'
    AND = '&'
    SEMI = ';'
    COMMA = ','
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
    ELSE = 'senao'
    WHILE = 'enquanto'
    INT = 'inteiro'
    REAL = 'real'
    BOOL = 'booleano'
    LIT_TRUE = 'verdade'
    LIT_FALSE = 'falso'

    #ID e Literais numéricos
    ID = 'ID'
    LIT_INT = 'LIT_INT'
    LIT_REAL = 'LIT_REAL'

    #Outros
    UNK = 'UNK'
    EOF = 'EOF'
    CONVERT = 'CONVERT'
        

    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f'<Tag: {self.name}>'