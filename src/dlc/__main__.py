import subprocess
import sys
from pathlib import Path

from dlc.codegen.codegen_x64 import CodeGeneratorX64
from dlc.inter.ir import IR
from dlc.inter.ssa import SSA
from dlc.inter.ssa_opt import optimize_ssa
from dlc.lex.lexer import Lexer
from dlc.semantic.checker import Checker
from dlc.syntax.parser import Parser

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
    #print(ast, '\n')

    #Geração de Código Intermediário
    ir = IR(ast)
    print("\n**** TAC ****")
    print(ir, '\n')
    print('\n**** Interpretação do TAC ****')
    ir.plot()
    ir.interpret()
    print('\n\n')

    ssa = SSA(ir)
    print("\n**** TAC-SSA ****")
    print(ssa)
    ssa.ir.plot()
    ssa.ir.interpret()
    print('\n\n')


    optimize_ssa(ssa)
    print("\n**** TAC-SSA otimizada ****")
    print(ssa.ir)
    ssa.ir.plot()
    print('\n\n**** Interpretação do TAC Otimizado ****')
    ssa.ir.interpret()
    print('\n\n')





    # print("\nVacidade para inteiro/booleano")
    # live_int = LivenessAnalysis(ssa, (Type.INT, Type.BOOL))
    # live_int.print_liveness()
    # print('vars', live_int.vars)
    # print('use', live_int.use)
    # print('def', live_int.def_)

    # print("\nVacidade para REAL")
    # live_real = LivenessAnalysis(ssa, (Type.REAL,))
    # live_real.print_liveness()
    # print('vars', live_real.vars)
    # print('use', live_real.use)
    # print('def', live_real.def_)


    # print("grafo interferencia inteiro/booleano")
    # ig_int = InterferenceGraph(live_int, ['r12d', 'r13d', 'r14d', 'r15d'])
    # print('registradores ', ig_int.reg_alloc, '\n')
    # print('spill', ig_int.mem_alloc, '\n')
    # print('spill slot count', ig_int.spill_slots_count)

    # print("grafo interferencia real")
    # ig_real = InterferenceGraph(live_real, [])
    # print('registradores ', ig_real.reg_alloc, '\n')
    # print('spill', ig_real.mem_alloc, '\n')
    # print('spill slot count', ig_real.spill_slots_count)







    # #Geração de código x64
    cgx64 = CodeGeneratorX64(ssa)
    #print(cgx64.reg_alloc)
    #print(cgx64.mem_alloc)
    file_name = 'out/prog.s'
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)
    file = open(file_name, 'w')
    file.write('\n'.join(cgx64.code))
    file.close()
    print('\n\n**** Saída do programa alvo gerado ****')
    subprocess.run(['gcc', file_name, '-o', 'out/prog', '-lm'], check=True)
    subprocess.run(['./out/prog'], check=True)

    #Fim
    print('\nCompilação concluída com sucesso!')
