from dl.lex.lexer import Lexer
from dl.syntax.parser import Parser
from dl.semantic.checker import Checker
from dl.inter.ic import IC
from dl.codegen.x64_codegen import X64CodeGenerator
from pathlib import Path
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
    lexer = Lexer(open(file_input, 'r'))

    #Análise Sintática
    parser = Parser(lexer)
    if parser.had_errors:
        exit()
    ast = parser.ast
    print('\nAST')
    print(ast, '\n')

    #Análise Semântica
    checker = Checker(ast)
    if checker.had_errors:
        exit()
    print('\nAST com anotações semânticas')
    print(ast, '\n')

    #Geração de Código Intermediário
    ic = IC(ast)
    print("\nTAC")
    print(ic, '\n')
    print('\nInterpretação do Código Intermediário')
    ic.interpret()

    #Geração de código x64
    code = X64CodeGenerator(ic).code
    file_name = 'out/prog.s'
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)
    file = open(file_name, 'w')
    file.write('\n'.join(code))
    file.close()
    print('\n\nSaída do programa alvo gerado')
    subprocess.run(['gcc', file_name, '-o', 'out/prog', '-lm'], check=True)
    subprocess.run(['./out/prog'], check=True)

    #Fim
    print('\nCompilação concluída com sucesso!')
