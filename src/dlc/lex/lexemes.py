"""Lexeme definitions for the DL compiler.

This module defines the fixed lexemes (keywords and operators) used in the DL language,
mapping each tag to its corresponding string representation.
"""

from dlc.lex.tag import Tag

FIXED_LEXEMES: dict[Tag, str] = {
    Tag.PROGRAM: 'programa',
    Tag.BEGIN: 'inicio',
    Tag.END: 'fim',
    Tag.WRITE: 'escreva',
    Tag.READ: 'leia',
    Tag.IF: 'se',
    Tag.ELSE: 'senao',
    Tag.WHILE: 'enquanto',
    Tag.INT: 'inteiro',
    Tag.REAL: 'real',
    Tag.BOOL: 'booleano',
    Tag.LIT_TRUE: 'verdade',
    Tag.LIT_FALSE: 'falso',
    Tag.ASSIGN: '=',
    Tag.SUM: '+',
    Tag.SUB: '-',
    Tag.MUL: '*',
    Tag.DIV: '/',
    Tag.MOD: '%',
    Tag.POW: '^',
    Tag.EQ: '==',
    Tag.NE: '!=',
    Tag.NOT: '!',
    Tag.LT: '<',
    Tag.LE: '<=',
    Tag.GT: '>',
    Tag.GE: '>=',
    Tag.OR: '|',
    Tag.AND: '&',
    Tag.SEMI: ';',
    Tag.COMMA: ',',
    Tag.DOT: '.',
    Tag.LPAREN: '(',
    Tag.RPAREN: ')'
}