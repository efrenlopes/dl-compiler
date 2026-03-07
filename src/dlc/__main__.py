from dlc.inter_ssa.ssa_interference_graph import InterferenceGraph
from dlc.inter_ssa.ssa_live_analysis import LivenessAnalysis
from dlc.inter_ssa.ssa_opt import optimize_ssa
from dlc.inter_ssa.ssa import SSA
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.lex.lexer import Lexer
from dlc.semantic.type import Type
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
    #print("\n**** TAC ****")
    print(ic, '\n')
    #print('\n**** Interpretação do TAC ****')
    #ic.plot()
    #ic.interpret()
    print('\n\n')

    ssa = SSA(ic)
    print(ssa)
    #ssa.ic.plot()
    #ssa.ic.interpret()
    print('\n\n')


    optimize_ssa(ssa)
    print(ssa.ic)
    # ssa.ic.plot()
    #ssa.ic.interpret()
    print('\n\n')


    live_int = LivenessAnalysis(ssa)
    live_int.print_liveness()

    # live_real = LivenessAnalysis(ssa, Type.REAL)
    # live_real.print_liveness()


    #ig = InterferenceGraph(live_range, 1)
    #ig.print_allocation_summary()
    #print('registradores ', ig.reg_alloc, '\n')
    #print('spill', ig.mem_alloc, '\n')


    # live_ranges = LivenessAnalyzer.compute_live_ranges(ssa)
    # for k in live_ranges:
    #     print(k, live_ranges[k])
    
    # alloc = SSALinearScanRegisterAllocator(live_ranges, ['r0'])
    # a = alloc.allocations
    # for k in a:
    #     print(k, a[k])
    # print()

    # s = alloc.spills
    # for k in s:
    #     print(k, s[k])


    #copy_propagation(ic)
    #dead_code_elimination(ic)
    #SCCP.optimize(ic)

    # print('****************')
    # for bb in ic.bb_sequence:
    #     for instr in bb:
    #         print(f'{instr.op} {instr.arg1} {instr.arg2} {instr.result}' )
    # print('****************')



    

    #Otimização
    # optimize(ic)
    # print("\n\n\n**** TAC otimizado ****")
    # print(ic, '\n')
    # print('\n**** Interpretação do TAC Otimizado ****')
    # ic.interpret()



    #Geração de código x64
    #code = SSAX64CodeGenerator(ssa)
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
