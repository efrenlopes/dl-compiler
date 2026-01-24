import sys
from dl.lex.lexer import Lexer
from dl.syntax.parser import Parser
from dl.semantic.checker import Checker
from dl.inter.ic import IC

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
    ast = parser.ast
    print('\nAST')
    print(ast, '\n')

    #Análise Semântica
    checker = Checker(ast)
    print('\nAST com anotações semânticas')
    print(ast, '\n')
    if checker.has_semantic_error:
        exit()

    #Geração de Código Intermediário
    ic = IC(ast)
    print("\nTAC")
    print(ic, '\n')
    #print('\nTAC Interpretation Output')
    #ic.interpret()

    #Fim
    print('\nCompilação concluída com sucesso!')
