from dlc.lex.lexemes import FIXED_LEXEMES
from dlc.lex.tag import Tag


class Token:
    
    def __init__(self, line: int, tag: Tag, lexeme: str|None=None) -> None:
        self.line = line
        self.tag = tag
        self.inter_lexeme = lexeme

    @property
    def lexeme(self) -> str:
        if self.inter_lexeme:
            return self.inter_lexeme
        elif self.tag in FIXED_LEXEMES:
            return FIXED_LEXEMES[self.tag]
        else:
            return self.tag.name

    def __str__(self) -> str:
        if self.inter_lexeme:
            return f"<{self.tag.name}, '{self.inter_lexeme}'>"
        return f'<{self.tag.name}>'

    def __repr__(self) -> str:
        return f'<Token: {str(self)} at line {self.line}>'