import sys
from dl.lex.lexer import Lexer
from dl.syntax.parser import Parser

if __name__ == '__main__':
    #Entrada
    if len(sys.argv) != 2:
        print('Argumentos inválidos! Esperado um caminho ' +
              'de arquivo para um programa na linguagem DL.')
        exit()
    file_input = sys.argv[1]

    #Análise Léxica
    lexer = Lexer(file_input)

    #Análise Sintática
    parser = Parser(lexer)

    #Fim
    print('Compilação concluída com sucesso!')