"""Lexical analyzer for the DL compiler.

This module provides the Lexer class which tokenizes source code input
by reading characters from an input stream and producing tokens based on
lexical rules for identifiers, numbers, operators, and reserved words.
"""

from typing import TextIO

import colorama

from dlc.lex.lexemes import FIXED_LEXEMES
from dlc.lex.tag import Tag
from dlc.lex.token import Token
from dlc.lex.trie import Trie


class Lexer:
    """Lexical analyzer for tokenizing source code.
    
    This class reads characters from an input stream and produces tokens
    based on lexical rules for identifiers, numbers, operators, and reserved words.
    
    Attributes
    ----------
    EOF_CHAR : str
        The end-of-file character marker.
    line : int
        The current line number in the input stream.
    peek : str
        The current character being examined.
    trie : Trie
        A trie data structure for efficient operator matching.

    """

    EOF_CHAR = ''

    def __init__(self, input_stream: TextIO) -> None:
        """Initialize the Lexer with an input stream.
        
        Parameters
        ----------
        input_stream : TextIO
            The input stream to tokenize.

        """
        self.__input = input_stream
        self.line = 1
        self.peek = ' '
        self.trie = Trie()

        #Palavras reservadas
        self.__reserved_words = { lexeme: tag
            for tag, lexeme in FIXED_LEXEMES.items()
                if lexeme.isalpha()
        }

        #Prefix-tree
        trie_list = [ tag
            for tag, lexeme in FIXED_LEXEMES.items()
                if not lexeme.isalpha()
        ]
        for t in trie_list:
            self.trie.insert(t, FIXED_LEXEMES[t])
        


    def __error(self, line: int, msg: str) -> None:
        """Report a lexical error and terminate execution.

        Parameters
        ----------
        line : int
            Line where the error occurred.
        msg : str
            Descriptive error message.

        """
        colorama.init()
        print(colorama.Fore.RED, end='')
        print(f'Erro léxico na linha {line}: {msg}')
        print(colorama.Style.RESET_ALL, end='')
        exit()



    def __next_char(self) -> str:
        """Read the next character from the input stream.
        
        Updates the line counter if a newline character is encountered.
        
        Returns
        -------
        str
            The next character from the input stream, or EOF_CHAR if end of file.
            
        """
        if (self.peek == '\n'):
            self.line += 1
        peek = self.__input.read(1)
        return peek



    def next_token(self) -> Token:
        """Tokenize the next token from the input stream.
        
        Skips over whitespace and comments, then identifies and returns
        the next token based on lexical rules for numbers, identifiers,
        operators, and reserved words.
        
        Returns
        -------
        Token
            The next token from the input stream.
            
        """
        next_char = self.__next_char

        # ------------------------------------------------------------------
        # 1. Skip whitespace and comments
        # ------------------------------------------------------------------
        while True:

            # Consume spaces, tabs and newlines
            while self.peek in (' ', '\n', '\t', '\r'):
                self.peek = next_char()
            
            # It is not a comment
            if self.peek != '#':
                break

            # Line comment (#)
            self.peek = next_char()
            if self.peek != '#':
                while self.peek != '\n' and self.peek != Lexer.EOF_CHAR: 
                    self.peek = next_char()

            # Block comment (## ... ##)
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

                # Unclosed comment block
                else:
                    self.__error(self.line, 'Bloco de comentário não fechado!')
            

        # ------------------------------------------------------------------
        # 2. Numeric literal recognition
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 3. Identifiers and reserved words
        # ------------------------------------------------------------------
        if self.peek.isalpha() or self.peek == '_':
            lex = ''
            while self.peek.isalnum() or self.peek == '_':
                lex += self.peek
                self.peek = next_char()
            if lex in self.__reserved_words:
                return Token(self.line, self.__reserved_words[lex])
            return Token(self.line, Tag.ID, lex)
        
        # ------------------------------------------------------------------
        # 4. End of file
        # ------------------------------------------------------------------        
        if self.peek == self.EOF_CHAR:
            return Token(self.line, Tag.EOF, 'EoF')
        
        # ------------------------------------------------------------------
        # 5. Operators and delimiters (via trie)
        # ------------------------------------------------------------------
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
