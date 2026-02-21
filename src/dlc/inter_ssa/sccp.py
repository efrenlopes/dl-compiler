from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAConst, SSAOperand



@staticmethod
def optimize_ssa(ic: SSA_IC):
    changed = True
    while changed:
        changed = False
        changed |= copy_propagation(ic)
        changed |= dead_code_elimination(ic)


@staticmethod
def copy_propagation(ic: SSA_IC) -> bool:
    changed = False
    copies = {}

    # 1. Identificar cópias (inclusive de constantes)
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            if instr.op == SSAOperator.MOVE:
                val_original = instr.arg1
                if val_original in copies:
                    val_original = copies[val_original]
                copies[instr.result] = val_original

    # 2. Substituir usos, PROTEGENDO as PHIs
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            # Se for PHI, não substituímos os argumentos por literais
            if instr.op == SSAOperator.PHI:
                continue 
            
            # Para as demais instruções, substituímos
            if instr.arg1 in copies:
                instr.arg1 = copies[instr.arg1]
                changed = True
            if instr.arg2 in copies:
                instr.arg2 = copies[instr.arg2]
                changed = True
                
    return changed



@staticmethod
def dead_code_elimination(ic: SSA_IC) -> bool:
    changed = False
    use_count = {}

    # 1. Contagem rigorosa de todos os usos
    for bb in ic.bb_sequence:
        for instr in bb.instructions:
            # Usos em argumentos normais
            for op in [instr.arg1, instr.arg2]:
                if op and (op.is_temp or op.is_temp_version):
                    use_count[op] = use_count.get(op, 0) + 1
            
            # Usos dentro de PHIs (isso salva as definições de variáveis)
            if instr.op == SSAOperator.PHI:
                phi_op = instr.arg1
                for version in phi_op.paths.values():
                    if version and version.is_temp_version:
                        use_count[version] = use_count.get(version, 0) + 1

    # 2. Remoção de instruções inúteis
    for bb in ic.bb_sequence:
        new_instrs = []
        for instr in bb.instructions:
            # Instruções com efeitos colaterais ou controle de fluxo NUNCA saem
            if instr.op in [SSAOperator.PRINT, SSAOperator.IF, SSAOperator.IFFALSE, 
                            SSAOperator.GOTO, SSAOperator.STORE]:
                new_instrs.append(instr)
                continue
            
            # Se a instrução gera um resultado que ninguém usa, ela morre
            if instr.result and (instr.result.is_temp or instr.result.is_temp_version):
                if use_count.get(instr.result, 0) == 0:
                    changed = True
                    continue 
            
            new_instrs.append(instr)
        
        bb.instructions = new_instrs

    return changed



