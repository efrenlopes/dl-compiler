from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAConst, SSAOperand



@staticmethod
def optimize_ssa(ic: SSA_IC):
    changed = True
    while changed:
        changed = False
        changed |= copy_propagation(ic)

        changed |= constant_folding(ic)

        changed |= dead_code_elimination(ic)

        #changed |= simplify_cfg(ic)

        changed |= remove_unreachable_blocks(ic)


@staticmethod
def copy_propagation(ic: SSA_IC) -> bool:
    changed = False
    copies = {}

    # 1. Identificar cópias de forma exaustiva
    for bb in ic.bb_sequence:
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
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            if instr.op == SSAOperator.PHI:
                # Otimização: Também podemos propagar para dentro das PHIs!
                phi_op = instr.arg1
                for block, version in phi_op.paths.items():
                    if version in copies:
                        phi_op.paths[block] = copies[version]
                        changed = True
                continue 
            
            # Substituição padrão para arg1 e arg2
            if instr.arg1 in copies:
                instr.arg1 = copies[instr.arg1]
                changed = True
            if instr.arg2 in copies:
                instr.arg2 = copies[instr.arg2]
                changed = True
                
    return changed





@staticmethod
def constant_folding(ic: SSA_IC) -> bool:
    changed = False

    for bb in ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            # 1. Verificar se é uma operação binária onde ambos os argumentos são constantes
            # (Assumindo que seus operandos tenham algo como .is_constant ou .value)
            if instr.op in SSA_IC.OPS and instr.arg1.is_const and instr.arg2.is_const:
                try:
                    # 2. Calcular o resultado em tempo de compilação
                    val1 = instr.arg1.value
                    val2 = instr.arg2.value
                    result_value = SSA_IC.OPS[instr.op](val1, val2)

                    # 3. Transformar a instrução complexa em um MOVE constante
                    # Ex: t3_1 = 5 * 2  ==>  t3_1 = 10
                    instr.op = SSAOperator.MOVE
                    instr.arg1 = SSAConst(instr.result.type, result_value)
                    instr.arg2 = SSAOperand.EMPTY
                    
                    changed = True
                except ZeroDivisionError:
                    # Se houver divisão por zero, deixamos para o tempo de execução 
                    # ou emitimos um aviso.
                    pass
            
            # Dentro do loop de instruções do constant_folding:
            elif instr.op == SSAOperator.IF and instr.arg1.is_const:
                condicao = instr.arg1.value is True
                # Se a condição for verdadeira, vai para o primeiro destino (L1)
                # Se for falsa, vai para o segundo (L2)
                destino = instr.arg2 if condicao else instr.result
                
                instr.op = SSAOperator.GOTO
                instr.arg1 = SSAOperand.EMPTY
                instr.arg2 = SSAOperand.EMPTY
                instr.result = destino
                changed = True


            new_instrs.append(instr)
        bb.instructions = new_instrs

    return changed





@staticmethod
def dead_code_elimination(ic: SSA_IC) -> bool:
    changed = False
    use_count = {}

    # 1. Contagem rigorosa
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            # PHIs são usos
            if instr.op == SSAOperator.PHI:
                for version in instr.arg1.paths.values():
                    use_count[version] = use_count.get(version, 0) + 1
            else:
                # IMPORTANTÍSSIMO: Contar usos em arg1 e arg2 de QUALQUER instrução
                # Isso inclui o argumento do IF, do PRINT e de operações matemáticas
                for op in (instr.arg1, instr.arg2):
                    if hasattr(op, 'is_temp_version') and op.is_temp_version:
                        use_count[op] = use_count.get(op, 0) + 1

    # 2. Remoção
    for bb in ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            # Nunca apagar instruções que têm efeitos colaterais ou controle de fluxo
            # mesmo que o 'result' delas seja vago.
            if instr.op in (SSAOperator.PRINT, SSAOperator.IF, SSAOperator.GOTO, SSAOperator.LABEL):
                new_instrs.append(instr)
                continue

            # Se a instrução gera um resultado e ninguém usa...
            res = instr.result
            if res and hasattr(res, 'is_temp_version') and res.is_temp_version:
                if use_count.get(res, 0) == 0:
                    changed = True
                    continue # Deleta
            
            new_instrs.append(instr)
        bb.instructions = new_instrs
    return changed




@staticmethod
def remove_unreachable_blocks(ic: SSA_IC) -> bool:
    # 1. Identificar blocos alcançáveis a partir do entry (BFS ou DFS)
    reachable = set()
    stack = [ic.bb_sequence[0]]
    while stack:
        curr = stack.pop()
        if curr not in reachable:
            reachable.add(curr)
            stack.extend(curr.successors)

    # 2. Filtrar a sequência de blocos
    if len(reachable) == len(ic.bb_sequence):
        return False

    original_count = len(ic.bb_sequence)
    ic.bb_sequence = [bb for bb in ic.bb_sequence if bb in reachable]
    
    # 3. Limpar as referências de predecessores nos blocos que ficaram
    for bb in ic.bb_sequence:
        bb.predecessors = [p for p in bb.predecessors if p in reachable]
        
    return len(ic.bb_sequence) < original_count



@staticmethod
def simplify_cfg(ic: SSA_IC) -> bool:
    changed = False
    for bb in ic.bb_sequence:
        # Verifica se o bloco é apenas um Label + Goto
        # (Ajuste o índice conforme sua estrutura de label)
        instrs = [i for i in bb.instructions if i.op != SSAOperator.LABEL]
        
        if len(instrs) == 1 and instrs[0].op == SSAOperator.GOTO:
            target_label = instrs[0].result # Destino do goto
            target_bb = next(b for b in ic.bb_sequence if ic.bb_from_label(label) == target_label)
            
            if target_bb == bb: continue # Evita loop infinito em si mesmo

            # Redirecionar todos os predecessores de 'bb' para 'target_bb'
            for pred in bb.predecessors[:]:
                last_instr = pred.instructions[-1]
                
                # Se o predecessor era um GOTO ou IF, atualizamos o destino
                if last_instr.op == SSAOperator.GOTO:
                    last_instr.result = target_label
                elif last_instr.op == SSAOperator.IF:
                    if last_instr.arg2 == bb.label: last_instr.arg2 = target_label
                    if last_instr.result == bb.label: last_instr.result = target_label
                
                # Atualiza os links de sucessores/predecessores no grafo
                pred.successors.remove(bb)
                pred.successors.append(target_bb)
                target_bb.predecessors.append(pred)
                bb.predecessors.remove(pred)
                changed = True
    return changed


@staticmethod
def phi_pruning(ic: SSA_IC) -> bool:
    changed = False
    for bb in ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            if instr.op == SSAOperator.PHI:
                phi_op = instr.arg1
                # Remove caminhos de blocos que não existem mais no CFG
                # (Importante caso você tenha removido blocos inalcançáveis)
                valid_paths = {b: v for b, v in phi_op.paths.items() if b in bb.predecessors}
                phi_op.paths = valid_paths

                # Se a PHI tem apenas 1 caminho, ela vira um MOVE
                if len(valid_paths) == 1:
                    val = list(valid_paths.values())[0]
                    instr.op = SSAOperator.MOVE
                    instr.arg1 = val
                    changed = True
                
                # Se todos os caminhos levam ao mesmo valor, vira um MOVE
                elif len(set(valid_paths.values())) == 1:
                    val = list(valid_paths.values())[0]
                    instr.op = SSAOperator.MOVE
                    instr.arg1 = val
                    changed = True

            new_instrs.append(instr)
        bb.instructions = new_instrs
    return changed