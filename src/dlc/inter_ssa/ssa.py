from dlc.inter.basic_block import BasicBlock
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAOperand, SSAPhi, SSATempVersion


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
                # if instr.op == SSAOperator.ALLOCA:
                #     v = instr.result
                #     self.promotable_vars.add(v)
                #     self.defsites.setdefault(v, set()).add(bb)
                if instr.op == SSAOperator.STORE:
                    v = instr.result # O endereço onde estamos guardando
                    self.promotable_vars.add(v)
                    #if v.is_temp: # Ajuste conforme sua flag
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
        # self.stack = {v: [] for v in self.promotable_vars}
        # self.counters = {v: 0 for v in self.promotable_vars}
        self.stack = {}
        self.counters = {}
        for bb in self.ic.bb_sequence:
            for instr in bb:
                if instr.result.is_temp:
                    self.stack[instr.result] = []
                    self.counters[instr.result] = 0
        
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
        for instr in bb.instructions:

            new_instr = instr
            match instr.op:
                case SSAOperator.ALLOCA: #remove ALLOCAs
                    continue
                case SSAOperator.LOAD | SSAOperator.STORE: #transforma LOADs/STOREs em MOVEs
                    new_instr = SSAInstr(SSAOperator.MOVE, instr.arg1, SSAOperand.EMPTY, instr.result)

            # Troca os temporários por temporários versionados (importante fazer result por último)
            if new_instr.arg1.is_temp:
                temp = new_instr.arg1
                if self.stack[temp]:
                    current_version = self.stack[temp][-1]
                    new_instr.arg1 = current_version

            if new_instr.arg2.is_temp:
                temp = new_instr.arg2
                if self.stack[temp]:
                    current_version = self.stack[temp][-1]
                    new_instr.arg2 = current_version

            if new_instr.result.is_temp:
                temp = new_instr.result
                self.counters[temp] += 1
                new_version = SSATempVersion(temp, self.counters[temp])
                self.stack[temp].append(new_version)
                new_instr.result = new_version


            new_instrs.append(new_instr)

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
            if instr.result.is_temp_version:
                self.stack[instr.result.origin].pop()
