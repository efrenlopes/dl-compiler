"""Token tags for the lexer.

This module defines all the token types (tags) used by the lexer to classify
and represent tokens in the DL compiler, including operators, delimiters,
reserved words, identifiers, numeric literals, and special tokens.
"""
from enum import Enum, auto


class Tag(Enum):
    """Token tags for the DL compiler lexer.
    
    This enumeration defines all token types used by the lexer to classify
    tokens, including operators, delimiters, reserved words, identifiers,
    numeric literals, and special tokens.
    """

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
        """Return the name of the tag."""
        return self.name
    
    def __repr__(self) -> str:
        """Return a detailed string representation of the tag."""
        return f'<Tag: {self.name}>'