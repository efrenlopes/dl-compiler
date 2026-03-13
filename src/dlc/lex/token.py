"""Token representation for the lexical analyzer.

This module provides the Token class which represents a single token
produced by the lexical analyzer, including its tag, lexeme, and line number.
"""

from dlc.lex.lexemes import FIXED_LEXEMES
from dlc.lex.tag import Tag


class Token:
    """Represents a single token produced by the lexical analyzer.
    
    Attributes
    ----------
    line : int
        The line number where the token appears.
    tag : Tag
        The token's tag identifying its type.
    inter_lexeme : str|None
        The token's lexeme value (optional).
    
    """
    
    def __init__(self, line: int, tag: Tag, lexeme: str|None=None) -> None:
        self.line = line
        self.tag = tag
        self.inter_lexeme = lexeme


    @property
    def lexeme(self) -> str:
        """Return the token's lexeme string representation.
        
        Returns
        -------
        str
            The lexeme value, either from inter_lexeme or FIXED_LEXEMES.
        
        """
        if self.inter_lexeme:
            return self.inter_lexeme
        return FIXED_LEXEMES[self.tag]


    def __str__(self) -> str:
        if self.inter_lexeme:
            return f"<{self.tag.name}, '{self.inter_lexeme}'>"
        return f'<{self.tag.name}>'


    def __repr__(self) -> str:
        return f'<Token: {str(self)} at line {self.line}>'