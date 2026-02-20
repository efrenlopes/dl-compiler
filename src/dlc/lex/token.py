from dlc.lex.tag import Tag

class Token:
    
    def __init__(self, line:int, tag: Tag, lexeme: str=None):
        self.line = line
        self.tag = tag
        self.lexeme = lexeme

    def __str__(self):
        if self.lexeme:
            return f"<{self.tag.name}, '{self.lexeme}'>"
        return f'<{self.tag.name}>'

    def __repr__(self):
        return f'<Token: {str(self)} at line {self.line}>'