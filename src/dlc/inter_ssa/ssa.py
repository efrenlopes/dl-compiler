from dlc.inter.basic_block import BasicBlock
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAOperand, SSAPhi, SSATempVersion


#### Pensar em como fazer todas os temporários do SSA versionados!!!!!!!

class SSA:
    def __init__(self, ssa_ic: SSA_IC):
        self.ic = ssa_ic
        self.dom = self._compute_dominators()
        self.idom = self._compute_idom()  # Dominador Imediato
        self.dom_tree = self._build_dom_tree()
        self.df = self._compute_dominance_frontier()
        self.phi = self._insert_phi()
        self.rename()

        

    def _compute_dominators(self):
        basic_blocks = self.ic.bb_sequence
        entry = basic_blocks[0]
        dom = {}

        for bb in basic_blocks:
            if bb == entry:
                dom[bb] = {bb}
            else:
                dom[bb] = set(basic_blocks)

        changed = True
        while changed:
            changed = False
            for bb in basic_blocks:
                if bb == entry:
                    continue

                new_dom = set(basic_blocks)
                for p in bb.predecessors:
                    new_dom &= dom[p]
                new_dom.add(bb)

                if new_dom != dom[bb]:
                    dom[bb] = new_dom
                    changed = True

        return dom
    

    def _compute_idom(self):
        basic_blocks = self.ic.bb_sequence
        entry = basic_blocks[0]
        idom = {entry: None}

        for b in basic_blocks:
            if b == entry:
                continue

            strict_doms = self.dom[b] - {b}

            # idom é o dominador estrito que não é dominado por outro
            for d in strict_doms:
                if all(d == other or d not in self.dom[other]
                    for other in strict_doms):
                    idom[b] = d
                    break
        return idom



    def _build_dom_tree(self):
        basic_blocks = self.ic.bb_sequence
        dom_tree = {b: [] for b in basic_blocks}

        for bb in basic_blocks:
            if self.idom[bb] is not None:
                dom_tree[self.idom[bb]].append(bb)

        return dom_tree

    
    
    def _compute_dominance_frontier(self):
        basic_blocks = self.ic.bb_sequence
        df = {bb: set() for bb in basic_blocks}

        for bb in basic_blocks:
            if len(bb.predecessors) >= 2:
                for p in bb.predecessors:
                    runner = p
                    while runner is not None and runner != self.idom[bb]:
                        df[runner].add(bb)
                        runner = self.idom[runner]
        return df




    def _insert_phi(self):
        basic_blocks = self.ic.bb_sequence
        
        # 1. Identificar variáveis promovíveis (que possuem ALLOCA)
        self.promotable_vars = set()
        self.defsites = {}
        for bb in basic_blocks:
            for instr in bb.instructions:
                if instr.op == SSAOperator.ALLOCA:
                    v = instr.result
                    self.promotable_vars.add(v)
                    self.defsites.setdefault(v, set()).add(bb)
                elif instr.op == SSAOperator.STORE:
                    v = instr.result # O endereço onde estamos guardando
                    if v.is_temp: # Ajuste conforme sua flag
                        self.defsites.setdefault(v, set()).add(bb)

        # 2. Inserção iterada de PHIs usando a Fronteira de Dominância
        phi_map = {b: {} for b in basic_blocks}
        for v in self.promotable_vars:
            w = list(self.defsites.get(v, []))
            #added_phi = set()
            while w:
                n = w.pop()
                for y in self.df[n]:
                    if v not in phi_map[y]:
                        phi_map[y][v] = SSAPhi()
                        if y not in self.defsites.get(v, []):
                            w.append(y)
        
        return phi_map



    def rename(self):
        # Inicializa pilhas e contadores para cada variável alocada
        self.stack = {v: [] for v in self.promotable_vars}
        self.counters = {v: 0 for v in self.promotable_vars}
        
        entry = self.ic.bb_sequence[0]
        self._rename_block(entry)





    def _rename_block(self, bb: BasicBlock):
        # =========================
        # 1️⃣ Inserir PHIs no topo
        # =========================
        phi_instrs = []
        for v, phi_op in self.phi[bb].items(): 
            # Incrementa contador e empilha nova versão para a PHI
            self.counters[v] += 1
            new_version = SSATempVersion(v, self.counters[v])
            self.stack[v].append(new_version)

            # O mapa 'self.phi[bb][v]' guardará a instrução para o passo 3
            phi_instr = SSAInstr(SSAOperator.PHI, phi_op, SSAOperand.EMPTY, new_version)
            phi_instrs.append(phi_instr)
            self.phi[bb][v] = phi_instr

        index = 1 if bb.instructions and bb.instructions[0].op == SSAOperator.LABEL else 0
        bb.instructions[index:index] = phi_instrs

        # =========================
        # 2️⃣ Processar instruções
        # =========================
        new_instrs = []
        for instr in bb.instructions[:]:
            # Pula PHIs recém-criadas no passo 1
            if instr.op == SSAOperator.PHI:
                new_instrs.append(instr)
                continue

            
            if instr.op == SSAOperator.ALLOCA:
                bb.instructions.remove(instr)
                continue

            # -------- LOAD (t2 = load t0) --------
            if instr.op == SSAOperator.LOAD:
                addr = instr.arg1
                if addr in self.promotable_vars:
                    # Se houver algo na pilha, usamos a versão mais recente
                    if self.stack[addr]:
                        current_version = self.stack[addr][-1]
                        # Transforma LOAD em MOVE (t2 = t0_v1)
                        new_instrs.append(SSAInstr(SSAOperator.MOVE, current_version, SSAOperand.EMPTY, instr.result))
                        continue

            # -------- STORE (store t2, t0) --------
            elif instr.op == SSAOperator.STORE:
                addr = instr.result # Onde guardamos (o l-value)
                if addr in self.promotable_vars:
                    value = instr.arg1
                    
                    # Se o valor que estamos guardando for outra variável, pega a versão dela
                    if value in self.promotable_vars and self.stack[value]:
                        value = self.stack[value][-1]

                    # Cria nova versão para o destino
                    self.counters[addr] += 1
                    new_version = SSATempVersion(addr, self.counters[addr])
                    self.stack[addr].append(new_version)

                    # Transforma STORE em MOVE (t0_v2 = valor)
                    new_instrs.append(SSAInstr(SSAOperator.MOVE, value, SSAOperand.EMPTY, new_version))
                    continue

            # -------- OUTRAS INSTRUÇÕES (Cálculos, IFs, etc) --------
            # Renomeia arg1 e arg2 se forem variáveis de memória
            if instr.arg1 in self.promotable_vars and self.stack[instr.arg1]:
                instr.arg1 = self.stack[instr.arg1][-1]
            if instr.arg2 in self.promotable_vars and self.stack[instr.arg2]:
                instr.arg2 = self.stack[instr.arg2][-1]

            new_instrs.append(instr)

        bb.instructions = new_instrs

        # =====================================
        # 3️⃣ Preencher argumentos das PHIs nos sucessores
        # =====================================
        for succ in bb.successors:
            if succ in self.phi:
                for v, entry in self.phi[succ].items():
                    # entry pode ser a SSAInstr ou o objeto SSAPhi (caixa postal)
                    target_phi_op = entry.arg1 if isinstance(entry, SSAInstr) else entry
                    
                    if v in self.stack and self.stack[v]:
                        version = self.stack[v][-1]
                        target_phi_op.add_path(bb, version)

        # =====================================
        # 4️⃣ DFS na Árvore de Dominância
        # =====================================
        for child in self.dom_tree[bb]:
            self._rename_block(child)

        # =====================================
        # 5️⃣ Backtrack (Pop)
        # =====================================
        # Importante: Desempilhar apenas o que foi empilhado NESTE bloco
        for instr in bb.instructions:
            if isinstance(instr.result, SSATempVersion):
                origin_var = instr.result.origin
                if origin_var in self.promotable_vars:
                    self.stack[origin_var].pop()
