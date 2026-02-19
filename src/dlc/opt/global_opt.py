from dlc.inter.ic import IC
from dlc.inter.instr import Instr
from dlc.inter.operand import Const, Operand, Temp
from dlc.inter.operator import Operator


class Lattice:
    TOP = "TOP"       # Indefinido (ainda não visitado)
    BOTTOM = "BOTTOM" # Não é constante (valor varia)

    @staticmethod
    def meet(v1, v2):
        """Função de encontro (Meet Operator ∧)"""
        if v1 == Lattice.BOTTOM or v2 == Lattice.BOTTOM:
            return Lattice.BOTTOM
        if v1 == Lattice.TOP:
            return v2
        if v2 == Lattice.TOP:
            return v1
        if v1 == v2:
            return v1
        return Lattice.BOTTOM # Constantes diferentes (ex: 5 ∧ 6)


@staticmethod
def optimize(ic):
    changed = True
    while changed:
        changed = False
        
        # 1. Resolve a matemática (Folding + Constant Prop)
        # Transforma t1 = 10 + 5 em t1 = 15
        changed |= global_constant_propagation_and_folding(ic)
        
        # 2. Conecta os nomes (Copy Prop)
        # Se tinha v2 = t1, ele troca o uso de v2 por t1 lá na frente
        changed |= global_copy_propagation(ic)
        
        # 3. Limpa os mortos (DCE)
        # Se t1 virou 15 e ninguém mais lê t1, ele apaga a linha t1 = 15
        changed |= global_dead_code_elimination(ic)

        changed |= simplify_graph_branches(ic)
    




@staticmethod
def global_constant_propagation_and_folding(ic):
    all_vars = set()
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            for op in [instr.result, instr.arg1, instr.arg2]:
                if isinstance(op, Temp):
                    all_vars.add(op)

    in_states = {bb: {v: Lattice.TOP for v in all_vars} for bb in ic.bb_sequence}
    out_states = {bb: {v: Lattice.TOP for v in all_vars} for bb in ic.bb_sequence}
    
    worklist = list(ic.bb_sequence)

    while worklist:
        bb = worklist.pop(0)

        # MEET
        if bb.predecessors:
            new_in = {v: Lattice.TOP for v in all_vars}
            for pred in bb.predecessors:
                for v in all_vars:
                    new_in[v] = Lattice.meet(new_in[v], out_states[pred][v])
            in_states[bb] = new_in

        # TRANSFER + FOLDING INTEGRADO
        old_out = out_states[bb].copy()
        current_vals = in_states[bb].copy()

        for instr in bb.instructions:
            # 1. Resolve os operandos (Lattice ou constante literal)
            val1 = current_vals.get(instr.arg1) if isinstance(instr.arg1, Temp) else instr.arg1.value if isinstance(instr.arg1, Const) else None
            val2 = current_vals.get(instr.arg2) if isinstance(instr.arg2, Temp) else instr.arg2.value if isinstance(instr.arg2, Const) else None

            res_lat = Lattice.BOTTOM

            # 2. Tenta o Folding durante a análise
            if instr.op == Operator.MOVE:
                res_lat = val1 if val1 is not None else Lattice.BOTTOM
            elif instr.op in IC.OPS:
                # Se ambos os operandos viraram constantes numéricas, calculamos AGORA
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    try:
                        res_lat = IC.operate(instr.op, val1, val2)
                    except Exception:
                        res_lat = Lattice.BOTTOM
                elif isinstance(val1, (int, float)) and (instr.arg2 == Operand.EMPTY or instr.arg2 is None):
                    try:
                        res_lat = IC.operate_unary(instr.op, val1)
                    except Exception:
                        res_lat = Lattice.BOTTOM
            
            if isinstance(instr.result, Temp):
                current_vals[instr.result] = res_lat

        out_states[bb] = current_vals
        if out_states[bb] != old_out:
            for succ in bb.successors:
                if succ not in worklist:
                    worklist.append(succ)

    # 3. APPLY (Reescreve o TAC com as constantes e as contas resolvidas)
    return apply_global_folding(ic, in_states)



