from dlc.inter_ssa.sccp import SCCP, copy_propagation, dead_code_elimination, optimize_ssa
from dlc.inter_ssa.ssa import SSA
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.lex.lexer import Lexer
from dlc.syntax.parser import Parser
from dlc.semantic.checker import Checker
import sys

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
    print('\n**** AST ****')
    print(ast, '\n')

    #Análise Semântica
    checker = Checker(ast)
    if checker.had_errors:
        exit()
    print('\n**** AST com anotações semânticas ****')
    print(ast, '\n')

    #Geração de Código Intermediário
    ic = SSA_IC(ast)
    print("\n**** TAC ****")
    print(ic, '\n')
    print('\n**** Interpretação do TAC ****')
    ic.plot()
    ic.interpret()

    ssa = SSA(ic)
    #optimize_ssa(ic)
    #copy_propagation(ic)
    #dead_code_elimination(ic)
    #SCCP.optimize(ic)

    #ic.bb_sequence[0].instructions[1].result.number = 15

    print(ic)
    ic.plot()
    ic.interpret()

    

    #Otimização
    # optimize(ic)
    # print("\n\n\n**** TAC otimizado ****")
    # print(ic, '\n')
    # print('\n**** Interpretação do TAC Otimizado ****')
    # ic.interpret()

    #Geração de código x64
    # code = X64CodeGenerator(ic).code
    # file_name = 'out/prog.s'
    # Path(file_name).parent.mkdir(parents=True, exist_ok=True)
    # file = open(file_name, 'w')
    # file.write('\n'.join(code))
    # file.close()
    # print('\n\n**** Saída do programa alvo gerado ****')
    # subprocess.run(['gcc', file_name, '-o', 'out/prog', '-lm'], check=True)
    # subprocess.run(['./out/prog'], check=True)

    #Fim
    print('\nCompilação concluída com sucesso!')
