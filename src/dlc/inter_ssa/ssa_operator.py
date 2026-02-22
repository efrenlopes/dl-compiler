from enum import Enum


class SSAOperator(Enum):
    LABEL = 'label'
    GOTO = 'goto'
    IF = 'if'
    PRINT = 'print'
    READ = 'read'
    CONVERT = 'convert'
    MOVE = '='
    SUM = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    POW = '^'
    EQ = '=='
    NE = '!='
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    PLUS = 'plus'
    MINUS = 'minus'
    NOT = 'not'
    PHI = 'phi'
    ALLOCA = 'alloca'
    STORE = 'store'
    LOAD = 'load'

    def __str__(self):
        return self.value