@staticmethod
def apply_global_folding(ic, in_states):
    changed = False
    for bb in ic.bb_sequence:
        # Começamos com os valores conhecidos na entrada do bloco
        current_vals = in_states[bb].copy()
        
        for instr in bb.instructions:
            # --- PASSO 1: SUBSTITUIÇÃO DE USOS ---
            # Verifica se os argumentos da instrução atual são constantes conhecidas
            if isinstance(instr.arg1, Temp):
                val = current_vals.get(instr.arg1)
                if isinstance(val, (int, float)):
                    instr.arg1 = Const(instr.arg1.type, val)
                    changed = True
            
            if isinstance(instr.arg2, Temp):
                val = current_vals.get(instr.arg2)
                if isinstance(val, (int, float)):
                    instr.arg2 = Const(instr.arg2.type, val)
                    changed = True

            # --- PASSO 2: CONSTANT FOLDING (SIMPLIFICAÇÃO) ---
            # Agora que substituímos os argumentos, verificamos se podemos resolver a operação
            val1 = instr.arg1.value if isinstance(instr.arg1, Const) else None
            val2 = instr.arg2.value if isinstance(instr.arg2, Const) else None
            
            res_lat = Lattice.BOTTOM

            if instr.op == Operator.MOVE:
                # Se for MOVE de uma constante, o resultado é essa constante
                res_lat = val1 if val1 is not None else Lattice.BOTTOM
                
            elif instr.op in IC.OPS:
                # Se os operandos necessários são constantes, calculamos o resultado
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    try:
                        res_lat = IC.operate(instr.op, val1, val2)
                        # Transforma a conta em um MOVE constante: t1 = 10 + 5 -> t1 = 15
                        instr.op = Operator.MOVE
                        instr.arg1 = Const(instr.result.type, res_lat)
                        instr.arg2 = Operand.EMPTY
                        changed = True
                    except Exception:
                        res_lat = Lattice.BOTTOM
                
                # Caso para operações unárias (ex: NOT, NEG)
                elif isinstance(val1, (int, float)) and (instr.arg2 in (Operand.EMPTY, None)):
                    try:
                        res_lat = IC.operate_unary(instr.op, val1)
                        instr.op = Operator.MOVE
                        instr.arg1 = Const(instr.result.type, res_lat)
                        changed = True
                    except Exception:
                        res_lat = Lattice.BOTTOM

            # --- PASSO 3: ATUALIZAÇÃO DO ESTADO LOCAL ---
            # Atualizamos o dicionário para que a PRÓXIMA linha do mesmo bloco 
            # já veja os valores atualizados por esta linha
            if isinstance(instr.result, Temp):
                current_vals[instr.result] = res_lat
                
    return changed




@staticmethod
def global_copy_propagation(ic):
    all_vars = set()
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            for op in [instr.result, instr.arg1, instr.arg2]:
                if isinstance(op, Temp):
                    all_vars.add(op)

    # IN e OUT guardam um dicionário { var_destino: var_origem }
    # Inicializamos com todas as cópias possíveis (Universal Set) para a interseção funcionar
    # Exceto o bloco de entrada, que começa vazio.
    in_states = {bb: {} for bb in ic.bb_sequence}
    out_states = {bb: {v: v for v in all_vars} for bb in ic.bb_sequence} # Estado "Universal"
    
    ic.bb_sequence[0].predecessors = [] # Garantir entrada
    out_states[ic.bb_sequence[0]] = {} 

    worklist = list(ic.bb_sequence)

    while worklist:
        bb = worklist.pop(0)

        # 1. MEET (Interseção das cópias que vêm de todos os predecessores)
        if bb.predecessors:
            new_in = None
            for pred in bb.predecessors:
                if new_in is None:
                    new_in = out_states[pred].copy()
                else:
                    # Interseção: apenas cópias presentes em TODOS os caminhos
                    new_in = {k: v for k, v in new_in.items() 
                                if k in out_states[pred] and out_states[pred][k] == v}
            in_states[bb] = new_in or {}

        # 2. TRANSFER
        old_out = out_states[bb].copy()
        current_copies = in_states[bb].copy()

        for instr in bb.instructions:
            # Se a instrução é v2 = t1 (MOVE entre registradores)
            if instr.op == Operator.MOVE and isinstance(instr.result, Temp) and isinstance(instr.arg1, Temp):
                # v2 agora é uma cópia de t1 (ou de quem t1 já era cópia)
                src = current_copies.get(instr.arg1, instr.arg1)
                current_copies[instr.result] = src
            
            # KILL: Se a variável é alterada, ela não pode mais ser destino nem origem de cópias
            elif isinstance(instr.result, Temp):
                res = instr.result
                # Remove se ela era o destino: v2 = ...
                current_copies.pop(res, None)
                # Remove qualquer par onde ela era a origem: ... = v2
                current_copies = {k: v for k, v in current_copies.items() if v != res}

        out_states[bb] = current_copies

        if out_states[bb] != old_out:
            for succ in bb.successors:
                if succ not in worklist:
                    worklist.append(succ)

    # 3. APPLY
    return apply_copy_propagation(ic, in_states)

