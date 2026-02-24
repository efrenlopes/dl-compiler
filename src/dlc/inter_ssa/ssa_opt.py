from dlc.inter_ssa.ssa import SSA
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAConst, SSAOperand



@staticmethod
def optimize_ssa(ssa: SSA):
    changed = True

    while changed:
        changed = False
        changed |= copy_propagation(ssa)
        changed |= constant_folding(ssa)
        changed |= branch_folding(ssa)
        changed |= unreachable_code_elimination(ssa)
        changed |= phi_simplification(ssa)
        changed |= phi_simplification(ssa)
        changed |= dead_code_elimination(ssa)
        changed |= merge_blocks(ssa)

@staticmethod
def copy_propagation(ssa: SSA) -> bool:
    changed = False
    copies = {}

    # 1. Identificar cópias de forma exaustiva
    for bb in ssa.ic.bb_sequence:
        for instr in bb.instructions:
            if instr.op == SSAOperator.MOVE:
                target = instr.result
                source = instr.arg1
                # Se a fonte já é uma cópia de outra coisa, vai até a raiz
                while source in copies:
                    source = copies[source]
                if target != source:
                    copies[target] = source

    # 2. Substituir usos
    for bb in ssa.ic.bb_sequence:
        for instr in bb.instructions:

            # if instr.op == SSAOperator.PHI:
            #     # Otimização: Também podemos propagar para dentro das PHIs!
            #     phi_op = instr.arg1
            #     for block, version in phi_op.paths.items():
            #         if version in copies:
            #             phi_op.paths[block] = copies[version]
            #             changed = True
            #     continue 
            
            # Substituição padrão para arg1 e arg2
            if instr.arg1 in copies:
                instr.arg1 = copies[instr.arg1]
                changed = True
            if instr.arg2 in copies:
                instr.arg2 = copies[instr.arg2]
                changed = True
                
    return changed





@staticmethod
def constant_folding(ssa: SSA) -> bool:
    changed = False
    for bb in ssa.ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            # 1. Verificar se é uma operação binária onde ambos os argumentos são constantes
            if instr.op in SSA_IC.OPS and instr.arg1.is_const and (instr.arg2.is_const or instr.arg2 == SSAOperand.EMPTY):
                try:
                    # 2. Calcular o resultado em tempo de compilação
                    val1 = instr.arg1.value
                    val2 = instr.arg2.value if instr.arg2.is_const else None
                    result_value = SSA_IC.OPS[instr.op](val1, val2)
                    # 3. Transformar a instrução em um MOVE de constante
                    instr.op = SSAOperator.MOVE
                    instr.arg1 = SSAConst(instr.result.type, result_value)
                    instr.arg2 = SSAOperand.EMPTY
                    changed = True
                except ZeroDivisionError:
                    pass
            new_instrs.append(instr)
        bb.instructions = new_instrs
    return changed


@staticmethod
def branch_folding(ssa: SSA) -> bool:
    changed = False
    for bb in ssa.ic.bb_sequence[:]:
        for instr in bb.instructions:
            if instr.op == SSAOperator.IF:
                # Verifica se a condição do IF é uma constante
                if instr.arg1.is_const:
                    # Decide o caminho a ser tomado
                    keep_label, dead_label = (instr.arg2, instr.result) if instr.arg1.value else (instr.result, instr.arg2)
                    bb_dead = ssa.ic.bb_from_label(dead_label)
                    bb_dead.predecessors.remove(bb)
                    bb.successors.remove(bb_dead)
                    # Transforma o IF em um GOTO incondicional para o bloco correto
                    instr.op = SSAOperator.GOTO
                    instr.arg1 = SSAOperand.EMPTY
                    instr.arg2 = SSAOperand.EMPTY
                    instr.result = keep_label
                    changed = True
    return changed



@staticmethod
def unreachable_code_elimination(ssa: SSA) -> bool:
    changed = False
    reachable_labels = set()

    # 1. Coletar todos os labels que são alvos de saltos (GOTO ou IF)
    reachable_labels.add(ssa.ic.bb_sequence[0].instructions[0].result)
    for bb in ssa.ic.bb_sequence:
        for instr in bb.instructions:
            if instr.op == SSAOperator.GOTO:
                reachable_labels.add(instr.result) # Adapte para pegar o nome do label
            elif instr.op == SSAOperator.IF:
                reachable_labels.add(instr.arg2)
                reachable_labels.add(instr.result)

    # 2. Manter apenas os blocos que são o Entry Block (o primeiro) ou que têm um label atingível
    new_bb_sequence = []
    for bb in ssa.ic.bb_sequence:
        first_instr = bb.instructions[0]
        if first_instr.op == SSAOperator.LABEL and first_instr.result in reachable_labels:
            new_bb_sequence.append(bb)
        else:
            for succ in bb.successors:
                succ.predecessors.remove(bb)
            changed = True # Se o label não está na lista, o bloco morre
    ssa.ic.bb_sequence = new_bb_sequence
    return changed