class SCCP:
    # Estados do Lattice
    TOP = 0       # Ainda não visitado
    CONSTANT = 1  # Valor constante conhecido
    BOTTOM = 2    # Não é constante (Varying)

    @staticmethod
    def optimize(ic: SSA_IC) -> bool:
        lattice = {}  # {SSAOperand: (status, value)}
        executable_blocks = set()
        ssa_worklist = []
        flow_worklist = [ic.bb_sequence[0]]
        
        changed_anything = False

        # --- Mapeamentos auxiliares ---
        instr_to_bb = {}
        uses = {}
        for bb in ic.bb_sequence:
            for instr in bb.instructions:
                instr_to_bb[instr] = bb
                # Mapeia quais instruções usam cada operando (para a worklist SSA)
                for op in [instr.arg1, instr.arg2]:
                    if op and op.is_temp_version:
                        uses.setdefault(op, []).append(instr)

        def get_lattice(op):
            if op is None or op == "" or op == SSAOperand.EMPTY: return (SCCP.TOP, None)
            if op.is_const: return (SCCP.CONSTANT, op.value)
            if not op.is_temp_version: return (SCCP.BOTTOM, None)
            return lattice.get(op, (SCCP.TOP, None))

        def set_lattice(op, status, value=None):
            if not op or not op.is_temp_version: return False
            prev_status, prev_val = get_lattice(op)
            if (prev_status, prev_val) != (status, value):
                lattice[op] = (status, value)
                return True
            return False

        # --- LOOP DE ANÁLISE (SIMULAÇÃO) ---
        while flow_worklist or ssa_worklist:
            # 1. Processar novos caminhos de fluxo (Blocos Básicos)
            if flow_worklist:
                bb = flow_worklist.pop(0)
                if bb not in executable_blocks:
                    executable_blocks.add(bb)
                    # Ao ativar um bloco, todas as suas instruções entram na fila
                    ssa_worklist.extend(bb.instructions)

            # 2. Processar instruções (Fluxo de Dados)
            if ssa_worklist:
                instr = ssa_worklist.pop(0)
                bb_atual = instr_to_bb.get(instr)
                if bb_atual not in executable_blocks:
                    continue

                status_changed = False
                
                # Operador MOVE (Essencial para propagar t0_1 -> t2)
                if instr.op == SSAOperator.MOVE:
                    st, val = get_lattice(instr.arg1)
                    status_changed = set_lattice(instr.result, st, val)

                # Operadores Aritméticos e Lógicos (Onde ocorre o FOLDING)
                elif instr.op in [SSAOperator.SUM, SSAOperator.SUB, SSAOperator.MUL, 
                                 SSAOperator.DIV, SSAOperator.EQ, SSAOperator.NE,
                                 SSAOperator.LT, SSAOperator.GT, SSAOperator.LE, SSAOperator.GE]:
                    st1, v1 = get_lattice(instr.arg1)
                    st2, v2 = get_lattice(instr.arg2)
                    
                    if st1 == SCCP.BOTTOM or st2 == SCCP.BOTTOM:
                        status_changed = set_lattice(instr.result, SCCP.BOTTOM)
                    elif st1 == SCCP.CONSTANT and st2 == SCCP.CONSTANT:
                        # Executa a operação em tempo de compilação
                        res_val = ic.operate(instr.op, v1, v2)
                        status_changed = set_lattice(instr.result, SCCP.CONSTANT, res_val)
                
                # Funções PHI
                elif instr.op == SSAOperator.PHI:
                    phi_op = instr.arg1
                    current_status, current_val = SCCP.TOP, None
                    
                    for pred_bb, version in phi_op.paths.items():
                        # Só considera valores de arestas que o fluxo já provou serem executáveis
                        if pred_bb in executable_blocks:
                            st, val = get_lattice(version)
                            if st == SCCP.BOTTOM:
                                current_status = SCCP.BOTTOM
                                break
                            elif st == SCCP.CONSTANT:
                                if current_status == SCCP.TOP:
                                    current_status, current_val = st, val
                                elif current_val != val:
                                    current_status = SCCP.BOTTOM
                                    break
                    status_changed = set_lattice(instr.result, current_status, current_val)

                # Controle de Fluxo (Decide quais próximos blocos ativar)
                elif instr.op in [SSAOperator.IF, SSAOperator.IFFALSE, SSAOperator.GOTO]:
                    if instr.op == SSAOperator.GOTO:
                        flow_worklist.extend(bb_atual.successors)
                    else:
                        st, val = get_lattice(instr.arg1)
                        if st == SCCP.CONSTANT:
                            # Aqui você poderia ativar apenas o sucessor True ou False
                            # Para segurança, ativamos todos, mas a PHI filtrará pelo lattice
                            flow_worklist.extend(bb_atual.successors)
                        elif st == SCCP.BOTTOM:
                            flow_worklist.extend(bb_atual.successors)

                # Se o valor do resultado mudou, re-adiciona quem usa ele na fila
                if status_changed:
                    for user_instr in uses.get(instr.result, []):
                        if user_instr not in ssa_worklist:
                            ssa_worklist.append(user_instr)

        # --- FASE DE SUBSTITUIÇÃO (TRANSFORMAÇÃO REAL) ---
        for bb in ic.bb_sequence:
            if bb not in executable_blocks:
                bb.instructions = [] # Opcional: Remove blocos mortos
                continue

            for instr in bb.instructions:
                # 1. Substitui argumentos por constantes conhecidas
                for attr in ['arg1', 'arg2']:
                    op = getattr(instr, attr)
                    if op and op.is_temp_version:
                        st, val = get_lattice(op)
                        if st == SCCP.CONSTANT:
                            setattr(instr, attr, SSAConst(op.type, val))
                            changed_anything = True
                
                # 2. Se a instrução resultou em uma constante, simplifica para um MOVE
                # (Ignoramos PHI aqui pois elas são resolvidas na substituição de argumentos)
                if instr.op not in [SSAOperator.PHI, SSAOperator.MOVE, SSAOperator.PRINT]:
                    st, val = get_lattice(instr.result)
                    if st == SCCP.CONSTANT:
                        instr.op = SSAOperator.MOVE
                        instr.arg1 = SSAConst(instr.result.type, val)
                        instr.arg2 = None
                        changed_anything = True

        return changed_anything