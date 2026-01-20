from dl.lex.tag import Tag

class Parser:
    
    def __init__(self, lex):
        self.lexer = lex
        self.lookahead = None
        self.__move()
        self.__parse()

    def __error(self, line: int, msg: str):
        print(f'Erro sintático na linha {line}: {msg}')
        exit()

    def __move(self):
        save = self.lookahead
        self.lookahead = self.lexer.next_token()
        return save
    
    def __match(self, tag: Tag):
        if self.lookahead.tag == tag:
            return self.__move()
        self.__error(self.lookahead.line, f'"{self.lookahead.lexeme}" inesperado')

    def __parse(self):
        self.__program()

    def __program(self):
        match = self.__match
        match(Tag.PROGRAM)
        match(Tag.ID)
        self.__stmt()
        match(Tag.DOT)
        match(Tag.EOF)

    def __stmt(self):
        pass

    # def __block(self):
    #     match = self.__match
    #     match(Tag.BEGIN)
    #     while self.lookahead.tag != Tag.END:
    #         self.__stmt()
    #         match(Tag.SEMI)
    #     match(Tag.END)


    # def __decl(self):
    #     self.__move()
    #     self.__match(Tag.ID)