@staticmethod
def phi_simplification(ssa: SSA):
    changed = False
    for bb in ssa.ic.bb_sequence:
        for instr in bb:
            if instr.op == SSAOperator.PHI:
                #Remove dos PHIs os BBs que não existem mais
                for bb in list(instr.arg1.paths):
                    if bb not in ssa.ic.bb_sequence:
                        changed = True
                        del instr.arg1.paths[bb]
                #PHIs com valor único são transformados em MOVEs
                if len(instr.arg1.paths) == 1:
                    instr.op = SSAOperator.MOVE
                    instr.arg1 = list(instr.arg1.paths.values())[0]
    return changed








@staticmethod
def dead_code_elimination(ssa: SSA) -> bool:
    changed = False
    use_count = {}

    # 1. Contagem rigorosa
    for bb in ssa.ic.bb_sequence:
        for instr in bb.instructions:
            # PHIs são usos
            if instr.op == SSAOperator.PHI:
                for version in instr.arg1.paths.values():
                    if version.is_temp_version:
                        use_count[version] = use_count.get(version, 0) + 1
            else:
                # IMPORTANTÍSSIMO: Contar usos em arg1 e arg2 de QUALQUER instrução
                # Isso inclui o argumento do IF, do PRINT e de operações matemáticas
                for op in (instr.arg1, instr.arg2):
                    if op.is_temp_version:
                        use_count[op] = use_count.get(op, 0) + 1

    # 2. Remoção
    for bb in ssa.ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            # Nunca apagar instruções que têm efeitos colaterais ou controle de fluxo
            # mesmo que o 'result' delas seja vago.
            if instr.op in (SSAOperator.PRINT, SSAOperator.READ, SSAOperator.IF, SSAOperator.GOTO, SSAOperator.LABEL):
                new_instrs.append(instr)
                continue

            # Se a instrução gera um resultado e ninguém usa...
            res = instr.result
            if res and res.is_temp_version:
                if use_count.get(res, 0) == 0:
                    changed = True
                    continue
            
            new_instrs.append(instr)
        bb.instructions = new_instrs
    return changed




@staticmethod
def merge_blocks(ssa: SSA):
    changed = False
    i = 0
    while i < len(ssa.ic.bb_sequence):
        bb = ssa.ic.bb_sequence[i]
        if len(bb.successors) == 1:
            succ = bb.successors[0]
            if len(succ.predecessors) == 1 and succ != bb:
                # Corrigir PHIs nos sucessores do bloco que vai sumir
                for grandson in succ.successors:
                    for instr in grandson.instructions:
                        if instr.op == SSAOperator.PHI:
                            phi_op = instr.arg1
                            # Se a PHI esperava algo vindo de 'succ', agora vem de 'bb'
                            if succ in phi_op.paths:
                                phi_op.paths[bb] = phi_op.paths.pop(succ)
                
                # --- Lógica de fusão que você já tinha ---
                bb.instructions.pop() # Remove o GOTO
                bb.instructions.extend(succ.instructions[1:]) # Anexa instruções (sem o LABEL)
                
                bb.successors = succ.successors
                for s in bb.successors:
                    s.predecessors = [bb if p == succ else p for p in s.predecessors]
                
                ssa.ic.bb_sequence.remove(succ)
                changed = True
                continue 
        i += 1
    return changed


# @staticmethod
# def merge_blocks(ssa: SSA):
#     changed = False
#     new_bb_sequence = []
#     for bb in ssa.ic.bb_sequence[:]:
#         # Só podemos fundir se:
#         # 1. bb tem exatamente 1 sucessor (succ)
#         # 2. succ tem exatamente 1 predecessor (bb)
#         if len(bb.successors) == 1:
#             succ = bb.successors[0]
#             if len(succ.predecessors) == 1 and len(succ.instructions) == 2 :
#                 bb.instructions.pop() #remove o goto
#                 bb.instructions.extend(succ.instructions[1:]) #anexa o sucessor ao bb



#                 bb.successors = succ.successors #bb herda os sucessores do seu sucessor
                
#                 for s in bb.successors: # Atualiza os predecessores dos novos sucessores
#                     s.predecessors = [bb if p == succ else p for p in s.predecessors]
#                 succ.instructions.clear()
#                 succ.predecessors.clear()
#                 succ.successors.clear()
#                 #ssa.ic.bb_sequence.remove(succ) # Remove bloco da lista global

#                 changed = True
#                 continue
#         new_bb_sequence.append(bb)
#     ssa.ic.bb_sequence = new_bb_sequence
#     return changed

