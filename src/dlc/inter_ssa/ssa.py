from dlc.inter.basic_block import BasicBlock
from dlc.inter_ssa.ssa_ic import SSA_IC
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.inter_ssa.ssa_operand import SSAOperand, SSAPhi, SSATempVersion


class SSA:
    def __init__(self, ssa_ic: SSA_IC):
        self.ic = ssa_ic
        self._mem2reg(self.ic)
        self.dom = self._compute_dominators()
        self.idom = self._compute_idom()  # Dominador Imediato
        self.dom_tree = self._build_dom_tree()
        self.df = self._compute_dominance_frontier()
        self.phi = self._insert_phi()
        self._rename()
        self._remove_trivial_phis()

    def __str__(self):
        return str(self.ic)
    
    def _mem2reg(self, ic: SSA_IC): 
        for bb in self.ic.bb_sequence:
            new_instrs = []
            for instr in bb.instructions:
                if instr.op == SSAOperator.ALLOCA:
                    continue                
                elif instr.op in (SSAOperator.STORE, SSAOperator.LOAD):
                    instr.op = SSAOperator.MOVE 
                
                new_instrs.append(instr)
            bb.instructions = new_instrs



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




    # def _insert_phi(self):
    #     basic_blocks = self.ic.bb_sequence
        
    #     # 1. Identificar variáveis promovíveis (que possuem ALLOCA)
    #     self.promotable_vars = set()
    #     self.defsites = {}
        
    #     for bb in basic_blocks:
    #         for instr in bb.instructions:
    #             if instr.op == SSAOperator.STORE:
    #                 v = instr.result # O endereço onde estamos guardando
    #                 self.promotable_vars.add(v)
    #                 self.defsites.setdefault(v, set()).add(bb)

    #     # 2. Inserção iterada de PHIs usando a Fronteira de Dominância
    #     phi_map = {b: {} for b in basic_blocks}
    #     for v in self.promotable_vars:
    #         w = list(self.defsites.get(v, []))
    #         #added_phi = set()
    #         while w:
    #             n = w.pop()
    #             for y in self.df[n]:
    #                 if v not in phi_map[y]:
    #                     phi_map[y][v] = SSAPhi()
    #                     if y not in self.defsites.get(v, []):
    #                         w.append(y)
        
    #     return phi_map


    def _insert_phi(self):
        self.defsites = {}
        
        # 1. Mapeia ONDE cada temporário é definido (não importa a instrução)
        for bb in self.ic.bb_sequence:
            for instr in bb.instructions:
                if instr.result and instr.result.is_temp:
                    v = instr.result
                    self.defsites.setdefault(v, set()).add(bb)

        # 2. Define quem ganha PHI:
        # Qualquer variável com mais de um ponto de definição (defsite)
        phi_vars = [v for v, sites in self.defsites.items() if len(sites) > 1]

        # 3. Inserção iterada (Sua lógica de DF permanece a mesma)
        phi_map = {b: {} for b in self.ic.bb_sequence}
        for v in phi_vars:
            w = list(self.defsites[v])
            while w:
                n = w.pop()
                for y in self.df[n]:
                    if v not in phi_map[y]:
                        phi_map[y][v] = SSAInstr(SSAOperator.PHI, SSAPhi(), SSAOperand.EMPTY, SSAOperand.EMPTY)
                        # Se y não era um local de definição original, adicione ao worklist
                        if y not in self.defsites[v]:
                            w.append(y)
        return phi_map




    def _rename(self):
        # Inicializa pilhas e contadores para cada variável
        self.stack = {}
        self.counters = {}
        
        for bb in self.ic.bb_sequence:
            for instr in bb.instructions:
                # Coletamos todos os temporários possíveis (definições e usos)
                temps = [instr.result, instr.arg1, instr.arg2]
                for t in temps:
                    if t and t.is_temp and t not in self.stack:
                        self.stack[t] = []
                        self.counters[t] = 0
                        
        entry = self.ic.bb_sequence[0]
        self._rename_block(entry)





    def _rename_block(self, bb: BasicBlock):
        # =========================
        # 1️⃣ Inserir PHIs no topo
        # =========================
        phi_instrs = []
        # bb pode não estar no mapa phi se não tiver fronteira de dominância
        phis_in_this_bb = self.phi.get(bb, {})
        for v, instr in phis_in_this_bb.items(): 
            # Incrementa contador e empilha nova versão para a PHI
            self.counters[v] += 1
            new_version = SSATempVersion(v, self.counters[v])
            self.stack[v].append(new_version)
            instr.result = new_version
            phi_instrs.append(instr)
        # Insere as PHIs logo após o Label
        bb.instructions[1:1] = phi_instrs

        # =========================
        # 2️⃣ Processar instruções (Versionamento Universal)
        # =========================
        new_instrs = []
        for instr in bb.instructions:
            if instr.arg1.is_temp:
                temp = instr.arg1
                if self.stack[temp]:
                    instr.arg1 = self.stack[temp][-1]

            if instr.arg2.is_temp:
                temp = instr.arg2
                if self.stack[temp]:
                    instr.arg2 = self.stack[temp][-1]

            # Versiona Resultado (Definição)
            if instr.result.is_temp:
                temp = instr.result
                self.counters[temp] += 1
                new_version = SSATempVersion(temp, self.counters[temp])
                self.stack[temp].append(new_version)
                instr.result = new_version

            new_instrs.append(instr)

        bb.instructions = new_instrs


        # =====================================
        # 3️⃣ Preencher argumentos das PHIs nos sucessores
        # =====================================
        for succ in bb.successors:
            for v, instr in self.phi[succ].items():
                if v in self.stack and self.stack[v]:
                    version = self.stack[v][-1]
                    instr.arg1.add_path(bb, version)
                    


        # =====================================
        # 4️⃣ DFS na Árvore de Dominância
        # =====================================
        for child in self.dom_tree.get(bb, []):
            self._rename_block(child)

        # =====================================
        # 5️⃣ Backtrack (Pop)
        # =====================================
        # Removemos da pilha apenas o que este bloco definiu
        for instr in bb.instructions:
            if instr.result and instr.result.is_temp_version:
                origin_var = instr.result.origin
                if origin_var in self.stack:
                    self.stack[origin_var].pop()




    def _remove_trivial_phis(self):
        for bb in self.ic.bb_sequence:
            new_instrs = []
            for instr in bb.instructions:
                if instr.op == SSAOperator.PHI:
                    if len(instr.arg1.paths) < 2:
                        continue
                new_instrs.append(instr)
            bb.instructions = new_instrs
    

    #procurar forma mais simples de remover os triviais
    # def _remove_trivial_phis(self):
    #     changed = True

    #     while changed:
    #         changed = False

    #         for bb in self.ic.bb_sequence:
    #             new_instrs = []

    #             for instr in bb.instructions:
    #                 if instr.op == SSAOperator.PHI:
    #                     phi = instr.arg1
    #                     values = list(phi.paths.values())

    #                     # Remove entradas None
    #                     values = [v for v in values if v is not None]

    #                     # Caso 1: zero ou um argumento
    #                     if len(values) <= 1:
    #                         changed = True
    #                         continue

    #                     # Caso 2: todos iguais
    #                     first = values[0]
    #                     if all(v == first for v in values):
    #                         changed = True
    #                         continue

    #                 new_instrs.append(instr)

    #             bb.instructions = new_instrs