from enum import Enum


class Operator(Enum):
    LABEL = 'label'
    GOTO = 'goto'
    IF = 'if'
    IFFALSE = 'iffalse'
    PRINT = 'print'
    READ = 'read'
    CONVERT = 'convert'
    MOVE = '='
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
    

    def __str__(self):
        return self.value