@staticmethod
def apply_copy_propagation(ic, in_states):
    changed = False
    for bb in ic.bb_sequence:
        current_copies = in_states[bb].copy()
        for instr in bb.instructions:
            # Substitui arg1 e arg2 se houver uma cópia disponível
            if isinstance(instr.arg1, Temp) and instr.arg1 in current_copies:
                instr.arg1 = current_copies[instr.arg1]
                changed = True
            if isinstance(instr.arg2, Temp) and instr.arg2 in current_copies:
                instr.arg2 = current_copies[instr.arg2]
                changed = True
            
            # Atualiza o estado local para a próxima instrução
            if instr.op == Operator.MOVE and isinstance(instr.result, Temp) and isinstance(instr.arg1, Temp):
                current_copies[instr.result] = current_copies.get(instr.arg1, instr.arg1)
            elif isinstance(instr.result, Temp):
                res = instr.result
                current_copies.pop(res, None)
                current_copies = {k: v for k, v in current_copies.items() if v != res}
    return changed



@staticmethod
def global_dead_code_elimination(ic):
    # 1. ANÁLISE DE VIVACIDADE (Liveness Analysis)
    # Inicializa IN e OUT de cada bloco como conjuntos vazios
    in_sets = {bb: set() for bb in ic.bb_sequence}
    out_sets = {bb: set() for bb in ic.bb_sequence}
    
    worklist = list(reversed(ic.bb_sequence))
    
    while worklist:
        bb = worklist.pop(0)
        
        # OUT[bb] = união dos INs de todos os sucessores
        new_out = set()
        for succ in bb.successors:
            new_out.update(in_sets[succ])
        out_sets[bb] = new_out
        
        # IN[bb] = (OUT[bb] - DEFs) + USEs
        # Processamos as instruções do bloco de trás para frente para calcular o IN
        current_live = out_sets[bb].copy()
        for instr in reversed(bb.instructions):
            # Se a instrução define algo, isso "mata" a vivacidade para cima
            if isinstance(instr.result, Temp):
                current_live.discard(instr.result)
            # Se a instrução usa algo, isso "gera" vivacidade para cima
            if isinstance(instr.arg1, Temp):
                current_live.add(instr.arg1)
            if isinstance(instr.arg2, Temp):
                current_live.add(instr.arg2)
        
        if current_live != in_sets[bb]:
            in_sets[bb] = current_live
            # Se o IN mudou, os predecessores precisam ser reanalisados
            for pred in bb.predecessors:
                if pred not in worklist:
                    worklist.append(pred)

    # 2. ELIMINAÇÃO (Baseada na análise)
    changed = False
    for bb in ic.bb_sequence:
        new_instrs = []
        # Começamos com as variáveis vivas na SAÍDA do bloco
        live_at_this_point = out_sets[bb].copy()
        
        # Analisamos de trás para frente para saber o que está vivo em cada linha
        for instr in reversed(bb.instructions):
            is_dead = False
            res = instr.result
            
            # Regra de Ouro do DCE:
            # Uma instrução é morta se:
            # 1. O resultado é um Temp (registrador/variável)
            # 2. Esse Temp NÃO está vivo no momento
            # 3. A instrução não tem efeitos colaterais (como PRINT ou CALL)
            if isinstance(res, Temp):
                if res not in live_at_this_point and instr.op not in (Operator.PRINT, Operator.READ):
                    is_dead = True
            
            if is_dead:
                changed = True
                continue # Remove a instrução
            
            # Se não for removida, atualizamos o que está vivo para a linha de cima
            if isinstance(instr.result, Temp):
                live_at_this_point.discard(instr.result)
            if isinstance(instr.arg1, Temp):
                live_at_this_point.add(instr.arg1)
            if isinstance(instr.arg2, Temp):
                live_at_this_point.add(instr.arg2)
            
            new_instrs.append(instr)
        
        bb.instructions = list(reversed(new_instrs))
        
    return changed



