from typing import TextIO

import colorama

from dlc.lex.lexemes import FIXED_LEXEMES
from dlc.lex.tag import Tag
from dlc.lex.token import Token
from dlc.lex.trie import Trie


class Lexer:
    EOF_CHAR = ''

    def __init__(self, input_stream: TextIO) -> None:
        self.__input = input_stream
        self.line = 1
        self.peek = ' '
        self.trie = Trie()

        #Palavras reservadas
        self.__reserved_words = { lexeme: tag
            for tag, lexeme in FIXED_LEXEMES.items()
                if lexeme.isalpha()
        }

        #Trie
        trie_list = [ tag
            for tag, lexeme in FIXED_LEXEMES.items()
                if not lexeme.isalpha()
        ]
        for t in trie_list:
            self.trie.insert(t, FIXED_LEXEMES[t])
        


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
            if self.peek == '#':
                self.peek = next_char()
                # 2.1. Comentário de linha: #
                if self.peek != '#':
                    while self.peek != '\n' and self.peek != Lexer.EOF_CHAR: 
                        self.peek = next_char()

                # 2.2. Comentário de bloco: ##
                else:
                    self.peek = next_char()
                    while self.peek != Lexer.EOF_CHAR:
                        if self.peek == '#':
                            self.peek = next_char()
                            if self.peek == '#':
                                self.peek = next_char()
                                break
                        else:
                            self.peek = next_char()
                    # 2.2.1 Comentário de bloco não fechado
                    else:
                        self.__error(self.line, 'Comentário não fechado!')
            
            # 3. Não é comentário
            else:
                break


        if self.peek.isdigit():
            lex = ''
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
            lex = ''
            while self.peek.isalnum() or self.peek == '_':
                lex += self.peek
                self.peek = next_char()
            if lex in self.__reserved_words:
                return Token(self.line, self.__reserved_words[lex])
            return Token(self.line, Tag.ID, lex)
        
        
        elif self.peek == self.EOF_CHAR:
            return Token(self.line, Tag.EOF)
        

        else:
            lex = ''
            node = self.trie.root
            if self.peek in node.children:
                while self.peek in node.children:
                    node = node.children[self.peek]
                    lex += self.peek
                    self.peek = next_char()
                return Token(self.line, node.tag)
            else:
                unk = self.peek
                self.peek = next_char()
                return Token(self.line, Tag.UNKNOWN, unk)

