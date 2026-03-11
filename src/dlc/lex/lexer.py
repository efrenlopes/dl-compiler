from typing import TextIO

import colorama

from dlc.lex.tag import Tag
from dlc.lex.token import Token


class Lexer:
    EOF_CHAR = ''

    def __init__(self, input_stream: TextIO) -> None:
        self.__input = input_stream
        self.line = 1
        self.peek = ' '
        #Keywords
        self.__words = { tag.value: tag
            for tag in (
                Tag.PROGRAM,
                Tag.BEGIN,
                Tag.END,
                Tag.WRITE,
                Tag.READ,
                Tag.IF,
                Tag.ELSE,
                Tag.WHILE,
                Tag.INT,
                Tag.REAL,
                Tag.BOOL,
                Tag.LIT_TRUE,
                Tag.LIT_FALSE 
            )
        }

    def __error(self, line: int, msg: str) -> None:
        colorama.init()
        print(colorama.Fore.RED, end='')
        print(f'Erro léxico na linha {line}: {msg}')
        print(colorama.Style.RESET_ALL, end='')
        exit()


    def __next_char(self) -> str:
        if (self.peek == '\n'):
            self.line += 1
        peek = self.__input.read(1)
        return peek

    def next_token(self) -> Token:
        next_char = self.__next_char

        # Ignora comentários e espaços em braco
        while True:
            # 1. Ignora espaços
            while self.peek in (' ', '\n', '\t', '\r'):
                self.peek = next_char()
            
            # 2. Verifica se pode ser um comentário
            if self.peek == '/':
                self.peek = next_char()
                # 2.1. Comentário de linha: //
                if self.peek == '/':
                    while self.peek != '\n' and self.peek != Lexer.EOF_CHAR: 
                        self.peek = next_char()
                # 2.2. Comentário de bloco: /*
                elif self.peek == '*':
                    self.peek = next_char()
                    while self.peek != Lexer.EOF_CHAR:
                        if self.peek == '*':
                            self.peek = next_char()
                            if self.peek == '/':
                                self.peek = next_char()
                                break
                        else:
                            self.peek = next_char()
                    # 2.2.1 Comentário de bloco não fechado
                    else:
                        self.__error(self.line, 'Comentário não fechado!')
                # 2.3. Token de divisão
                else:
                    return Token(self.line, Tag.DIV)
            else:
                break


        match self.peek:
            case Tag.ASSIGN.value:
                self.peek = next_char()
                if self.peek == Tag.EQ.value[1]:
                    self.peek = next_char()
                    return Token(self.line, Tag.EQ)
                return Token(self.line, Tag.ASSIGN)
            case Tag.NOT.value:
                self.peek = next_char()
                if self.peek == Tag.NE.value[1]:
                    self.peek = next_char()
                    return Token(self.line, Tag.NE)
                return Token(self.line, Tag.NOT)

            case Tag.SUM.value:
                self.peek = next_char()
                return Token(self.line, Tag.SUM)
            case Tag.SUB.value:
                self.peek = next_char()
                return Token(self.line, Tag.SUB)
            case Tag.MUL.value:
                self.peek = next_char()
                return Token(self.line, Tag.MUL)
            case Tag.MOD.value:
                self.peek = next_char()
                return Token(self.line, Tag.MOD)
            case Tag.POW.value:
                self.peek = next_char()
                return Token(self.line, Tag.POW)
            case Tag.OR.value:
                self.peek = next_char()
                return Token(self.line, Tag.OR)
            case Tag.AND.value:
                self.peek = next_char()
                return Token(self.line, Tag.AND)
            case Tag.LT.value:
                self.peek = next_char()
                if self.peek == Tag.LE.value[1]:
                    self.peek = next_char()
                    return Token(self.line, Tag.LE)
                return Token(self.line, Tag.LT)
            case Tag.GT.value:
                self.peek = next_char()
                if self.peek == Tag.GE.value[1]:
                    self.peek = next_char()
                    return Token(self.line, Tag.GE)
                return Token(self.line, Tag.GT)
            case Tag.SEMI.value:
                self.peek = next_char()
                return Token(self.line, Tag.SEMI)
            case Tag.COMMA.value:
                self.peek = next_char()
                return Token(self.line, Tag.COMMA)
            case Tag.DOT.value:
                self.peek = next_char()
                return Token(self.line, Tag.DOT)
            case Tag.LPAREN.value:
                self.peek = next_char()
                return Token(self.line, Tag.LPAREN)
            case Tag.RPAREN.value:
                self.peek = next_char()
                return Token(self.line, Tag.RPAREN)
            case Lexer.EOF_CHAR:
                return Token(self.line, Tag.EOF)
            case _:
                lex = ''
                if self.peek.isdigit():
                    while self.peek.isdigit():
                        lex += self.peek
                        self.peek = next_char()
                    if self.peek != '.':
                        return Token(self.line, Tag.LIT_INT, lex)
                    
                    while True:
                        lex += self.peek
                        self.peek = next_char()
                        if not self.peek.isdigit():
                            break
                    return Token(self.line, Tag.LIT_REAL, lex)
                elif self.peek.isalpha() or self.peek == '_':
                    while self.peek.isalnum() or self.peek == '_':
                        lex += self.peek
                        self.peek = next_char()
                    if lex in self.__words:
                        return Token(self.line, self.__words[lex])
                    return Token(self.line, Tag.ID, lex)

        unk = self.peek
        self.peek = next_char()
        return Token(self.line, Tag.UNK, unk)