@staticmethod
def simplify_graph_branches(ic: IC):
    changed = False
    
    for bb in ic.bb_sequence:
        if not bb.instructions:
            continue
        last = bb.instructions[-1]
        
        # Foco: Transformar IFFALSE constante em GOTO ou nada
        if last.op == Operator.IFFALSE and last.arg1.is_const:
            val = last.arg1.value
            target_label = last.result
            
            # Identifica quem é quem nos sucessores originais
            # (Assume-se que seu construtor colocou o alvo em [0] e fallthrough em [1])
            target_bb = bb.successors[0] #next((s for s in bb.successors if s.instructions and s.instructions[0] == target_label), None)
            fallthrough_bb = bb.successors[1] #next((s for s in bb.successors if s != target_bb), None)

            if not target_bb or not fallthrough_bb:
                continue

            changed = True
            if val == 0: # IFFALSE 0 -> SEMPRE PULA
                # 1. Transforma a instrução em GOTO
                bb.instructions[-1] = Instr(Operator.GOTO, Operand.EMPTY, Operand.EMPTY, target_label)
                # 2. Desconecta o caminho que não será seguido
                bb.successors.remove(fallthrough_bb)
                fallthrough_bb.predecessors.remove(bb)
            else: # IFFALSE 1 -> NUNCA PULA
                # 1. Remove a instrução de salto (o fluxo apenas "cai" no próximo)
                bb.instructions.pop()
                # 2. Desconecta o caminho do pulo
                bb.successors.remove(target_bb)
                target_bb.predecessors.remove(bb)

    # APÓS simplificar as arestas, chame a limpeza
    if changed:
        remove_unreachable_blocks(ic)
        merge_blocks(ic)

    return changed


@staticmethod
def remove_unreachable_blocks(ic):
    if not ic.bb_sequence:
        return False

    # 1. Encontrar todos os blocos alcançáveis usando DFS
    reachable = set()
    stack = [ic.bb_sequence[0]] # Começa pelo bb0
    
    while stack:
        curr = stack.pop()
        if curr not in reachable:
            reachable.add(curr)
            # Adiciona todos os sucessores à pilha para explorar
            stack.extend(curr.successors)
            
    # Se todos são alcançáveis, nada a fazer
    if len(reachable) == len(ic.bb_sequence):
        return False

    # 2. Antes de remover, desconectar os blocos mortos dos vivos
    unreachable = [bb for bb in ic.bb_sequence if bb not in reachable]
    for dead_bb in unreachable:
        # Avisar aos sucessores que este bloco não aponta mais para eles
        for succ in dead_bb.successors:
            if dead_bb in succ.predecessors:
                succ.predecessors.remove(dead_bb)
        # Limpar as próprias listas do bloco morto por segurança
        dead_bb.successors.clear()
        dead_bb.predecessors.clear()

    # 3. Filtrar a sequência global
    ic.bb_sequence = [bb for bb in ic.bb_sequence if bb in reachable]
    return True

@staticmethod
def merge_blocks(ic):
    changed = False
    i = 0
    while i < len(ic.bb_sequence) - 1:
        curr = ic.bb_sequence[i]
        
        # Só podemos fundir se:
        # 1. curr tem exatamente 1 sucessor (succ)
        # 2. succ tem exatamente 1 predecessor (curr)
        if len(curr.successors) == 1:
            succ = curr.successors[0]
            if len(succ.predecessors) == 1:
                # FUNDIR!
                # a) Remove instrução de pulo incondicional (GOTO) no final de curr se houver
                if curr.instructions and curr.instructions[-1].op == Operator.GOTO:
                    curr.instructions.pop()
                
                # b) Anexa instruções do sucessor no atual
                # Se a primeira instrução do sucessor for um LABEL, podemos ignorá-lo na fusão
                start_idx = 1 if succ.instructions and succ.instructions[0].op == Operator.LABEL else 0
                curr.instructions.extend(succ.instructions[start_idx:])
                
                # c) O atual herda os sucessores do bloco "comido"
                curr.successors = succ.successors
                
                # d) Atualizar os predecessores dos novos sucessores
                for s in curr.successors:
                    s.predecessors = [p if p != succ else curr for p in s.predecessors]
                
                # e) Remover o bloco succ da lista global e reiniciar o teste no curr atual
                ic.bb_sequence.remove(succ)
                changed = True
                continue 
        i += 1
    return changed