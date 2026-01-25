from dl.lex.lexer import Lexer
from dl.syntax.parser import Parser
from dl.semantic.checker import Checker
from dl.inter.ic import IC
from dl.codegen.x64_codegen import X64CodeGenerator
import sys
import subprocess

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
    print('\nInterpretação do Código Intermediário')
    ic.interpret()

    #Geração de código x64
    code = X64CodeGenerator(ic).code
    file = open('out/prog.s', 'w')
    file.write('\n'.join(code))
    file.close()
    print('\n\nSaída do programa alvo gerado')
    subprocess.run(['gcc', 'out/prog.s', '-o', 'out/prog'], check=True)
    subprocess.run(['./out/prog'], check=True)

    #Fim
    print('\nCompilação concluída com sucesso!')
