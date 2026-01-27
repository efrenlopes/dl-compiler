from enum import Enum


class Operator(Enum):
    LABEL = 'label'
    GOTO = 'goto'
    IF = 'if'
    IFFALSE = 'iffalse'
    PRINT = 'print'
    CONVERT = 'convert'
    MOVE = '='
    SUM = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    EQ = '=='
    GT = '>'
    LT = '<'

    def __str__(self):
        return self.value

